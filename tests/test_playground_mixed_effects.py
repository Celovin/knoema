from __future__ import annotations

import importlib
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")
research_statistics = importlib.import_module("knoema.research.statistics")


def test_subtask36_batch_jsonl_emits_seed_tick_rows() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Nested Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
        batch_mode=True,
        batch_runs=10,
        master_seed=20260419,
    )

    rows = playground_app._jsonl_rows(result.jsonl)
    seed_tick_rows = [
        row for row in rows if str(row.get("record_type", "")) == "seed_tick_stat"
    ]

    assert seed_tick_rows
    assert {int(row["seed"]) for row in seed_tick_rows} == set(range(20260419, 20260429))


def test_subtask36_nested_summary_returns_effect_and_posterior() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Nested Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
        batch_mode=True,
        batch_runs=10,
        master_seed=20260419,
    )

    summary = research_statistics.summarize_seed_tick_effect(
        playground_app._jsonl_rows(result.jsonl)
    )

    assert summary is not None
    assert summary.seed_count == 10
    assert summary.observation_count >= 20
    assert math.isfinite(summary.fixed_effect)
    assert math.isfinite(summary.posterior_mean)
    assert summary.backend.endswith("analytic posterior")


def test_subtask36_statistics_panel_mentions_mixed_effects_and_posterior() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Nested Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
        batch_mode=True,
        batch_runs=10,
        master_seed=20260419,
    )

    markdown = playground_app._statistical_analysis_markdown(result.jsonl, "English")

    assert "Mixed effects" in markdown
    assert "Bayesian posterior" in markdown
    assert "backend=" in markdown
