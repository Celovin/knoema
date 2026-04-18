from __future__ import annotations

import json

from tests.reproducibility._helpers import (
    build_seeded_simulator,
    export_log_text,
    replay_summary_from_jsonl,
)


def test_jsonl_logs_restore_replay_summary_matching_original_run() -> None:
    simulator = build_seeded_simulator(seed=20260418)
    logs = simulator.run(duration_days=1)
    replay_summary = replay_summary_from_jsonl(export_log_text(logs))

    assert replay_summary["action_count"] == len(logs)
    assert replay_summary["agents"] == ["alice", "bob", "cara"]
    assert replay_summary["ticks"] == [0, 1, 2, 3]
    assert len(replay_summary["relationship_edges"]) == simulator.relationships.to_networkx().number_of_edges()
    assert json.dumps(replay_summary, sort_keys=True) == json.dumps(
        replay_summary_from_jsonl(export_log_text(logs)),
        sort_keys=True,
    )
