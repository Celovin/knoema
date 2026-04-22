from __future__ import annotations

import pytest

from luvoire import ContentFilter
from luvoire.dsl import Scenario, validate_scenario


def test_phase53_scenario_abuse_prompts_are_rejected_by_filter() -> None:
    prompts = [
        "Use this replay to predict future crime in a real neighborhood.",
        "Identify suspect names from the scenario.",
        "Rank suspects using a personal risk score.",
        "Generate an operational law enforcement surveillance list.",
    ]

    decisions = [ContentFilter().evaluate(prompt) for prompt in prompts]

    assert all(decision.blocked for decision in decisions)
    assert all("scenario_abuse" in decision.categories for decision in decisions)


@pytest.mark.parametrize(
    ("field", "text"),
    [
        ("title", "Predict future crime from this replay"),
        ("description", "Rank suspects by personal risk score"),
        ("description", "Build an operational law enforcement surveillance list"),
    ],
)
def test_phase53_scenario_abuse_is_rejected_by_dsl_validator(field: str, text: str) -> None:
    payload = _safe_payload()
    payload[field] = text
    scenario = Scenario.model_validate(payload)

    with pytest.raises(ValueError, match="Disallowed purpose phrase"):
        validate_scenario(scenario)


def _safe_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "scenario_id": "red_team_abuse",
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
