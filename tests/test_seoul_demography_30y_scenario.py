"""Tests for the 30-year synthetic demographic scenario."""

from __future__ import annotations

import json
from pathlib import Path

from luvoire.dsl.v2 import load_scenario_v2, validate_scenario_v2
from scenarios.seoul_demography_30y import run_scenario as scenario

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_YAML = ROOT / "scenarios" / "seoul_demography_30y" / "scenario.yaml"
SUMMARY_JSON = (
    ROOT
    / "scenarios"
    / "seoul_demography_30y"
    / "results"
    / "demography_summary.json"
)


# --- DSL v2 loading -------------------------------------------------------


def test_scenario_yaml_loads_via_dsl_v2() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    assert loaded.scenario_id == "seoul_demography_30y"
    assert loaded.schema_version == "2.0"


def test_scenario_yaml_carries_demographic_projection_and_pssdp_flags() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    assert loaded.ethics.demographic_projection is True
    assert loaded.ethics.pssdp_mode is True
    # Guardrails remain in force even when the new flags are set.
    assert loaded.ethics.no_prediction is True
    assert loaded.ethics.no_suspect_scoring is True
    assert loaded.ethics.no_real_geometry is True


def test_scenario_yaml_passes_full_validation() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    # Validator interlock: demographic_projection + pssdp_mode require
    # no_prediction and no_suspect_scoring; the scenario's ethics block
    # has all four set so validation must pass.
    validate_scenario_v2(loaded)


def test_scenario_yaml_has_kosis_tier_b_references() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    assert loaded.parameters["baseline_tfr"].tier == "B"
    assert loaded.parameters["baseline_tfr"].source == "KOSIS 출생통계"
    assert loaded.parameters["baseline_tfr"].table_id == "1B36E27"
    assert loaded.parameters["baseline_life_expectancy"].tier == "B"


def test_scenario_yaml_has_three_fertility_sweep_knob() -> None:
    loaded = load_scenario_v2(SCENARIO_YAML)
    sweep = loaded.parameters["fertility_scale_sweep"]
    assert sweep.tier == "C"
    # range 0.85 to 1.15 mirrors KOSTAT low / medium / high reference triple.
    assert sweep.range == (0.85, 1.15)


# --- Determinism ----------------------------------------------------------


def test_run_scenario_is_deterministic_per_seed() -> None:
    summary_a = scenario.run(seed=20260428)
    summary_b = scenario.run(seed=20260428)
    assert summary_a["summary_sha256"] == summary_b["summary_sha256"]


def test_run_scenario_diverges_under_different_seeds() -> None:
    summary_a = scenario.run(seed=1)
    summary_b = scenario.run(seed=2)
    assert summary_a["summary_sha256"] != summary_b["summary_sha256"]


def test_committed_summary_matches_freshly_built_summary() -> None:
    fresh = scenario.run()
    committed = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    assert fresh["summary_sha256"] == committed["summary_sha256"]


# --- Output shape and policy invariants ----------------------------------


def test_summary_includes_three_canonical_fertility_scenarios() -> None:
    summary = scenario.run()
    assert set(summary["scenarios"].keys()) == {
        "low_fertility",
        "medium_fertility",
        "high_fertility",
    }


def test_summary_horizon_is_thirty_years() -> None:
    summary = scenario.run()
    assert summary["horizon_years"] == 30


def test_summary_num_cells_is_twenty_five() -> None:
    summary = scenario.run()
    assert summary["num_cells"] == 25


def test_per_cell_events_have_no_per_person_keys() -> None:
    """Regression — output keys must be synthetic-grid cell ids only,
    never per-person identifiers.
    """

    summary = scenario.run()
    for label, payload in summary["scenarios"].items():
        for cell_id in payload["per_cell_events"]:
            assert cell_id.startswith("synthetic-grid-r"), (
                f"scenario {label} emitted a non-cell key {cell_id!r} — "
                "per-person output is forbidden"
            )


def test_per_cell_events_are_aggregate_integer_counts() -> None:
    summary = scenario.run()
    for payload in summary["scenarios"].values():
        for count in payload["per_cell_events"].values():
            assert isinstance(count, int)
            assert count >= 0


def test_year_h_is_thirty_years_after_initial_year() -> None:
    summary = scenario.run()
    for payload in summary["scenarios"].values():
        assert payload["year"] == 2056


def test_higher_fertility_yields_larger_year_h_total() -> None:
    summary = scenario.run()
    low = summary["scenarios"]["low_fertility"]["year_h_total"]
    medium = summary["scenarios"]["medium_fertility"]["year_h_total"]
    high = summary["scenarios"]["high_fertility"]["year_h_total"]
    assert low <= medium <= high


def test_region_label_is_string_only() -> None:
    """Regression — region_label must be a string, never a coordinate
    tuple or geometry object.
    """

    summary = scenario.run()
    for payload in summary["scenarios"].values():
        assert isinstance(payload["region_label"], str)
        assert payload["region_label"] == "서울특별시 강남구"
