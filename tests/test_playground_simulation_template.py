from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask58_build_app_exposes_simulation_template_fields() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    field_ids = {
        getattr(component, "elem_id", None)
        for component in components
        if type(component).__name__ == "Textbox"
    }

    assert {
        "prereg-data-generation",
        "prereg-factor-design",
        "prereg-performance-metrics",
        "prereg-aggregation",
    } <= field_ids


def test_subtask58_preregistration_export_uses_simulation_studies_sections() -> None:
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
        126,
        "independent_t",
        0.5,
        0.05,
        0.8,
        "Scenario YAML and seed schedule are frozen.",
        "2 x 2 design over stressor and agreeableness.",
        "Cooperation rate, refusal rate, trust delta.",
        "Aggregate over seeds before agent-level summaries.",
    )

    path = Path(export_path)
    try:
        text = path.read_text(encoding="utf-8")
        assert "### Data generation process" in text
        assert "Scenario YAML and seed schedule are frozen." in text
        assert "### Factor design matrix" in text
        assert "### Performance metrics" in text
        assert "### Aggregation plan" in text
        assert text == preview
    finally:
        path.unlink(missing_ok=True)
