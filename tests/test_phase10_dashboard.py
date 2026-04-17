from __future__ import annotations

import json

import pytest

from dashboard.components.agent_view import build_agent_cards
from dashboard.components.conversation_log import recent_rows
from dashboard.components.realtime_view import build_tick_summary, playback_window, tick_bounds
from dashboard.components.relationship_graph import build_relationship_edges
from dashboard.data import (
    filter_rows,
    load_jsonl,
    loads_jsonl,
    normalize_log_records,
    summarize_logs,
)


def _record(tick: int, agent_id: str, target: str | None, content: str) -> dict[str, object]:
    return {
        "tick": tick,
        "timestamp": f"2026-03-02T09:{tick:02d}:00",
        "agent_id": agent_id,
        "action": {
            "agent_id": agent_id,
            "timestamp": f"2026-03-02T09:{tick:02d}:00",
            "action_type": "speak",
            "target": target,
            "content": content,
            "location": "Korea > Seoul > Dorm",
        },
    }


def test_dashboard_loads_and_normalizes_jsonl(tmp_path) -> None:
    path = tmp_path / "sim.jsonl"
    records = [
        _record(0, "alice", "bob", "quiet writing time"),
        _record(1, "bob", "alice", "morning physics review"),
    ]
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    rows = normalize_log_records(load_jsonl(path))

    assert len(rows) == 2
    assert rows[0].agent_id == "alice"
    assert rows[1].target == "alice"


def test_dashboard_rejects_invalid_jsonl() -> None:
    with pytest.raises(ValueError, match="invalid JSONL"):
        loads_jsonl("{bad json")


def test_dashboard_summarizes_and_filters_rows() -> None:
    rows = normalize_log_records(
        [
            _record(0, "alice", "bob", "quiet writing time"),
            _record(1, "bob", "alice", "morning physics review"),
            _record(2, "alice", None, "private study"),
        ]
    )

    summary = summarize_logs(rows)
    filtered = filter_rows(rows, agent_id="alice", search="private")

    assert summary["total_actions"] == 3
    assert summary["agent_count"] == 2
    assert len(filtered) == 1
    assert filtered[0].content == "private study"


def test_dashboard_builds_agent_cards_relationship_edges_and_recent_rows() -> None:
    rows = normalize_log_records(
        [
            _record(0, "alice", "bob", "quiet writing time"),
            _record(1, "bob", "alice", "morning physics review"),
            _record(2, "alice", "bob", "shared schedule"),
        ]
    )

    cards = build_agent_cards(rows)
    edges = build_relationship_edges(rows)
    recent = recent_rows(rows, limit=2)

    assert cards[0]["agent_id"] == "alice"
    assert cards[0]["actions"] == 2
    assert edges[0]["source"] == "alice"
    assert edges[0]["interactions"] == 2
    assert [row.tick for row in recent] == [1, 2]


def test_dashboard_builds_realtime_playback_window_and_tick_summary() -> None:
    rows = normalize_log_records(
        [
            _record(0, "alice", "bob", "quiet writing time"),
            _record(1, "bob", "alice", "morning physics review"),
            _record(2, "alice", None, "private study"),
            _record(3, "bob", "alice", "asks about the schedule"),
        ]
    )

    window = playback_window(rows, tick_end=3, trailing_ticks=2)
    summary = build_tick_summary(window.rows)

    assert tick_bounds(rows) == (0, 3)
    assert window.tick_start == 2
    assert window.tick_end == 3
    assert [row.tick for row in window.rows] == [2, 3]
    assert summary == [
        {"tick": 2, "actions": 1, "agents": 1, "top_action": "speak", "timestamp": "2026-03-02T09:02:00"},
        {"tick": 3, "actions": 1, "agents": 1, "top_action": "speak", "timestamp": "2026-03-02T09:03:00"},
    ]
