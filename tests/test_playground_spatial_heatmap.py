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


def test_subtask22_build_app_exposes_spatial_heatmap_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "spatial-heatmap-panel"
    )
    plot = next(
        component
        for component in components
        if type(component).__name__ == "Plot"
        and getattr(component, "elem_id", None) == "spatial-heatmap-treemap"
    )

    assert panel.label == playground_app.LABELS["ko"]["spatial_heatmap_panel"]
    assert plot.label == playground_app.LABELS["ko"]["spatial_heatmap"]


def test_subtask22_spatial_heatmap_renders_three_level_treemap_with_hover_fields() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Village: ten agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Heat Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )

    figure = playground_app._spatial_heatmap_figure(
        result.jsonl,
        result.memory_snapshot,
        language="en",
    )
    treemap = figure.data[0]

    assert treemap.type == "treemap"
    assert max(tree_id.count(" / ") + 1 for tree_id in treemap.ids) >= 3
    assert "Total tick count" in treemap.hovertemplate
    assert "Dominant emotion" in treemap.hovertemplate


def test_subtask22_spatial_heatmap_localizes_empty_and_batch_states() -> None:
    empty_figure = playground_app._spatial_heatmap_figure("", {}, language="en")
    batch_result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Heat Mina",
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
    batch_figure = playground_app._spatial_heatmap_figure(
        batch_result.jsonl,
        batch_result.memory_snapshot,
        language="ko",
    )

    assert empty_figure.layout.annotations[0].text == playground_app.LABELS["en"]["spatial_heatmap_empty"]
    assert batch_figure.layout.annotations[0].text == playground_app.LABELS["ko"]["spatial_heatmap_batch"]
