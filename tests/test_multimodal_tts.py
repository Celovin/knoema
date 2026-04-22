from __future__ import annotations

import wave
from io import BytesIO

from luvoire.multimodal.tts import OPENAI_TTS_VOICES, VoiceProfile, synthesize


class _FakeSpeech:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> bytes:
        self.calls.append(kwargs)
        return b"RIFFfake-openai-wav"


class _FakeAudio:
    def __init__(self) -> None:
        self.speech = _FakeSpeech()


class _FakeOpenAIClient:
    def __init__(self) -> None:
        self.audio = _FakeAudio()


def test_voice_profile_serialization_round_trip() -> None:
    profile = VoiceProfile(agent_id="mina", voice_id="nova", speed=1.1, provider="openai-hd")

    restored = VoiceProfile.from_dict(profile.to_dict())

    assert restored == profile
    assert "nova" in profile.to_json()
    assert set(OPENAI_TTS_VOICES) == {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}


def test_offline_fallback_returns_valid_cached_wav(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = VoiceProfile(agent_id="bjorn", voice_id="alloy")

    first = synthesize("hello from replay", profile, cache_dir=tmp_path)
    second = synthesize("hello from replay", profile, cache_dir=tmp_path)

    assert first == second
    assert len(list(tmp_path.glob("*.wav"))) == 1
    with wave.open(BytesIO(first), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 16_000
        assert wav_file.getnframes() > 0


def test_openai_synthesis_uses_cache(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    client = _FakeOpenAIClient()
    profile = VoiceProfile(agent_id="ari", voice_id="shimmer", speed=0.9)

    first = synthesize("new speak action", profile, cache_dir=tmp_path, client=client)
    second = synthesize("new speak action", profile, cache_dir=tmp_path, client=client)
    third = synthesize("different speak action", profile, cache_dir=tmp_path, client=client)

    assert first == second == b"RIFFfake-openai-wav"
    assert third == b"RIFFfake-openai-wav"
    assert len(client.audio.speech.calls) == 2
    assert client.audio.speech.calls[0]["model"] == "tts-1"
    assert client.audio.speech.calls[0]["voice"] == "shimmer"
