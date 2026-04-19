from __future__ import annotations

from datetime import datetime

from knoema.cli import CliAgentConfig
from knoema.decision import build_decision_messages
from knoema.environment import Environment, EnvironmentContext
from knoema.game.schedule import RoutineEntry
from knoema.llm import LocalClient
from knoema.persona import Persona
from knoema.relationship import Relationship
from knoema.simulator import Simulator
from knoema.types import Emotion, Memory, Personality, WorldEvent


def _shopkeeper_persona() -> Persona:
    return Persona(
        agent_id="tavern_keeper",
        name="Bjorn",
        age=44,
        background="Runs the tavern and keeps a predictable village schedule.",
        personality=Personality(0.5, 0.8, 0.6, 0.6, 0.3),
        values=["routine", "reliability"],
        goals=["open the tavern on time"],
        routine=[
            RoutineEntry(7, 9, ("Town", "Tavern", "Kitchen"), "craft_item"),
            RoutineEntry(9, 12, ("Town", "Tavern", "Bar"), "speak"),
            RoutineEntry(12, 13, ("Town", "Market", "Square"), "trade_offer"),
            RoutineEntry(13, 22, ("Town", "Tavern", "Bar"), "speak"),
        ],
    )


def _memory() -> Memory:
    return Memory(
        id="mem-routine",
        agent_id="tavern_keeper",
        timestamp=datetime(2026, 4, 19, 6, 30),
        content="Prepared ingredients before opening time.",
        memory_type="episodic",
        importance=0.6,
    )


def test_phase32_cli_agent_config_accepts_routine_entries() -> None:
    config = CliAgentConfig.model_validate(
        {
            "agent_id": "tavern_keeper",
            "name": "Bjorn",
            "age": 44,
            "background": "Runs a tavern.",
            "personality": {
                "openness": 0.5,
                "conscientiousness": 0.8,
                "extraversion": 0.6,
                "agreeableness": 0.6,
                "neuroticism": 0.3,
            },
            "routine": [
                {
                    "start_hour": 7,
                    "end_hour": 9,
                    "location_path": ["Town", "Tavern", "Kitchen"],
                    "default_action": "craft_item",
                }
            ],
        }
    )

    agent = config.to_domain()

    assert agent.routine is not None
    assert agent.routine[0].location_path == ("Town", "Tavern", "Kitchen")
    assert agent.routine[0].default_action == "craft_item"


def test_phase32_simulator_applies_daily_routine_locations_across_24_ticks() -> None:
    environment = Environment(
        start_time=datetime(2026, 4, 19, 7, 0),
        location_path=("Town", "Square"),
    )
    simulator = Simulator(
        agents=[_shopkeeper_persona()],
        environment=environment,
        tick_duration_minutes=30,
        llm=LocalClient(lambda messages: '{"action_type": "observe", "target": null, "content": "fallback"}'),
    )

    try:
        logs = simulator.run_ticks(24)
    finally:
        simulator.close()

    assert len(logs) == 24
    assert logs[0].action.action_type == "craft_item"
    assert logs[0].action.location == "Town > Tavern > Kitchen"
    assert logs[4].action.action_type == "speak"
    assert logs[4].action.location == "Town > Tavern > Bar"
    assert logs[10].action.action_type == "trade_offer"
    assert logs[10].action.location == "Town > Market > Square"
    assert logs[12].action.action_type == "speak"
    assert logs[12].action.location == "Town > Tavern > Bar"


def test_phase32_decision_messages_include_daily_routine_context() -> None:
    persona = _shopkeeper_persona()
    environment = EnvironmentContext(
        agent_id="tavern_keeper",
        timestamp=datetime(2026, 4, 19, 9, 0),
        location_path=("Town", "Tavern", "Bar"),
        conditions={"weather": "clear"},
        routine_note="Currently at Town > Tavern > Bar per daily routine. Default action: speak.",
    )

    messages = build_decision_messages(
        persona=persona,
        memories=[_memory()],
        relationships={
            "guest": Relationship(
                source="tavern_keeper",
                target="guest",
                weight=0.2,
                trust=0.6,
            )
        },
        environment=environment,
        emotion=Emotion(valence=0.1, arousal=0.3, dominance=0.6),
        trigger=WorldEvent(
            timestamp=datetime(2026, 4, 19, 9, 0),
            event_type="guest.arrival",
            participants=["tavern_keeper", "guest"],
            location="Town > Tavern > Bar",
            description="A guest walks up to the bar and asks for breakfast.",
        ),
    )

    assert "Currently at Town > Tavern > Bar per daily routine." in messages[1]["content"]
