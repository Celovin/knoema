"""OpenAI text-to-speech helpers with deterministic offline fallback."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import wave
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Final

OPENAI_TTS_VOICES: Final[tuple[str, ...]] = (
    "alloy",
    "echo",
    "fable",
    "onyx",
    "nova",
    "shimmer",
)
OPENAI_TTS_PROVIDERS: Final[tuple[str, ...]] = ("openai", "openai-hd", "offline")
DEFAULT_TTS_CACHE_DIR: Final[Path] = Path(tempfile.gettempdir()) / "knoema_tts_cache"
SILENT_WAV_SECONDS: Final[float] = 0.25
SILENT_WAV_SAMPLE_RATE: Final[int] = 16_000


@dataclass(frozen=True)
class VoiceProfile:
    """Serializable TTS profile for one simulated agent."""

    agent_id: str
    voice_id: str
    speed: float = 1.0
    provider: str = "openai"

    def __post_init__(self) -> None:
        agent_id = self.agent_id.strip()
        if not agent_id:
            raise ValueError("agent_id must be non-empty")
        voice_id = self.voice_id.strip()
        if voice_id not in OPENAI_TTS_VOICES:
            allowed = ", ".join(OPENAI_TTS_VOICES)
            raise ValueError(f"voice_id must be one of: {allowed}")
        provider = self.provider.strip()
        if provider not in OPENAI_TTS_PROVIDERS:
            allowed = ", ".join(OPENAI_TTS_PROVIDERS)
            raise ValueError(f"provider must be one of: {allowed}")
        if not 0.25 <= float(self.speed) <= 4.0:
            raise ValueError("speed must be between 0.25 and 4.0")

        object.__setattr__(self, "agent_id", agent_id)
        object.__setattr__(self, "voice_id", voice_id)
        object.__setattr__(self, "speed", float(self.speed))
        object.__setattr__(self, "provider", provider)

    def to_dict(self) -> dict[str, str | float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VoiceProfile:
        return cls(
            agent_id=str(payload["agent_id"]),
            voice_id=str(payload["voice_id"]),
            speed=float(payload.get("speed", 1.0)),
            provider=str(payload.get("provider", "openai")),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


def synthesize(
    text: str,
    profile: VoiceProfile,
    *,
    cache_dir: str | Path | None = None,
    client: Any | None = None,
) -> bytes:
    """Synthesize ``text`` as WAV bytes, caching by SHA256(text + profile).

    The function never requires network access when ``OPENAI_API_KEY`` is unset.
    In that mode it returns a short deterministic silent WAV and stores it in
    the same on-disk cache path used by live OpenAI calls.
    """

    normalized_text = str(text).strip()
    target_dir = _resolve_cache_dir(cache_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    cache_path = target_dir / f"{_cache_key(normalized_text, profile)}.wav"
    if cache_path.exists():
        return cache_path.read_bytes()

    if not normalized_text or profile.provider == "offline" or not os.environ.get("OPENAI_API_KEY"):
        audio = _silent_wav_bytes()
    else:
        try:
            audio = _openai_speech_bytes(normalized_text, profile, client=client)
        except Exception:
            audio = _silent_wav_bytes()

    _atomic_write_bytes(cache_path, audio)
    return audio


def _resolve_cache_dir(cache_dir: str | Path | None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir)
    configured = os.environ.get("KNOEMA_TTS_CACHE_DIR", "").strip()
    if configured:
        return Path(configured)
    return DEFAULT_TTS_CACHE_DIR


def _cache_key(text: str, profile: VoiceProfile) -> str:
    payload = f"{text}\0{profile.to_json()}".encode()
    return hashlib.sha256(payload).hexdigest()


def _provider_model(provider: str) -> str:
    return "tts-1-hd" if provider == "openai-hd" else "tts-1"


def _openai_speech_bytes(text: str, profile: VoiceProfile, *, client: Any | None = None) -> bytes:
    if client is None:
        from openai import OpenAI

        client = OpenAI()

    response = client.audio.speech.create(
        model=_provider_model(profile.provider),
        voice=profile.voice_id,
        input=text,
        response_format="wav",
        speed=profile.speed,
    )
    return _binary_response_to_bytes(response)


def _binary_response_to_bytes(response: Any) -> bytes:
    if isinstance(response, bytes):
        return response
    if isinstance(response, bytearray):
        return bytes(response)
    read = getattr(response, "read", None)
    if callable(read):
        return bytes(read())
    content = getattr(response, "content", None)
    if content is not None:
        return bytes(content)
    nested_response = getattr(response, "response", None)
    nested_content = getattr(nested_response, "content", None)
    if nested_content is not None:
        return bytes(nested_content)
    raise TypeError("OpenAI speech response did not expose binary content")


def _silent_wav_bytes() -> bytes:
    sample_count = int(SILENT_WAV_SAMPLE_RATE * SILENT_WAV_SECONDS)
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SILENT_WAV_SAMPLE_RATE)
        wav_file.writeframes(b"\x00\x00" * sample_count)
    return buffer.getvalue()


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(payload)
    temporary_path.replace(path)


__all__ = ["OPENAI_TTS_VOICES", "VoiceProfile", "synthesize"]
