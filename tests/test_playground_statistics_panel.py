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


def test_subtask24_build_app_exposes_statistics_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    statistics_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "statistics-panel"
    )

    assert statistics_panel.label == playground_app.LABELS["ko"]["statistics_panel"]


def test_subtask24_statistical_analysis_markdown_reports_batch_tests() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Stats Mina",
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

    assert "### Statistical analysis" in markdown
    assert "Mann-Whitney U" in markdown
    assert "chi-square" in markdown
    assert "Cohen's d" in markdown
    assert "Cliff's delta" in markdown
    assert "Holm step-down" in markdown


def test_subtask24_statistical_analysis_markdown_requires_batch_mode() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Solo Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=2,
    )

    markdown = playground_app._statistical_analysis_markdown(result.jsonl, "English")

    assert markdown == playground_app.LABELS["en"]["statistics_batch_only"]
