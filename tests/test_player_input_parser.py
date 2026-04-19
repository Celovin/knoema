from __future__ import annotations

import importlib
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

player_input_parser = importlib.import_module("playground.player_input_parser")


def test_subtask33_parser_maps_attack_command_to_attack_target() -> None:
    parsed = player_input_parser.parse_player_input(
        "attack Bjorn",
        agent_id="player-1",
        timestamp=datetime(2026, 4, 19, 18, 0, 0),
        location="Town > Tavern > Bar",
        roster=[("player-1", "Player"), ("npc-1", "Bjorn")],
        language="en",
    )

    assert parsed is not None
    assert parsed.action_type == "attack_target"
    assert parsed.target == "npc-1"


def test_subtask33_parser_defaults_korean_order_to_speak_with_target() -> None:
    parsed = player_input_parser.parse_player_input(
        "Bjorn에게 맥주 1개 주문",
        agent_id="player-1",
        timestamp=datetime(2026, 4, 19, 18, 0, 0),
        location="Town > Tavern > Bar",
        roster=[("player-1", "Player"), ("npc-1", "Bjorn")],
        language="ko",
    )

    assert parsed is not None
    assert parsed.action_type == "speak"
    assert parsed.target == "npc-1"
    assert parsed.content == "Bjorn에게 맥주 1개 주문"


def test_subtask33_help_command_returns_none_and_localized_help() -> None:
    parsed = player_input_parser.parse_player_input(
        "/help",
        agent_id="player-1",
        timestamp=datetime(2026, 4, 19, 18, 0, 0),
        location="Town > Tavern > Bar",
        roster=[("player-1", "Player"), ("npc-1", "Bjorn")],
        language="ko",
    )

    assert parsed is None
    assert "`/quest" in player_input_parser.player_help_text("ko")
