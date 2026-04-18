"""Phase 18 tests for demo video scripts."""

from __future__ import annotations

from pathlib import Path

VIDEO_ROOT = Path("docs/videos")


def test_phase18_video_script_files_exist() -> None:
    expected = [
        "script_30sec.md",
        "script_3min.md",
        "script_10min.md",
        "shotlist.md",
    ]

    missing = [path for path in expected if not (VIDEO_ROOT / path).exists()]

    assert missing == []


def test_phase18_scripts_include_timing_and_capture_guidance() -> None:
    for filename in ["script_30sec.md", "script_3min.md", "script_10min.md"]:
        script = (VIDEO_ROOT / filename).read_text(encoding="utf-8")
        assert "Time" in script
        assert "Narration" in script
        assert "Capture Notes" in script


def test_phase18_shotlist_covers_required_surfaces() -> None:
    shotlist = (VIDEO_ROOT / "shotlist.md").read_text(encoding="utf-8")
    required = [
        "Playground timeline",
        "Playground relationship graph",
        "JSONL log preview",
        "CLI terminal run",
        "Dashboard playback",
        "Godot adapter README",
        "Unity adapter README",
        "Competitor matrix",
    ]

    missing = [item for item in required if item not in shotlist]

    assert missing == []
