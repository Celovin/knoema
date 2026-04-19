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


def test_subtask35_build_app_exposes_preregistration_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    prereg_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "preregistration-panel"
    )
    prereg_button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "prereg-button"
    )

    assert prereg_panel.label == playground_app.LABELS["ko"]["prereg_panel"]
    assert prereg_button.value == playground_app.LABELS["ko"]["prereg_button"]


def test_subtask35_preregistration_markdown_attaches_run_digest() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Prereg Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.7,
        neuroticism=0.3,
        ticks=4,
        batch_mode=True,
        batch_runs=10,
        master_seed=20260419,
    )

    markdown = playground_app._preregistration_markdown(
        "Mode: Replay only | Agents: 2",
        result.jsonl,
        "English",
        "Dormitory cooperation study",
        "H1. Agreeableness increases cooperation.",
        "Deterministic replay across batch seeds.",
        "Primary: cooperative action rate.",
        "Use batch comparisons before qualitative interpretation.",
        True,
        "No deviations recorded.",
    )

    assert "## OSF-format pre-registration" in markdown
    assert "Freeze fingerprint" in markdown
    assert "### Attached run evidence" in markdown
    assert "JSONL digest" in markdown
    assert "Batch summary: runs=10" in markdown


def test_subtask35_export_preregistration_writes_markdown_file() -> None:
    preview, export_path = playground_app._export_preregistration(
        "Mode: Replay only | Agents: 2",
        "",
        "English",
        "Dormitory cooperation study",
        "H1. Agreeableness increases cooperation.",
        "Deterministic replay across batch seeds.",
        "Primary: cooperative action rate.",
        "Use batch comparisons before qualitative interpretation.",
        True,
        "",
    )

    path = Path(export_path)
    try:
        assert path.suffix == ".md"
        text = path.read_text(encoding="utf-8")
        assert text == preview
        assert "Dormitory cooperation study" in text
        assert "No run artifact is attached yet." in text
    finally:
        path.unlink(missing_ok=True)
