"""Tests for the synthetic Seoul-style 5x5 scenario (T2.4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from luvoire.dsl.v2 import load_scenario_v2
from scenarios.synthetic_seoul import run_scenario as scenario

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_YAML = ROOT / "scenarios" / "synthetic_seoul" / "scenario.yaml"
SUMMARY_JSON = (
    ROOT / "scenarios" / "synthetic_seoul" / "results" / "synthetic_seoul_summary.json"
)


def test_scenario_yaml_loads_via_dsl_v2() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    assert loaded.scenario_id == "synthetic_seoul_5x5"
    assert loaded.schema_version == "2.0"
    assert loaded.ethics.no_real_geometry is True


def test_scenario_yaml_has_three_tier_parameters() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    tiers = {name: spec.tier for name, spec in loaded.parameters.items()}
    assert tiers["opportunity_definition"] == "A"
    assert tiers["schedule_prior"] == "B"
    assert tiers["convergence_threshold"] == "C"


def test_scenario_yaml_uses_synthetic_epsg() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    assert loaded.environment.epsg == "luvoire-synthetic-v1"


def test_run_scenario_is_deterministic_per_seed() -> None:
    a = scenario.run(seed=20260427)
    b = scenario.run(seed=20260427)
    assert a == b, "same seed must reproduce identical summary"


def test_run_scenario_changes_with_seed() -> None:
    a = scenario.run(seed=1)
    b = scenario.run(seed=2)
    assert (
        a["per_cell_events"] != b["per_cell_events"]
        or a["total_opportunity_events"] != b["total_opportunity_events"]
    ), "different seeds should diverge in event distribution"


def test_committed_summary_matches_default_run() -> None:
    committed = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    fresh = scenario.run(seed=committed["seed"])
    assert fresh["summary_sha256"] == committed["summary_sha256"]


def test_grid_event_counts_sum_matches_total() -> None:
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    per_cell_total = sum(summary["per_cell_events"].values())
    assert per_cell_total == summary["total_opportunity_events"]


def test_cells_with_events_consistent_with_per_cell() -> None:
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    expected = sum(1 for n in summary["per_cell_events"].values() if n > 0)
    assert summary["cells_with_events"] == expected


def test_activity_sample_uses_canonical_codes() -> None:
    canonical = {
        "sleep",
        "work_or_school",
        "commute",
        "meals",
        "leisure",
        "care",
        "other",
    }
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    for sample in summary["activity_sample"]:
        assert sample in canonical


def test_summary_records_module_version_through_scenario_constants() -> None:
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    assert summary["scenario_id"] == "synthetic_seoul_5x5"
    assert summary["grid_rows"] == 5
    assert summary["grid_cols"] == 5
    assert summary["threshold"] == pytest.approx(0.125)
