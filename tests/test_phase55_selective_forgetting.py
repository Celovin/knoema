from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from knoema import Memory, SQLiteFaissMemoryStore


def test_selective_forgetting_drops_stale_entries(tmp_path: Path) -> None:
    store = SQLiteFaissMemoryStore(tmp_path / "forgetting.sqlite3")
    reference_time = datetime(2026, 4, 19, 12, 0)
    try:
        store.add_many(
            [
                Memory(
                    id="old-low-1",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(days=30),
                    content="Old cafeteria gossip about a forgotten umbrella.",
                    memory_type="episodic",
                    importance=0.10,
                ),
                Memory(
                    id="old-low-2",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(days=20),
                    content="Old hallway observation about a missed study group.",
                    memory_type="episodic",
                    importance=0.20,
                ),
                Memory(
                    id="recent-low",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(hours=2),
                    content="Recent note: the projector cable is in drawer C.",
                    memory_type="episodic",
                    importance=0.20,
                ),
                Memory(
                    id="old-high",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(days=25),
                    content="Critical incident report: fire drill exit map moved to lobby board.",
                    memory_type="episodic",
                    importance=0.95,
                ),
                Memory(
                    id="semantic-old",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(days=40),
                    content="Semantic summary: Alice usually studies in the east library wing.",
                    memory_type="semantic",
                    importance=0.15,
                ),
            ]
        )

        result = store.apply_selective_forgetting(as_of=reference_time, retain_at_least=3)

        assert result.dropped_ids == ("old-low-1", "old-low-2")
        assert result.dropped_count == 2
        assert result.retained_count == 3
        assert [memory.id for memory in store.all()] == [
            "recent-low",
            "old-high",
            "semantic-old",
        ]
    finally:
        store.close()


def test_selective_forgetting_keeps_retrieval_operational(tmp_path: Path) -> None:
    store = SQLiteFaissMemoryStore(tmp_path / "forgetting-retrieval.sqlite3")
    reference_time = datetime(2026, 4, 19, 12, 0)
    try:
        store.add_many(
            [
                Memory(
                    id="stale-note",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(days=18),
                    content="Old reminder about cafeteria soup specials.",
                    memory_type="episodic",
                    importance=0.15,
                ),
                Memory(
                    id="live-note",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(hours=1),
                    content="The projector cable is in drawer C near the podium.",
                    memory_type="episodic",
                    importance=0.65,
                ),
                Memory(
                    id="semantic-policy",
                    agent_id="alice",
                    timestamp=reference_time - timedelta(days=10),
                    content="Semantic note: emergency supplies stay near the podium cabinet.",
                    memory_type="semantic",
                    importance=0.20,
                ),
            ]
        )

        store.apply_selective_forgetting(as_of=reference_time, retain_at_least=2)
        results = store.retrieve("Where is the projector cable?", k=2)

        assert [memory.id for memory in results] == ["live-note", "semantic-policy"]
        assert all(memory.id != "stale-note" for memory in results)
    finally:
        store.close()
