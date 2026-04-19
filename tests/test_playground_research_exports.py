from __future__ import annotations

import importlib
import sys
import zipfile
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


def test_subtask27_build_app_exposes_csv_and_latex_exports() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    csv_button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "csv-bundle-button"
    )
    latex_button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "latex-table-button"
    )

    assert csv_button.value == playground_app.LABELS["ko"]["csv_bundle_button"]
    assert latex_button.value == playground_app.LABELS["ko"]["latex_table_button"]


def test_subtask27_export_csv_bundle_writes_required_tables() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Export Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=3,
    )

    archive_path = Path(
        playground_app._export_csv_bundle(
            result.jsonl,
            result.memory_snapshot,
            "Mode: Replay only | Agents: 2",
            "English",
        )
    )

    try:
        assert archive_path.suffix == ".zip"
        with zipfile.ZipFile(archive_path) as archive:
            members = set(archive.namelist())
            assert {
                "run_summary.txt",
                "per_agent_stats.csv",
                "edge_weights.csv",
                "action_counts.csv",
                "emotion_trajectories.csv",
            }.issubset(members)
            per_agent_csv = archive.read("per_agent_stats.csv").decode("utf-8")
            assert "agent_id,total_actions,unique_targets,top_action_type" in per_agent_csv
            assert "mina" in per_agent_csv or "joon" in per_agent_csv
    finally:
        archive_path.unlink(missing_ok=True)


def test_subtask27_export_latex_table_writes_tabular_block() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Export Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=3,
    )

    latex_path = Path(
        playground_app._export_latex_table(
            result.jsonl,
            result.memory_snapshot,
            "Mode: Replay only | Agents: 2",
            "English",
        )
    )

    try:
        latex_text = latex_path.read_text(encoding="utf-8")
        assert latex_path.suffix == ".tex"
        assert r"\begin{table}" in latex_text
        assert "Single-run per-agent summary" in latex_text
        assert "Total Actions" in latex_text
    finally:
        latex_path.unlink(missing_ok=True)
