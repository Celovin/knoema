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


def test_subtask9_build_app_exposes_tick_scrubber_and_focus_below_graph() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    tick_scrubber = next(
        component
        for component in components
        if type(component).__name__ == "Slider"
        and getattr(component, "elem_id", None) == "tick-scrubber"
    )
    tick_focus = next(
        component
        for component in components
        if type(component).__name__ == "Markdown"
        and getattr(component, "elem_id", None) == "tick-focus-panel"
    )
    graph_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "HTML"
        and getattr(child, "elem_id", None) == "relationship-graph"
    )
    scrubber_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Form"
        and any(
            type(grandchild).__name__ == "Slider"
            and getattr(grandchild, "elem_id", None) == "tick-scrubber"
            for grandchild in getattr(child, "children", []) or []
        )
    )
    focus_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Markdown"
        and getattr(child, "elem_id", None) == "tick-focus-panel"
    )
    timeline_index = next(
        index
        for index, child in enumerate(components)
        if type(child).__name__ == "Markdown"
        and getattr(child, "elem_id", None) == "timeline-panel"
    )

    assert tick_scrubber.minimum == -1
    assert tick_scrubber.maximum == 0
    assert tick_scrubber.value == -1
    assert tick_focus.value == playground_app.LABELS["ko"]["tick_focus_empty"]
    assert graph_index < scrubber_index < focus_index < timeline_index


def test_subtask9_tick_focus_markdown_filters_to_selected_tick() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Tick Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )

    all_ticks = playground_app._tick_focus_markdown(result.jsonl, -1, "en")
    tick_zero = playground_app._tick_focus_markdown(result.jsonl, 0, "en")

    assert "All ticks summary" in all_ticks
    assert "Events:" in all_ticks
    assert "### Tick 0" in tick_zero
    assert "- **" in tick_zero
