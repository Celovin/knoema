from __future__ import annotations

import pytest

from knoema.dsl import Scenario, collect_validation_issues, validate_scenario


@pytest.mark.parametrize(
    "mutation",
    [
        {"ethics": {"fictional": False}},
        {"ethics": {"no_real_people": False}},
        {"ethics": {"no_prediction": False}},
        {"ethics": {"no_suspect_scoring": False}},
        {"ethics": {"sensitive_domain": True, "irb_notes": ""}},
        {"agents": [{"synthetic": False}]},
    ],
)
def test_phase53_ethics_validator_bypass_attempts_fail(mutation: dict[str, object]) -> None:
    payload = _safe_payload()
    if "ethics" in mutation:
        ethics = dict(payload["ethics"])  # type: ignore[arg-type]
        ethics.update(mutation["ethics"])  # type: ignore[arg-type]
        payload["ethics"] = ethics
    if "agents" in mutation:
        agents = list(payload["agents"])  # type: ignore[arg-type]
        first_agent = dict(agents[0])  # type: ignore[arg-type]
        first_agent.update(mutation["agents"][0])  # type: ignore[index,union-attr]
        payload["agents"] = [first_agent]

    scenario = Scenario.model_validate(payload)

    assert collect_validation_issues(scenario)
    with pytest.raises(ValueError, match="scenario validation failed"):
        validate_scenario(scenario)


def _safe_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "scenario_id": "red_team_bypass",
        "title": "Fictional replay",
        "domain": "public_safety_research",
        "description": "Synthetic prevention replay with fictional agents.",
        "seed": 53,
        "environment": {
            "start_time": "2026-04-19T09:00:00",
            "location_path": ["Lab"],
        },
        "agents": [
            {
                "agent_id": "observer",
                "name": "Observer",
                "age": 30,
                "background": "Synthetic review participant.",
                "personality": {
                    "openness": 0.5,
                    "conscientiousness": 0.5,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "neuroticism": 0.5,
                },
                "synthetic": True,
            }
        ],
        "ethics": {
            "fictional": True,
            "no_real_people": True,
            "no_prediction": True,
            "no_suspect_scoring": True,
            "sensitive_domain": True,
            "irb_notes": "Synthetic internal review only.",
        },
    }
