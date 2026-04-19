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


def test_subtask20_build_app_exposes_conversation_threads_tab() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    threads_tab = next(
        component
        for component in components
        if type(component).__name__ == "Tab"
        and getattr(component, "elem_id", None) == "conversation-threads-tab"
    )
    threads_panel = next(
        component
        for component in components
        if type(component).__name__ == "Markdown"
        and getattr(component, "elem_id", None) == "conversation-threads-panel"
    )

    assert threads_tab.label == playground_app.LABELS["ko"]["threads_tab"]
    assert threads_panel.value == playground_app.LABELS["ko"]["threads_empty"]


def test_subtask20_conversation_threads_render_colored_cards_for_dorm_run() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Thread Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=8,
    )

    agent_ids = sorted(result.memory_snapshot)
    color_map = playground_app._agent_color_map(agent_ids)
    markdown = playground_app._conversation_threads_markdown(
        result.jsonl,
        result.memory_snapshot,
        color_map,
        language="en",
    )

    assert "Thread 1" in markdown
    assert "border-left:2px solid" in markdown
    assert any(color in markdown for color in color_map.values())


def test_subtask20_conversation_threads_empty_state_is_localized() -> None:
    assert (
        playground_app._conversation_threads_markdown("", {}, {}, language="en")
        == playground_app.LABELS["en"]["threads_empty"]
    )
