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
decision = importlib.import_module("knoema.decision")
simulator = importlib.import_module("knoema.simulator")
types_module = importlib.import_module("knoema.types")

parse_action_response = decision.parse_action_response
SimulationLogEntry = simulator.SimulationLogEntry
ACTION_TYPES = types_module.ACTION_TYPES
Action = types_module.Action
ActionType = types_module.ActionType
SOCIAL_ACTION_TYPES = types_module.SOCIAL_ACTION_TYPES


def test_subtask16_action_type_literal_matches_exported_action_list() -> None:
    assert set(get_args(ActionType)) == set(ACTION_TYPES)
    assert len(SOCIAL_ACTION_TYPES) == 20


def test_subtask16_action_templates_cover_all_verbs_in_english_and_korean() -> None:
    templates = playground_simulation.load_action_templates()

    for language in ("en", "ko"):
        assert set(templates[language]) == set(ACTION_TYPES)
        assert all(str(templates[language][action_type]).strip() for action_type in ACTION_TYPES)


def test_subtask16_action_jsonl_roundtrip_preserves_all_verb_types_and_metadata() -> None:
    now = datetime(2026, 4, 19, 16, 0, 0)

    for action_type in ACTION_TYPES:
        action = Action(
            agent_id="mina",
            timestamp=now,
            action_type=action_type,
            target="joon",
            content=f"performs {action_type}",
            location="Seoul > University Dorm > Shared Kitchen",
            metadata={"verb": action_type},
        )
        entry = SimulationLogEntry(
            tick=1,
            timestamp=now,
            agent_id="mina",
            action=action,
        )
        decoded = json.loads(json.dumps(entry.to_json_dict(), ensure_ascii=False))

        assert decoded["action"]["action_type"] == action_type
        assert decoded["action"]["metadata"]["verb"] == action_type


def test_subtask16_parse_action_response_reads_metadata_dict() -> None:
    action = parse_action_response(
        '{"action_type":"comfort","target":"joon","content":"steadying the room","metadata":{"tone":"soft"}}',
        agent_id="mina",
        timestamp=datetime(2026, 4, 19, 16, 5, 0),
        location="Dorm",
    )

    assert action.action_type == "comfort"
    assert action.metadata == {"tone": "soft"}


def test_subtask16_dorm_replay_uses_at_least_five_distinct_action_types_in_four_ticks() -> None:
    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Test Mina",
        primary_age=24,
        openness=0.8,
        conscientiousness=0.7,
        extraversion=0.6,
        agreeableness=0.5,
        neuroticism=0.4,
        ticks=4,
    )

    rows = [json.loads(line) for line in result.jsonl.splitlines()]
    action_types = {row["action"]["action_type"] for row in rows}

    assert len(action_types) >= 5
    assert action_types <= set(ACTION_TYPES)
