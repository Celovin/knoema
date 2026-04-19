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


def test_subtask41_trait_correlation_study_uses_one_hundred_batch_runs() -> None:
    study = playground_simulation.compute_trait_correlation_study()

    assert study.sample_count == 100
    assert len(study.trait_names) == len(playground_simulation.PERSONA_TRAIT_FIELDS) == 30
    assert len(study.correlation_matrix) == 30
    assert all(len(row) == 30 for row in study.correlation_matrix)
    assert all(
        study.correlation_matrix[index][index] == 1.0
        for index in range(len(study.trait_names))
    )
    assert study.max_pair[0]
    assert study.max_pair[1]
    assert 0.0 <= abs(study.max_pair[2]) <= 1.0


def test_subtask41_summary_reports_threshold_and_max_pair() -> None:
    summary = playground_simulation.trait_correlation_summary(language="en")

    assert "Batch runs" in summary
    assert "100" in summary
    assert "Max |r| pair" in summary
    assert "Merge threshold" in summary


def test_subtask41_build_app_exposes_trait_correlation_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    trait_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "trait-correlation-panel"
    )
    trait_plot = next(
        component
        for component in components
        if type(component).__name__ == "Plot"
        and getattr(component, "elem_id", None) == "trait-correlation-heatmap"
    )
    trait_summary = next(
        component
        for component in components
        if type(component).__name__ == "Markdown"
        and getattr(component, "elem_id", None) == "trait-correlation-summary"
    )

    assert trait_panel.label == playground_app.LABELS["ko"]["trait_matrix_panel"]
    assert trait_plot.label == playground_app.LABELS["ko"]["trait_matrix_plot"]
    assert "100" in str(trait_summary.value)
