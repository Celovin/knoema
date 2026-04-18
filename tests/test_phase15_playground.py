from __future__ import annotations

import json
from pathlib import Path

from playground.simulation import run_playground_scenario, scenario_choices, scenario_path


def test_phase15_playground_distribution_files_exist() -> None:
    playground = Path("playground")

    assert (playground / "app.py").exists()
    assert (playground / "requirements.txt").exists()
    assert (playground / "README.md").exists()
    assert (playground / "assets" / "cover.png").stat().st_size > 1000
    assert (playground / "assets" / "examples.gif").stat().st_size > 0
    assert "gradio" in (playground / "requirements.txt").read_text(encoding="utf-8")
    assert "celovin/knoema-playground" in Path("README.md").read_text(encoding="utf-8")
    assert "deploy_playground_space.py" in (playground / "README.md").read_text(encoding="utf-8")
    assert Path("scripts/deploy_playground_space.py").exists()


def test_phase15_scenarios_exist() -> None:
    choices = scenario_choices()

    assert choices == ["Dorm: two agents", "Village: ten agents", "School corridor"]
    assert all(scenario_path(choice).exists() for choice in choices)


def test_phase15_replay_mode_runs_and_exports_jsonl() -> None:
    result = run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Test Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=2,
    )

    assert result.mode == "Replay only"
    assert result.agent_count == 2
    assert result.tick_count == 2
    assert result.log_count == 4
    assert "Timeline" in result.timeline_markdown
    assert "Test Mina" not in result.jsonl
    assert Path(result.download_path).exists()
    rows = [json.loads(line) for line in result.jsonl.splitlines()]
    assert rows[0]["tick"] == 0
    assert rows[0]["action"]["action_type"] in {"speak", "observe"}


def test_phase15_playground_clamps_tick_count() -> None:
    result = run_playground_scenario(
        scenario_name="School corridor",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Yuna",
        primary_age=16,
        openness=0.7,
        conscientiousness=0.7,
        extraversion=0.5,
        agreeableness=0.8,
        neuroticism=0.3,
        ticks=100,
    )

    assert result.tick_count == 24
    assert result.log_count == 72
