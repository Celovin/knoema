from __future__ import annotations

import importlib
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


def test_playground_htn_controls_and_plan_panel_are_exposed() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    htn_checkbox = next(
        component
        for component in components
        if type(component).__name__ == "Checkbox"
        and getattr(component, "elem_id", None) == "htn-enabled-checkbox"
    )
    planning_depth = next(
        component
        for component in components
        if type(component).__name__ == "Slider"
        and getattr(component, "elem_id", None) == "planning-depth-slider"
    )
    current_plan_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "current-plan-panel"
    )

    assert htn_checkbox.label == playground_app.LABELS["ko"]["htn_enabled"]
    assert planning_depth.minimum == 2
    assert planning_depth.maximum == 4
    assert current_plan_panel.label == playground_app.LABELS["ko"]["current_plan_panel"]


def test_run_playground_scenario_returns_plan_markdown_when_htn_enabled() -> None:
    result = playground_simulation.run_playground_scenario(
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
        primary_planning_enabled=True,
        planning_depth=3,
        ticks=2,
    )

    assert "Current plan" in result.plan_markdown
    assert "Goal achievement rate" in result.plan_markdown
    assert "prepare breakfast" in result.plan_markdown


def test_run_playground_scenario_returns_disabled_copy_when_htn_off() -> None:
    result = playground_simulation.run_playground_scenario(
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
        primary_planning_enabled=False,
        planning_depth=3,
        ticks=1,
    )

    assert result.plan_markdown == "Hierarchical planning is disabled for this run."


def test_playground_run_round_trips_htn_controls_through_run() -> None:
    trait_values = [
        playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]
        for field_name in playground_simulation.PERSONA_TRAIT_FIELDS
    ]

    (
        timeline,
        _,
        monologue_markdown,
        plan_markdown,
        jsonl,
        download_path,
        summary,
        action_chart,
        tick_scrubber,
        tick_focus,
    ) = playground_app._run(
        "Dorm: two agents",
        "university_dorm_evening",
        "",
        "Replay only",
        "",
        "",
        "Roundtrip Mina",
        24,
        *trait_values,
        True,
        3,
        2,
        2,
        "English",
    )

    assert "Tick" in timeline
    assert "t0" in monologue_markdown
    assert "Current plan" in plan_markdown
    assert jsonl
    assert download_path
    assert "Mode: Replay only" in summary
    assert action_chart.data
    assert tick_scrubber["maximum"] == 1
    assert "All ticks summary" in tick_focus
