from __future__ import annotations

import json

from knoema.cli import SimulationRunConfig
from knoema.scenario_synthesis import scenario_to_yaml, synthesize_scenario


def test_batch_v_synthesizes_valid_run_config_from_natural_language() -> None:
    config = synthesize_scenario("중세 시장에서 상인 3명과 고객 2명이 가격을 협상한다", "ko")
    validated = SimulationRunConfig.model_validate(config)

    assert len(validated.agents) == 5
    assert validated.environment.location_path[-1] == "Stall Row"
    assert validated.runtime.prompt_language == "ko"
    assert validated.events[0].participants == [agent.agent_id for agent in validated.agents]
    assert "agents:" in scenario_to_yaml(config)


def test_batch_v_accepts_structured_llm_response() -> None:
    response = {
        "title": "Office escalation",
        "description": "A product team decides how to respond to a missed launch date.",
        "language": "en",
        "location_path": ["Generated World", "Office", "War Room"],
        "agents": [
            {
                "agent_id": "agent_1",
                "name": "Rin",
                "age": 31,
                "background": "A product lead coordinating stakeholders.",
                "personality": {
                    "openness": 0.7,
                    "conscientiousness": 0.8,
                    "extraversion": 0.5,
                    "agreeableness": 0.6,
                    "neuroticism": 0.4,
                },
                "values": ["clarity"],
                "goals": ["choose a response"],
            }
        ],
        "events": [
            {
                "event_type": "launch.missed",
                "location": "War Room",
                "description": "The launch gate slips by one week.",
                "participants": ["agent_1"],
            }
        ],
    }

    config = synthesize_scenario("office launch slip", "en", llm_response=json.dumps(response))

    assert config["agents"][0]["name"] == "Rin"
    assert config["description_en"] == response["description"]
