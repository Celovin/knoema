from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def test_subtask8_build_app_places_action_chart_between_summary_and_graph() -> None:
    app = playground_app.build_app()

    summary_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Form"
        and any(
            type(grandchild).__name__ == "Textbox"
            and getattr(grandchild, "label", None) == playground_app.LABELS["ko"]["summary"]
            for grandchild in getattr(child, "children", []) or []
        )
    )
    chart_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Plot"
        and getattr(child, "elem_id", None) == "action-breakdown-chart"
    )
    graph_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "HTML"
        and getattr(child, "elem_id", None) == "relationship-graph"
    )

    assert summary_index < chart_index < graph_index


def test_subtask8_action_chart_empty_state_is_localized() -> None:
    english = playground_app._action_chart_figure({}, language="en")
    korean = playground_app._action_chart_figure({}, language="ko")

    assert english.layout.title.text == "Action type breakdown"
    assert english.layout.annotations[0].text == "Not enough data yet"
    assert korean.layout.annotations[0].text == "데이터가 충분하지 않습니다."


def test_subtask8_run_returns_action_breakdown_and_agent_colors() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Chart Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )

    assert result.action_breakdown
    assert sum(sum(counts.values()) for counts in result.action_breakdown.values()) == result.log_count

    ordered_agents = sorted(result.action_breakdown)
    color_map = playground_app._agent_color_map(ordered_agents)
    figure = playground_app._action_chart_figure(result.action_breakdown, language="en")

    assert figure.data
    assert list(figure.data[0].x) == ordered_agents
    assert list(figure.data[0].marker.color) == [color_map[agent_id] for agent_id in ordered_agents]
