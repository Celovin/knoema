"""Parser tests for Scenario DSL v2: v1 deprecation upgrade and v2 load."""

from __future__ import annotations

from pathlib import Path

import pytest

from luvoire.dsl.v2 import (
    ScenarioV2,
    load_scenario_v2,
    loads_scenario_v2,
)
from luvoire.dsl.v2.parameters import TierAParam, TierBParam, TierCParam
from luvoire.dsl.v2.parser import _upgrade_v1_to_v2

FIXTURE_V2 = Path(__file__).parent / "fixtures" / "scenarios" / "v2_rat_baseline.yaml"
FIXTURE_V1 = Path(__file__).parent / "fixtures" / "scenarios" / "v1_legacy.yaml"


def test_load_v2_baseline_fixture() -> None:
    scenario = load_scenario_v2(FIXTURE_V2)
    assert isinstance(scenario, ScenarioV2)
    assert scenario.schema_version == "2.0"
    assert "opportunity_definition" in scenario.parameters
    assert isinstance(scenario.parameters["opportunity_definition"], TierAParam)
    assert isinstance(scenario.parameters["schedule_prior"], TierBParam)
    assert isinstance(scenario.parameters["guardianship_density"], TierCParam)


def test_load_v2_h3_cell_present() -> None:
    scenario = load_scenario_v2(FIXTURE_V2)
    assert scenario.environment.h3_cell == "8830e1ad81fffff"
    assert scenario.environment.epsg == "luvoire-synthetic-v1"


def test_load_v1_emits_deprecation_warning() -> None:
    with pytest.warns(DeprecationWarning, match="DSL v1.0 is deprecated"):
        scenario = load_scenario_v2(FIXTURE_V1)
    assert scenario.schema_version == "2.0"
    assert scenario.parameters == {}
    assert scenario.ethics.no_real_geometry is True


def test_upgrade_v1_to_v2_adds_no_real_geometry_default() -> None:
    payload = {
        "schema_version": "1.0",
        "ethics": {
            "fictional": True,
            "no_real_people": True,
            "no_prediction": True,
            "no_suspect_scoring": True,
        },
    }
    upgraded = _upgrade_v1_to_v2(payload)
    assert upgraded["schema_version"] == "2.0"
    assert upgraded["parameters"] == {}
    assert upgraded["ethics"]["no_real_geometry"] is True


def test_upgrade_v1_preserves_existing_no_real_geometry() -> None:
    payload = {
        "schema_version": "1.0",
        "ethics": {"no_real_geometry": False},
    }
    upgraded = _upgrade_v1_to_v2(payload)
    assert upgraded["ethics"]["no_real_geometry"] is False


def test_loads_scenario_v2_rejects_non_mapping() -> None:
    with pytest.raises(ValueError, match="must be a mapping"):
        loads_scenario_v2("- a\n- b\n")


def test_load_v2_validate_false_skips_validator() -> None:
    payload = (FIXTURE_V2).read_text(encoding="utf-8")
    scenario = loads_scenario_v2(payload, validate=False)
    assert scenario.schema_version == "2.0"
