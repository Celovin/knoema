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


def test_subtask10_build_app_exposes_memory_inspector_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    memory_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "memory-inspector-panel"
    )
    agent_dropdown = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "memory-inspector-agent"
    )
    memory_markdown = next(
        component
        for component in components
        if type(component).__name__ == "Markdown"
        and getattr(component, "elem_id", None) == "memory-inspector-markdown"
    )
    emotion_plot = next(
        component
        for component in components
        if type(component).__name__ == "Plot"
        and getattr(component, "elem_id", None) == "emotion-trajectory-plot"
    )

    assert memory_panel.label == playground_app.LABELS["ko"]["memory_inspector"]
    assert agent_dropdown.interactive is False
    assert agent_dropdown.multiselect is True
    assert memory_markdown.value == playground_app.LABELS["ko"]["memory_empty"]
    assert emotion_plot.label == playground_app.LABELS["ko"]["memory_emotion"]


def test_subtask10_run_playground_scenario_returns_memory_snapshot() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Memory Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=2,
    )

    assert result.memory_snapshot
    agent_id = sorted(result.memory_snapshot)[0]
    snapshot = result.memory_snapshot[agent_id]
    assert snapshot["short_term"]
    assert len(snapshot["short_term"]) <= 10
    assert snapshot["long_term"]
    assert len(snapshot["long_term"]) <= 5
    assert "score" in snapshot["long_term"][0]
    assert snapshot["monologue"]
    assert snapshot["emotion"]
    assert len(snapshot["emotion"]) == result.tick_count


def test_subtask10_memory_inspector_markdown_renders_sections() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Memory Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=1,
    )

    agent_id = sorted(result.memory_snapshot)[0]
    markdown = playground_app._memory_inspector_markdown(
        result.memory_snapshot,
        agent_id,
        language="en",
    )

    assert agent_id in markdown
    assert "Short-term memory" in markdown
    assert "Retrieved long-term memory" in markdown
    assert "Inner monologue" in markdown
    assert (
        playground_app._memory_inspector_markdown({}, None, language="en")
        == playground_app.LABELS["en"]["memory_empty"]
    )


def test_subtask64_memory_inspector_accepts_language_display_choice() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Memory Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=1,
    )

    agent_ids = sorted(result.memory_snapshot)
    markdown, figure = playground_app._memory_inspector_views(
        result.memory_snapshot,
        agent_ids,
        language=playground_app.KOREAN_CHOICE,
    )

    assert playground_app.LABELS["ko"]["memory_short_term"] in markdown
    assert figure.layout.title.text == playground_app.LABELS["ko"]["memory_emotion"]
