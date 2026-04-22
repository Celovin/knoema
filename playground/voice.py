"""Optional local voice helpers for playground player mode."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

STT_ENGINE_IDS = ("off", "whisper_cpp")
TTS_ENGINE_IDS = ("off", "pyttsx3", "edge_tts")


def stt_engine_choices(language: str = "en") -> list[tuple[str, str]]:
    if language == "ko":
        return [("끄기", "off"), ("whisper.cpp", "whisper_cpp")]
    return [("Off", "off"), ("whisper.cpp", "whisper_cpp")]


def tts_engine_choices(language: str = "en") -> list[tuple[str, str]]:
    if language == "ko":
        return [("끄기", "off"), ("pyttsx3", "pyttsx3"), ("Edge TTS", "edge_tts")]
    return [("Off", "off"), ("pyttsx3", "pyttsx3"), ("Edge TTS", "edge_tts")]


def transcribe_player_audio(
    audio_path: str | None,
    *,
    engine: str,
    language: str = "en",
) -> tuple[str, str]:
    if engine == "off" or not audio_path:
        return "", ""
    if engine != "whisper_cpp":
        return "", _voice_status(language, "Unsupported STT engine.")
    executable = _whisper_cpp_executable()
    if executable is None:
        return "", _voice_status(language, "whisper.cpp is unavailable on this machine.")
    model_path = _whisper_cpp_model(language)
    if model_path is None:
        return "", _voice_status(language, "No whisper.cpp model was found.")

    output_dir = Path(tempfile.mkdtemp(prefix="luvoire_whisper_"))
    output_prefix = output_dir / "transcript"
    command = [
        executable,
        "-m",
        str(model_path),
        "-f",
        str(audio_path),
        "-otxt",
        "-of",
        str(output_prefix),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    transcript_path = output_prefix.with_suffix(".txt")
    if completed.returncode != 0 or not transcript_path.exists():
        return "", _voice_status(language, "whisper.cpp transcription failed.")
    transcript = transcript_path.read_text(encoding="utf-8").strip()
    if not transcript:
        return "", _voice_status(language, "No speech was detected.")
    return transcript, _voice_status(language, "Voice input transcribed.")


def synthesize_text_to_audio(
    text: str,
    *,
    engine: str,
    language: str = "en",
) -> tuple[str | None, str]:
    if engine == "off" or not text.strip():
        return None, ""
    if engine == "pyttsx3":
        return _synthesize_with_pyttsx3(text, language=language)
    if engine == "edge_tts":
        return _synthesize_with_edge_tts(text, language=language)
    return None, _voice_status(language, "Unsupported TTS engine.")


def _synthesize_with_pyttsx3(text: str, *, language: str) -> tuple[str | None, str]:
    try:
        import pyttsx3  # type: ignore[import-not-found]
    except ImportError:
        return None, _voice_status(language, "pyttsx3 is unavailable on this machine.")

    fd, output_name = tempfile.mkstemp(prefix="luvoire_tts_", suffix=".wav")
    Path(output_name).unlink(missing_ok=True)
    os.close(fd)
    output_path = Path(output_name)
    engine = pyttsx3.init()
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    if not output_path.exists() or output_path.stat().st_size == 0:
        return None, _voice_status(language, "pyttsx3 synthesis failed.")
    return str(output_path), _voice_status(language, "Audio response is ready.")


def _synthesize_with_edge_tts(text: str, *, language: str) -> tuple[str | None, str]:
    try:
        import edge_tts  # type: ignore[import-not-found]
    except ImportError:
        return None, _voice_status(language, "Edge TTS is unavailable on this machine.")

    fd, output_name = tempfile.mkstemp(prefix="luvoire_edge_", suffix=".mp3")
    Path(output_name).unlink(missing_ok=True)
    os.close(fd)
    output_path = Path(output_name)
    voice_name = "ko-KR-SunHiNeural" if language == "ko" else "en-US-JennyNeural"
    asyncio.run(edge_tts.Communicate(text=text, voice=voice_name).save(str(output_path)))
    if not output_path.exists() or output_path.stat().st_size == 0:
        return None, _voice_status(language, "Edge TTS synthesis failed.")
    return str(output_path), _voice_status(language, "Audio response is ready.")


def _whisper_cpp_executable() -> str | None:
    for candidate in ("whisper-cli", "main"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _whisper_cpp_model(language: str) -> Path | None:
    configured_path = _configured_whisper_model_path(language)
    if configured_path is not None and configured_path.exists():
        return configured_path
    candidates = [
        Path.cwd() / "models" / "ggml-small.bin",
        Path.cwd() / "models" / "whisper.cpp" / "ggml-small.bin",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _configured_whisper_model_path(language: str) -> Path | None:
    env_key = "WHISPER_CPP_MODEL_KO" if language == "ko" else "WHISPER_CPP_MODEL"
    value = os.environ.get(env_key, "").strip() or os.environ.get("WHISPER_CPP_MODEL", "").strip()
    if not value:
        return None
    return Path(value)


def _voice_status(language: str, message: str) -> str:
    if language != "ko":
        return message
    translations = {
        "Unsupported STT engine.": "지원하지 않는 STT 엔진입니다.",
        "whisper.cpp is unavailable on this machine.": "이 환경에서는 whisper.cpp를 사용할 수 없습니다.",
        "No whisper.cpp model was found.": "사용 가능한 whisper.cpp 모델을 찾지 못했습니다.",
        "whisper.cpp transcription failed.": "whisper.cpp 전사가 실패했습니다.",
        "No speech was detected.": "감지된 음성이 없습니다.",
        "Voice input transcribed.": "음성 입력을 텍스트로 변환했습니다.",
        "Unsupported TTS engine.": "지원하지 않는 TTS 엔진입니다.",
        "pyttsx3 is unavailable on this machine.": "이 환경에서는 pyttsx3를 사용할 수 없습니다.",
        "pyttsx3 synthesis failed.": "pyttsx3 음성 합성이 실패했습니다.",
        "Edge TTS is unavailable on this machine.": "이 환경에서는 Edge TTS를 사용할 수 없습니다.",
        "Edge TTS synthesis failed.": "Edge TTS 음성 합성이 실패했습니다.",
        "Audio response is ready.": "응답 오디오를 준비했습니다.",
    }
    return translations.get(message, message)


__all__ = [
    "STT_ENGINE_IDS",
    "TTS_ENGINE_IDS",
    "stt_engine_choices",
    "synthesize_text_to_audio",
    "transcribe_player_audio",
    "tts_engine_choices",
]
