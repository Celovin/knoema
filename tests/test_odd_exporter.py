from __future__ import annotations

from pathlib import Path

import pytest

from luvoire.dsl import load_scenario
from luvoire.export.odd import OddReport, populate_from_simulation, render_markdown
from luvoire.export.odd.odd_schema import TODO_STUB

FIXTURE_DIR = Path(__file__).parent / "fixtures"
EXPECTED_HEADINGS = [
    "## 1. Purpose and Patterns",
    "## 2. Entities, State Variables, and Scales",
    "## 3. Process Overview and Scheduling",
    "## 4. Design Concepts",
    "## 5. Initialization",
    "## 6. Input Data",
    "## 7. Submodels",
]


def test_odd_exporter_matches_golden_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LUVOIRE_ODD_GENERATED_ON", "2026-04-23")
    scenario = load_scenario(FIXTURE_DIR / "odd_golden_scenario.yaml")
    report = populate_from_simulation(scenario.to_simulator(), scenario)

    with pytest.warns(UserWarning, match="TODO stubs"):
        rendered = render_markdown(report)

    assert rendered == (FIXTURE_DIR / "odd_golden_report.md").read_text(encoding="utf-8")


def test_odd_exporter_has_seven_canonical_sections(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LUVOIRE_ODD_GENERATED_ON", "2026-04-23")
    scenario = load_scenario(FIXTURE_DIR / "odd_golden_scenario.yaml")
    report = populate_from_simulation(scenario.to_simulator(), scenario)

    with pytest.warns(UserWarning):
        rendered = render_markdown(report)

    headings = [line for line in rendered.splitlines() if line.startswith("## ")]
    assert headings == EXPECTED_HEADINGS


def test_odd_exporter_warns_on_todo_stubs() -> None:
    report = OddReport(
        purpose_and_patterns=TODO_STUB,
        entities_state_variables_scales=TODO_STUB,
        process_overview_and_scheduling=TODO_STUB,
        design_concepts=TODO_STUB,
        initialization=TODO_STUB,
        input_data=TODO_STUB,
        submodels=TODO_STUB,
        generated_on="2026-04-23",
    )

    with pytest.warns(UserWarning, match="TODO stubs"):
        rendered = render_markdown(report)

    assert "## 7. Submodels" in rendered
