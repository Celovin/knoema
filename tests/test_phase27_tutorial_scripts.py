from __future__ import annotations

from pathlib import Path

SCRIPTS = [
    "01_getting_started_10min.md",
    "02_build_your_first_npc_15min.md",
    "03_research_experiment_20min.md",
]


def test_phase27_tutorial_scripts_exist() -> None:
    missing = [path for path in SCRIPTS if not Path("docs/videos/tutorials", path).exists()]

    assert missing == []


def test_phase27_scripts_include_recording_and_description_blocks() -> None:
    for script in SCRIPTS:
        content = Path("docs/videos/tutorials", script).read_text(encoding="utf-8")

        assert "## Recording Setup" in content
        assert "## Script" in content
        assert "## YouTube Description" in content
        assert "https://github.com/Celovin/knoema" in content


def test_phase27_research_script_keeps_safety_boundary() -> None:
    content = Path("docs/videos/tutorials/03_research_experiment_20min.md").read_text(
        encoding="utf-8"
    )

    assert "실제 개인이나 실제 사건을 입력하지 않습니다" in content
    assert "사람을 점수화하거나 미래 사건을 단정" in content
