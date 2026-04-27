"""Ethics guardrail tests for Scenario DSL v2 (no_real_geometry, EPSG, h3)."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from luvoire.dsl.scenario import AgentSpec, PersonalitySpec
from luvoire.dsl.v2 import (
    EnvironmentSpecV2,
    EthicsSpecV2,
    ScenarioV2,
    validate_scenario_v2,
)


def _agent() -> AgentSpec:
    return AgentSpec(
        agent_id="alice",
        name="Alice",
        age=20,
        background="Synthetic test agent.",
        personality=PersonalitySpec(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        ),
        synthetic=True,
    )


def _scenario(
    *,
    epsg: str | None = None,
    h3_cell: str | None = None,
    ethics: EthicsSpecV2 | None = None,
) -> ScenarioV2:
    env_kwargs: dict[str, object] = {
        "start_time": datetime(2026, 4, 27, 9, 0),
        "location_path": ("Synthetic World", "Plaza A"),
        "conditions": {"weather": "clear"},
    }
    if h3_cell is not None:
        env_kwargs["h3_cell"] = h3_cell
    if epsg is not None:
        env_kwargs["epsg"] = epsg
    return ScenarioV2(
        scenario_id="ethics_check",
        title="Ethics Check",
        domain="academic_research",
        description="Synthetic ethics test.",
        seed=1,
        environment=EnvironmentSpecV2(**env_kwargs),
        agents=[_agent()],
        ethics=ethics or EthicsSpecV2(),
    )


def test_no_real_geometry_blocks_real_epsg() -> None:
    scenario = _scenario(epsg="EPSG:5174")
    with pytest.raises(ValueError, match="no_real_geometry"):
        validate_scenario_v2(scenario)


def test_no_real_geometry_allows_synthetic_epsg() -> None:
    scenario = _scenario(epsg="luvoire-synthetic-v1")
    validate_scenario_v2(scenario)


def test_no_real_geometry_off_allows_any_epsg() -> None:
    scenario = _scenario(
        epsg="EPSG:5174",
        ethics=EthicsSpecV2(no_real_geometry=False),
    )
    validate_scenario_v2(scenario)


def test_h3_cell_format_enforced() -> None:
    with pytest.raises(ValidationError):
        _scenario(h3_cell="not-a-real-cell")


def test_h3_cell_valid_value_accepted() -> None:
    scenario = _scenario(h3_cell="8830e1ad81fffff")
    validate_scenario_v2(scenario)


def test_disallowed_phrase_v2_rejected() -> None:
    scenario = ScenarioV2(
        scenario_id="phrase_test",
        title="Synthetic Plaza",
        domain="academic_research",
        description="This scenario is meant to predict crime.",
        seed=1,
        environment=EnvironmentSpecV2(
            start_time=datetime(2026, 4, 27, 9, 0),
            location_path=("Synthetic World", "Plaza A"),
        ),
        agents=[_agent()],
    )
    with pytest.raises(ValueError, match="Disallowed purpose phrase"):
        validate_scenario_v2(scenario)


def test_ethics_default_no_real_geometry_is_true() -> None:
    ethics = EthicsSpecV2()
    assert ethics.no_real_geometry is True


def test_ethics_default_demographic_projection_is_false() -> None:
    ethics = EthicsSpecV2()
    assert ethics.demographic_projection is False
    assert ethics.pssdp_mode is False


def test_demographic_projection_requires_no_prediction() -> None:
    scenario = _scenario(
        ethics=EthicsSpecV2(
            demographic_projection=True,
            no_prediction=False,
        ),
    )
    with pytest.raises(ValueError, match="demographic_projection"):
        validate_scenario_v2(scenario)


def test_demographic_projection_with_no_prediction_true_is_allowed() -> None:
    scenario = _scenario(
        ethics=EthicsSpecV2(
            demographic_projection=True,
            no_prediction=True,
        ),
    )
    validate_scenario_v2(scenario)


def test_pssdp_mode_requires_no_prediction() -> None:
    scenario = _scenario(
        ethics=EthicsSpecV2(
            pssdp_mode=True,
            no_prediction=False,
        ),
    )
    with pytest.raises(ValueError, match="pssdp_mode"):
        validate_scenario_v2(scenario)


def test_pssdp_mode_requires_no_suspect_scoring() -> None:
    scenario = _scenario(
        ethics=EthicsSpecV2(
            pssdp_mode=True,
            no_prediction=True,
            no_suspect_scoring=False,
        ),
    )
    with pytest.raises(ValueError, match="pssdp_mode"):
        validate_scenario_v2(scenario)


def test_pssdp_mode_with_all_guardrails_active_is_allowed() -> None:
    scenario = _scenario(
        ethics=EthicsSpecV2(
            pssdp_mode=True,
            demographic_projection=True,
            no_prediction=True,
            no_suspect_scoring=True,
        ),
    )
    validate_scenario_v2(scenario)
