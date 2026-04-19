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


def test_subtask37_build_app_exposes_replication_package_export() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    replication_button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "replication-package-button"
    )

    assert replication_button.value == playground_app.LABELS["ko"]["replication_button"]


def test_subtask37_export_replication_package_writes_required_members() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Replication Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )

    archive_path = Path(
        playground_app._export_replication_package(
            result.jsonl,
            result.memory_snapshot,
            "Mode: Replay only | Agents: 2",
            "English",
        )
    )

    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = set(archive.namelist())
            assert {
                "README.md",
                "data/run.jsonl",
                "data/summary.txt",
                "config/reproduction_manifest.json",
                "config/environment-freeze.txt",
                "notebooks/reproduce_run.ipynb",
                "source/pyproject.toml",
                "source/playground/app.py",
            }.issubset(members)
            notebook = archive.read("notebooks/reproduce_run.ipynb").decode("utf-8")
            assert "Knoema replication notebook" in notebook
    finally:
        archive_path.unlink(missing_ok=True)
