from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_simulation = importlib.import_module("playground.simulation")


def test_subtask14_scenario_catalog_expands_to_thirty_entries_with_descriptions() -> None:
    choices = playground_simulation.scenario_choices()

    assert len(choices) == 30
    assert len(set(choices)) == 30

    for scenario_name in choices:
        config = playground_simulation.load_run_config(playground_simulation.scenario_path(scenario_name))
        assert config.description_ko
        assert config.description_en


def test_subtask14_all_thirty_scenarios_smoke_run_in_replay_mode() -> None:
    for scenario_name in playground_simulation.scenario_choices():
        result = playground_simulation.run_playground_scenario(
            scenario_name=scenario_name,
            provider="Replay only",
            api_key="",
            model="",
            primary_name="Smoke Agent",
            primary_age=24,
            openness=0.6,
            conscientiousness=0.6,
            extraversion=0.5,
            agreeableness=0.6,
            neuroticism=0.3,
            ticks=1,
        )

        assert result.log_count >= result.agent_count
        assert result.tick_count == 1
        assert result.timeline_markdown
        assert Path(result.download_path).exists()
