from __future__ import annotations

import json

from luvoire_bots.core import parse_bot_command, run_scenario_for_bot


def test_batch_nn_parse_bot_command_supports_ticks_and_quotes() -> None:
    command = parse_bot_command('!luvoire run "Dorm: two agents" --ticks 6')

    assert command.action == "run"
    assert command.scenario == "Dorm: two agents"
    assert command.ticks == 6


def test_batch_nn_run_scenario_for_bot_returns_jsonl_summary() -> None:
    summary = run_scenario_for_bot("Dorm", ticks=3)
    rows = [json.loads(line) for line in summary.jsonl.splitlines()]

    assert summary.scenario == "Dorm: two agents"
    assert summary.ticks == 3
    assert summary.agent_count == 2
    assert len(rows) == 6
    assert summary.action_counts
    assert "**Scenario:** Dorm: two agents" in summary.markdown
