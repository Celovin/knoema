from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
research_power = importlib.import_module("luvoire.research.power")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask50_build_app_exposes_power_analysis_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    planned_n = next(
        component
        for component in components
        if type(component).__name__ == "Number"
        and getattr(component, "elem_id", None) == "prereg-planned-n"
    )
    power_test = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "prereg-power-test"
    )
    power_summary = next(
        component
        for component in components
        if type(component).__name__ == "Markdown"
        and getattr(component, "elem_id", None) == "prereg-power-summary"
    )

    assert planned_n.value == 126
    assert power_test.value == "independent_t"
    assert "권장 총 표본수" in power_summary.value


def test_subtask50_sample_size_estimate_matches_balanced_two_sample_rule() -> None:
    plan = research_power.estimate_sample_size(
        effect_size=0.5,
        alpha=0.05,
        target_power=0.8,
        test_family="independent_t",
    )

    assert plan.sample_size_per_group == 63
    assert plan.total_sample_size == 126
    assert "two-sample" in plan.method


def test_subtask50_preregistration_export_includes_power_analysis() -> None:
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
        80,
        "independent_t",
        0.5,
        0.05,
        0.8,
    )

    path = Path(export_path)
    try:
        assert path.suffix == ".md"
        text = path.read_text(encoding="utf-8")
        assert "### Planned sample size" in text
        assert "- Planned N: 126" in text
        assert "### Power analysis" in text
        assert "Recommended total sample size: **126**" in text
        assert text == preview
    finally:
        path.unlink(missing_ok=True)
