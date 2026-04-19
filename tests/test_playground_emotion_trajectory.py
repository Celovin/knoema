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


def test_subtask21_build_app_exposes_emotion_trajectory_plot() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    emotion_plot = next(
        component
        for component in components
        if type(component).__name__ == "Plot"
        and getattr(component, "elem_id", None) == "emotion-trajectory-plot"
    )

    assert emotion_plot.label == playground_app.LABELS["ko"]["memory_emotion"]


def test_subtask21_run_populates_pad_trajectory_per_agent() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Emotion Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )

    agent_id = sorted(result.memory_snapshot)[0]
    series = result.memory_snapshot[agent_id]["emotion"]

    assert len(series) == result.tick_count
    assert set(series[0]) >= {"tick", "timestamp", "valence", "arousal", "dominance"}
    assert all(-1.0 <= float(entry["valence"]) <= 1.0 for entry in series)
    assert all(0.0 <= float(entry["arousal"]) <= 1.0 for entry in series)
    assert all(0.0 <= float(entry["dominance"]) <= 1.0 for entry in series)


def test_subtask21_emotion_figure_supports_multi_agent_grid_and_axis_ranges() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Emotion Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )

    agent_ids = sorted(result.memory_snapshot)
    single_figure = playground_app._emotion_trajectory_figure(
        result.memory_snapshot,
        [agent_ids[0]],
        language="en",
    )
    grid_figure = playground_app._emotion_trajectory_figure(
        result.memory_snapshot,
        agent_ids,
        language="en",
    )

    assert len(single_figure.data) == 3
    assert len(grid_figure.data) == 6
    assert tuple(single_figure.layout.yaxis.range) == (-1, 1)
    assert tuple(single_figure.layout.yaxis2.range) == (0, 1)
    assert grid_figure.layout.height >= 240
