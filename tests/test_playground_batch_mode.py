from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask25_build_app_exposes_batch_mode_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    batch_mode = next(
        component
        for component in components
        if type(component).__name__ == "Checkbox"
        and getattr(component, "elem_id", None) == "batch-mode-checkbox"
    )
    batch_runs = next(
        component
        for component in components
        if type(component).__name__ == "Slider"
        and getattr(component, "elem_id", None) == "batch-runs-slider"
    )
    master_seed = next(
        component
        for component in components
        if type(component).__name__ == "Number"
        and getattr(component, "elem_id", None) == "master-seed-number"
    )

    assert batch_mode.label == playground_app.LABELS["ko"]["batch_mode"]
    assert batch_runs.maximum == 100
    assert batch_runs.interactive is False
    assert master_seed.value == 20260419


def test_subtask25_batch_run_returns_aggregate_stats_and_reproducibility() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Batch Mina",
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

    assert result.batch_result is not None
    assert result.batch_result.batch_size == 10
    assert result.batch_result.seeds == tuple(20260419 + index for index in range(10))
    assert result.batch_result.reproducibility_coefficient >= 0.95
    assert result.log_count == 80
    assert "Batch runs: 10" in result.timeline_markdown

    rows = [json.loads(line) for line in result.jsonl.splitlines()]
    assert rows[0]["record_type"] == "batch_summary"
    assert rows[0]["reproducibility_coefficient"] >= 0.95


def test_subtask25_run_round_trips_batch_controls_into_summary() -> None:
    trait_values = [
        playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
    ]

    (
        timeline,
        thread_view,
        _,
        monologue_markdown,
        plan_markdown,
        jsonl,
        download_path,
        summary,
        action_chart,
        tick_scrubber,
        tick_focus,
        memory_snapshot,
        memory_agent,
        memory_markdown,
    ) = playground_app._run(
        "Dorm: two agents",
        "university_dorm_evening",
        "",
        "Replay only",
        "",
        "",
        "Batch Mina",
        24,
        *trait_values,
        False,
        3,
        4,
        2,
        True,
        10,
        20260419,
        "English",
    )

    assert "Batch timeline" in timeline
    assert "Batch runs: 10" in summary
    assert "multiple seeds" in monologue_markdown
    assert "multiple seeds" in plan_markdown
    assert "single-run mode only" in thread_view
    assert jsonl
    assert download_path
    assert action_chart.data
    assert tick_scrubber["maximum"] == 3
    assert "All ticks summary" in tick_focus
    assert memory_snapshot == {}
    assert memory_agent["interactive"] is False
    assert "single simulation" in memory_markdown
