from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import get_args

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_simulation = importlib.import_module("playground.simulation")
simulator_module = importlib.import_module("luvoire.simulator")
types_module = importlib.import_module("luvoire.types")
luvoire_package = importlib.import_module("luvoire")
game_module = importlib.import_module("luvoire.game")
llm_module = importlib.import_module("luvoire.llm")

Environment = luvoire_package.Environment
Persona = luvoire_package.Persona
Personality = luvoire_package.Personality
Simulator = luvoire_package.Simulator
Faction = game_module.Faction
Inventory = game_module.Inventory
LocalClient = llm_module.LocalClient
SimulationLogEntry = simulator_module.SimulationLogEntry
ACTION_TYPES = types_module.ACTION_TYPES
Action = types_module.Action
ActionType = types_module.ActionType
GAME_ACTION_TYPES = types_module.GAME_ACTION_TYPES


def _base_game_metadata(action_type: str) -> dict[str, object]:
    if action_type == "attack_target":
        return {"damage": 8}
    if action_type == "use_skill":
        return {"skill_id": "skill_1"}
    if action_type in {"use_item", "pickup_item", "drop_item"}:
        return {"item_id": "rope"}
    if action_type == "trade_offer":
        return {"give_items": ["rope"], "receive_items": ["torch"]}
    if action_type in {"quest_offer", "quest_accept", "quest_complete"}:
        return {"quest_id": "quest_village_1"}
    if action_type in {"faction_join", "faction_betray"}:
        return {"faction_id": "leader"}
    if action_type == "craft_item":
        return {"materials": ["wood", "ore"], "item_id": "crafted_item_1"}
    if action_type == "level_up":
        return {"stat": "conscientiousness"}
    return {}

def test_subtask31_game_action_type_literals_match_exports() -> None:
    assert len(GAME_ACTION_TYPES) == 15
    assert set(GAME_ACTION_TYPES) <= set(get_args(ActionType))
    assert set(get_args(ActionType)) == set(ACTION_TYPES)


def test_subtask31_game_action_jsonl_roundtrip_preserves_metadata() -> None:
    now = datetime(2026, 4, 19, 18, 0, 0)

    for action_type in GAME_ACTION_TYPES:
        action = Action(
            agent_id="leader",
            timestamp=now,
            action_type=action_type,
            target="scout",
            content=f"performs {action_type}",
            location="Village > Market Square",
            metadata=_base_game_metadata(action_type),
        )
        entry = SimulationLogEntry(
            tick=2,
            timestamp=now,
            agent_id="leader",
            action=action,
        )
        decoded = json.loads(json.dumps(entry.to_json_dict(), ensure_ascii=False))

        assert decoded["action"]["action_type"] == action_type
        for key, value in _base_game_metadata(action_type).items():
            assert decoded["action"]["metadata"][key] == value


def test_subtask31_inventory_and_faction_helpers_support_mutation() -> None:
    inventory = Inventory()
    inventory.add("rope")
    inventory.add("apple")
    assert inventory.has("rope") is True
    assert inventory.remove("rope") is True
    assert inventory.has("rope") is False

    faction = Faction()
    assert faction.join("leader") == 0.5
    assert faction.reputation("leader") == 0.5
    assert faction.betray("leader") == -0.7
    assert faction.reputation("leader") == -0.7


def test_subtask31_simulator_mutates_inventory_and_factions_from_game_actions() -> None:
    agent = Persona(
        agent_id="leader",
        name="Leader",
        age=34,
        background="Village captain",
        personality=Personality(0.7, 0.8, 0.5, 0.6, 0.2),
        values=["duty"],
        goals=["organize patrols"],
        inventory=Inventory(["rope"]),
    )
    responses = iter(
        [
            json.dumps(
                {
                    "action_type": "pickup_item",
                    "target": None,
                    "content": "picks up herbs",
                    "metadata": {"item_id": "herbs"},
                }
            ),
            json.dumps(
                {
                    "action_type": "faction_join",
                    "target": None,
                    "content": "joins the wardens",
                    "metadata": {"faction_id": "wardens"},
                }
            ),
        ]
    )
    simulator = Simulator(
        agents=[agent],
        environment=Environment(
            start_time=datetime(2026, 4, 19, 9, 0),
            location_path=("Village", "Square"),
            conditions={"weather": "clear"},
        ),
        llm=LocalClient(lambda _messages: next(responses)),
    )

    simulator.run_ticks(2)

    assert agent.inventory is not None
    assert agent.inventory.has("herbs") is True
    assert agent.factions == {"wardens": 0.5}


def test_subtask31_village_replay_with_leader_emits_quest_offer() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Village: ten agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Leader",
        primary_age=41,
        openness=0.6,
        conscientiousness=0.85,
        extraversion=0.5,
        agreeableness=0.5,
        neuroticism=0.2,
        ticks=8,
        agent_overrides=[
            {
                "name": "Leader",
                "age": 41,
                "personality_overrides": {"conscientiousness": 0.85},
                "factions": {"leader": 0.9},
            }
        ],
    )

    action_types = [json.loads(line)["action"]["action_type"] for line in result.jsonl.splitlines()]

    assert "quest_offer" in action_types
