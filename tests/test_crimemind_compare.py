"""Tests for the CrimeMind RAT-prompt comparison harness (T3.4)."""

from __future__ import annotations

import json
from pathlib import Path

from luvoire.dsl.v2 import load_scenario_v2
from scenarios.crimemind_compare import compare as scenario

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_YAML = ROOT / "scenarios" / "crimemind_compare" / "scenario.yaml"
SUMMARY_JSON = (
    ROOT
    / "scenarios"
    / "crimemind_compare"
    / "results"
    / "comparison_summary.json"
)


def test_scenario_yaml_loads_via_dsl_v2() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    assert loaded.scenario_id == "crimemind_compare_v1"
    assert loaded.schema_version == "2.0"
    assert loaded.ethics.no_real_geometry is True
    assert loaded.ethics.no_prediction is True
    assert loaded.ethics.no_suspect_scoring is True


def test_scenario_yaml_has_three_tier_c_weights() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    tiers = {name: spec.tier for name, spec in loaded.parameters.items()}
    assert tiers["motivation_weight"] == "C"
    assert tiers["exposure_weight"] == "C"
    assert tiers["guardian_gap_weight"] == "C"
    assert tiers["opportunity_definition"] == "A"


def test_run_is_deterministic_per_seed() -> None:
    a = scenario.run(seed=20260427)
    b = scenario.run(seed=20260427)
    assert a == b


def test_three_regimes_recorded() -> None:
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    names = [r["name"] for r in summary["regimes"]]
    assert names == ["equal_weights", "motivation_heavy", "guardian_heavy"]


def test_committed_summary_matches_default_run() -> None:
    committed = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    fresh = scenario.run(seed=committed["seed"])
    assert fresh["summary_sha256"] == committed["summary_sha256"]


def test_equal_weights_regime_emits_more_events_than_handicapped() -> None:
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    by_name = {r["name"]: r["events"] for r in summary["regimes"]}
    assert by_name["equal_weights"] >= by_name["motivation_heavy"]
    assert by_name["equal_weights"] >= by_name["guardian_heavy"]


def test_summary_threshold_matches_locked_default() -> None:
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    assert summary["threshold"] == 0.125


def test_grid_dimensions_recorded() -> None:
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    assert summary["grid_rows"] == 6
    assert summary["grid_cols"] == 6
