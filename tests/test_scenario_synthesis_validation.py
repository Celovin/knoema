from __future__ import annotations

import json

import pytest

from knoema.scenario_synthesis import ScenarioSynthesisError, synthesize_scenario


def test_batch_v_rejects_invalid_trait_values_from_llm_response() -> None:
    response = {
        "title": "Invalid trait",
        "description": "A generated scenario with an invalid trait value.",
        "language": "en",
        "location_path": ["Generated World", "Lab"],
        "agents": [
            {
                "agent_id": "agent_1",
                "name": "BadVector",
                "age": 30,
                "background": "Synthetic participant.",
                "personality": {
                    "openness": -1.0,
                    "conscientiousness": 0.5,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "neuroticism": 0.5,
                },
            }
        ],
        "events": [
            {
                "event_type": "invalid",
                "location": "Lab",
                "description": "Invalid trait probe.",
                "participants": ["agent_1"],
            }
        ],
    }

    with pytest.raises(ScenarioSynthesisError):
        synthesize_scenario("invalid trait probe", "en", llm_response=json.dumps(response))
