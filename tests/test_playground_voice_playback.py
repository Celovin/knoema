from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _speak_row(content: str = "Hello") -> str:
    return json.dumps(
        {
            "tick": 0,
            "timestamp": "2026-04-22T00:00:00",
            "agent_id": "alice",
            "action": {"action_type": "speak", "target": "bob", "content": content},
        }
    )


def test_timeline_voice_disabled_does_not_synthesize(monkeypatch) -> None:
    def fail_synthesis(*_args: Any, **_kwargs: Any) -> bytes:
        raise AssertionError("voice synthesis should not run when playback is disabled")

    monkeypatch.setattr(playground_app, "synthesize_voice", fail_synthesis)

    timeline = playground_app._timeline_markdown_with_agent_colors(
        _speak_row(),
        "",
        {"alice": "#123456"},
        language="en",
        voice_enabled=False,
        voice_agent_1="alloy",
    )

    assert "<audio" not in timeline


def test_timeline_voice_enabled_embeds_audio(monkeypatch) -> None:
    calls: list[str] = []

    def fake_synthesis(text: str, profile: Any) -> bytes:
        calls.append(text)
        assert profile.agent_id == "alice"
        assert profile.voice_id == "alloy"
        return b"RIFFfake-wav"

    monkeypatch.setattr(playground_app, "synthesize_voice", fake_synthesis)

    timeline = playground_app._timeline_markdown_with_agent_colors(
        _speak_row("Cache me"),
        "",
        {"alice": "#123456"},
        language="en",
        voice_enabled=True,
        voice_agent_1="alloy",
    )

    assert calls == ["Cache me"]
    assert "<audio controls" in timeline
    assert "data:audio/wav;base64," in timeline
