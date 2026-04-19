from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_simulation = importlib.import_module("playground.simulation")
quest_generation = importlib.import_module("playground.quest_generation")
knoema_package = importlib.import_module("knoema")
game_module = importlib.import_module("knoema.game")

Environment = knoema_package.Environment
Persona = knoema_package.Persona
Personality = knoema_package.Personality
Inventory = game_module.Inventory


def test_generate_procedural_quest_is_stable_for_same_session() -> None:
    agents = [
        Persona(
            agent_id="leader",
            name="Leader",
            age=34,
            background="Coordinates harbor repairs.",
            personality=Personality(
                openness=0.62,
                conscientiousness=0.88,
                extraversion=0.51,
                agreeableness=0.73,
                neuroticism=0.24,
                achievement=0.79,
                benevolence=0.74,
                need_for_cognition=0.68,
            ),
            values=["duty"],
            goals=["repair the damaged stall"],
            inventory=Inventory(["rope"]),
        ),
        Persona(
            agent_id="scout",
            name="Scout",
            age=22,
            background="Carries updates between stalls.",
            personality=Personality(
                openness=0.58,
                conscientiousness=0.49,
                extraversion=0.72,
                agreeableness=0.55,
                neuroticism=0.41,
            ),
            values=["speed"],
            goals=["report the queue"],
        ),
    ]
    environment = Environment(
        start_time=datetime(2026, 4, 20, 8, 0, 0),
        location_path=("Harbor Village", "Market Square"),
        conditions={
            "weather": "clear",
            "social_context": "neighbors coordinate repairs around one damaged stall",
        },
    )

    quest_a = quest_generation.generate_procedural_quest(
        agents,
        environment,
        session_id="session-a",
    )
    quest_b = quest_generation.generate_procedural_quest(
        agents,
        environment,
        session_id="session-a",
    )
    quest_c = quest_generation.generate_procedural_quest(
        agents,
        environment,
        session_id="session-c",
    )

    assert quest_a.to_metadata() == quest_b.to_metadata()
    assert quest_a.quest_id != quest_c.quest_id
    assert quest_a.giver_agent_id == "leader"
    assert quest_a.target_agent_id == "scout"
    assert "stall" in quest_a.objective.lower() or "repair" in quest_a.objective.lower()
    assert len(quest_a.success_conditions) == 2
    assert len(quest_a.failure_conditions) == 2


def test_run_playground_scenario_surfaces_procedural_quest_metadata() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Village: ten agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Aria",
        primary_age=31,
        openness=0.63,
        conscientiousness=0.82,
        extraversion=0.56,
        agreeableness=0.76,
        neuroticism=0.28,
        ticks=4,
        language="en",
    )

    quest_entries = [
        json.loads(line)
        for line in result.jsonl.splitlines()
        if json.loads(line)["action"]["action_type"] == "quest_offer"
    ]

    assert quest_entries
    metadata = quest_entries[0]["action"]["metadata"]
    assert metadata["quest_source"] == "procedural"
    assert metadata["quest_id"].startswith("quest_")
    assert metadata["quest_title"]
    assert metadata["quest_objective"]
    assert len(metadata["success_conditions"]) == 2
    assert len(metadata["failure_conditions"]) == 2
    assert "### Session Quest" in result.timeline_markdown
    assert metadata["quest_objective"] in result.timeline_markdown
