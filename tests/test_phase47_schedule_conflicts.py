from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_simulation = importlib.import_module("playground.simulation")
knoema_package = importlib.import_module("knoema")
game_module = importlib.import_module("knoema.game")
llm_module = importlib.import_module("knoema.llm")

Environment = knoema_package.Environment
Persona = knoema_package.Persona
Personality = knoema_package.Personality
Simulator = knoema_package.Simulator
RoutineEntry = game_module.RoutineEntry
LocalClient = llm_module.LocalClient


def test_phase47_simulator_queues_shared_routine_resources() -> None:
    shared_routine = [
        RoutineEntry(
            start_hour=7,
            end_hour=9,
            location_path=("Town", "Tavern", "Kitchen"),
            default_action="craft_item",
        )
    ]
    agents = [
        Persona(
            agent_id="aria",
            name="Aria",
            age=31,
            background="Runs the prep station.",
            personality=Personality(
                openness=0.55,
                conscientiousness=0.92,
                extraversion=0.48,
                agreeableness=0.64,
                neuroticism=0.22,
            ),
            values=["order"],
            goals=["prepare breakfast"],
            routine=shared_routine,
        ),
        Persona(
            agent_id="ben",
            name="Ben",
            age=29,
            background="Arrives for the same prep station.",
            personality=Personality(
                openness=0.49,
                conscientiousness=0.61,
                extraversion=0.42,
                agreeableness=0.58,
                neuroticism=0.31,
            ),
            values=["fairness"],
            goals=["start the shift"],
            routine=shared_routine,
        ),
    ]
    simulator = Simulator(
        agents=agents,
        environment=Environment(
            start_time=datetime(2026, 4, 20, 8, 0, 0),
            location_path=("Town", "Tavern", "Kitchen"),
            conditions={"weather": "clear"},
        ),
        llm=LocalClient(lambda _messages: '{"action_type":"observe","target":null,"content":"unused"}'),
    )

    simulator.run_ticks(1)

    assert len(simulator.logs) == 2
    first_action = simulator.logs[0].action
    second_action = simulator.logs[1].action

    assert first_action.action_type == "craft_item"
    assert first_action.metadata["queue_role"] == "holder"
    assert first_action.metadata["queue_position"] == 1
    assert first_action.metadata["shared_resource"] == "kitchen"

    assert second_action.action_type == "speak"
    assert second_action.target == "aria"
    assert second_action.metadata["queue_role"] == "waiting"
    assert second_action.metadata["queue_position"] == 2
    assert second_action.metadata["shared_resource"] == "kitchen"
    assert "queue" in second_action.content.lower()


def test_phase47_playground_run_negotiates_shared_kitchen_queue() -> None:
    shared_routine_yaml = playground_simulation.routine_preset_text("shopkeeper")

    result = playground_simulation.run_playground_scenario(
        scenario_name="Village: ten agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Aria",
        primary_age=31,
        openness=0.63,
        conscientiousness=0.9,
        extraversion=0.56,
        agreeableness=0.76,
        neuroticism=0.28,
        personality_overrides={"conscientiousness": 0.9},
        ticks=1,
        agent_count=2,
        agent_overrides=[
            {
                "name": "Aria",
                "age": 31,
                "personality_overrides": {"conscientiousness": 0.9},
                "routine_text": shared_routine_yaml,
            },
            {
                "name": "Ben",
                "age": 44,
                "personality_overrides": {"conscientiousness": 0.45},
                "routine_text": shared_routine_yaml,
            },
        ],
        language="en",
    )

    rows = [json.loads(line) for line in result.jsonl.splitlines()]
    assert len(rows) == 2

    holder = rows[0]["action"]
    waiter = rows[1]["action"]

    assert holder["metadata"]["queue_role"] == "holder"
    assert holder["metadata"]["shared_resource"] == "kitchen"
    assert waiter["action_type"] == "speak"
    assert waiter["target"] == "aria"
    assert waiter["metadata"]["queue_role"] == "waiting"
    assert waiter["metadata"]["queue_position"] == 2
