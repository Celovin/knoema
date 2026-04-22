"""Phase 2 tests for personas and memory subsystems."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from luvoire import (
    HashEmbeddingEncoder,
    Memory,
    MemorySearchResult,
    MemorySummarizer,
    Persona,
    Personality,
    RetrievalWeights,
    ShortTermMemoryBuffer,
    SQLiteFaissMemoryStore,
)


class _StaticTwoDimensionalEncoder:
    dimension = 2

    def encode(self, text: str) -> list[float]:
        return [1.0, 0.0]


def _memory_at(index: int, content: str, *, agent_id: str = "alice") -> Memory:
    return Memory(
        id=f"mem-{index:03d}",
        agent_id=agent_id,
        timestamp=datetime(2026, 4, 18, 9, 0) + timedelta(minutes=index),
        content=content,
        memory_type="episodic",
        importance=0.5 + ((index % 5) * 0.1),
    )


def test_persona_to_system_prompt_includes_core_fields() -> None:
    persona = Persona(
        agent_id="alice",
        name="Alice Kim",
        age=17,
        background="Introverted literature student in a dormitory.",
        personality=Personality(0.8, 0.6, 0.2, 0.7, 0.4),
        values=["honesty", "calm"],
        goals=["finish a novel", "avoid conflict"],
    )

    prompt = persona.to_system_prompt()

    assert "Alice Kim" in prompt
    assert "Introverted literature student" in prompt
    assert "finish a novel" in prompt


def test_persona_rejects_blank_values() -> None:
    with pytest.raises(ValueError, match="values\\[0\\] must not be blank"):
        Persona(
            agent_id="alice",
            name="Alice Kim",
            age=17,
            background="Dormitory student",
            personality=Personality(0.8, 0.6, 0.2, 0.7, 0.4),
            values=[" "],
            goals=["study"],
        )


def test_short_term_buffer_keeps_fifo_capacity() -> None:
    buffer = ShortTermMemoryBuffer(capacity=3)
    buffer.extend(_memory_at(index, f"event {index}") for index in range(5))

    assert [memory.id for memory in buffer.recent()] == ["mem-002", "mem-003", "mem-004"]


def test_short_term_buffer_recent_limit_is_applied() -> None:
    buffer = ShortTermMemoryBuffer(capacity=5)
    buffer.extend(_memory_at(index, f"event {index}") for index in range(5))

    assert [memory.id for memory in buffer.recent(2)] == ["mem-003", "mem-004"]


def test_short_term_buffer_rejects_invalid_capacity() -> None:
    with pytest.raises(ValueError, match="capacity must be positive"):
        ShortTermMemoryBuffer(capacity=0)


def test_hash_embedding_encoder_is_deterministic() -> None:
    encoder = HashEmbeddingEncoder(dimension=32)

    assert encoder.encode("shared breakfast") == encoder.encode("shared breakfast")


def test_long_term_store_adds_and_retrieves_relevant_memories(tmp_path: Path) -> None:
    store = SQLiteFaissMemoryStore(tmp_path / "memories.sqlite3")
    try:
        chemistry = _memory_at(1, "Alice studied chemistry in the library.")
        violin = _memory_at(2, "Bob practiced violin before dinner.", agent_id="bob")
        store.add(chemistry)
        store.add(violin)

        results = store.retrieve("chemistry study", k=1)

        assert results[0].id == chemistry.id
    finally:
        store.close()


def test_long_term_store_applies_recency_bias(tmp_path: Path) -> None:
    store = SQLiteFaissMemoryStore(tmp_path / "recency.sqlite3")
    try:
        older = Memory(
            id="older",
            agent_id="alice",
            timestamp=datetime(2026, 4, 10, 9, 0),
            content="Alice prepared chemistry notes.",
            memory_type="episodic",
            importance=0.6,
        )
        newer = Memory(
            id="newer",
            agent_id="alice",
            timestamp=datetime(2026, 4, 18, 9, 0),
            content="Alice prepared chemistry notes.",
            memory_type="episodic",
            importance=0.6,
        )
        store.add(older)
        store.add(newer)

        results = store.retrieve("chemistry notes", k=2, recency_bias=0.9)

        assert results[0].id == "newer"
    finally:
        store.close()


def test_long_term_store_add_many_batches_records_and_rejects_duplicates(
    tmp_path: Path,
) -> None:
    store = SQLiteFaissMemoryStore(tmp_path / "batch.sqlite3")
    try:
        memories = [_memory_at(index, f"Batch event {index} about study.") for index in range(3)]

        store.add_many(memories)

        assert len(store) == 3
        assert len(store.retrieve("study", k=2)) == 2

        with pytest.raises(ValueError, match="memory id already exists: mem-001"):
            store.add_many([_memory_at(1, "Duplicate existing memory.")])
        with pytest.raises(ValueError, match="memory id already exists: mem-010"):
            store.add_many(
                [
                    _memory_at(10, "Duplicate within one batch."),
                    _memory_at(10, "Duplicate within one batch again."),
                ]
            )
    finally:
        store.close()


def test_long_term_store_hybrid_reranking_returns_scored_results(tmp_path: Path) -> None:
    store = SQLiteFaissMemoryStore(
        tmp_path / "hybrid.sqlite3",
        encoder=_StaticTwoDimensionalEncoder(),
    )
    try:
        older_semantic_match = Memory(
            id="older",
            agent_id="alice",
            timestamp=datetime(2026, 4, 8, 9, 0),
            content="Alice prepared chemistry notes.",
            memory_type="episodic",
            importance=0.2,
            embedding=[1.0, 0.0],
        )
        newer_partial_match = Memory(
            id="newer",
            agent_id="alice",
            timestamp=datetime(2026, 4, 18, 9, 0),
            content="Alice discussed the study schedule this morning.",
            memory_type="episodic",
            importance=0.2,
            embedding=[0.8, 0.6],
        )
        store.add_many([older_semantic_match, newer_partial_match])

        results = store.retrieve_with_scores(
            "chemistry notes",
            k=2,
            weights=RetrievalWeights(semantic=0.35, temporal=0.60, importance=0.05),
            as_of=newer_partial_match.timestamp,
        )

        assert all(isinstance(result, MemorySearchResult) for result in results)
        assert [result.memory.id for result in results] == ["newer", "older"]
        assert results[1].semantic_score > results[0].semantic_score
        assert results[0].temporal_score > results[1].temporal_score
        assert results[0].final_score > results[1].final_score
    finally:
        store.close()


def test_retrieval_weights_reject_invalid_values() -> None:
    with pytest.raises(ValueError, match="semantic weight"):
        RetrievalWeights(semantic=-0.1)
    with pytest.raises(ValueError, match="at least one retrieval weight"):
        RetrievalWeights(semantic=0.0, temporal=0.0, importance=0.0)


def test_long_term_store_persists_records_between_instances(tmp_path: Path) -> None:
    database_path = tmp_path / "persistent.sqlite3"
    first_store = SQLiteFaissMemoryStore(database_path)
    try:
        first_store.add(_memory_at(1, "Alice cooked ramen after study hall."))
    finally:
        first_store.close()

    second_store = SQLiteFaissMemoryStore(database_path)
    try:
        results = second_store.retrieve("ramen", k=1)

        assert results[0].content == "Alice cooked ramen after study hall."
    finally:
        second_store.close()


def test_long_term_store_handles_one_hundred_events_with_small_runtime_budget(
    tmp_path: Path,
) -> None:
    store = SQLiteFaissMemoryStore(tmp_path / "performance.sqlite3")
    try:
        start = time.perf_counter()
        for index in range(100):
            store.add(_memory_at(index, f"Event {index} about shared dorm routines and study habits."))
        results = store.retrieve("study habits", k=5)
        elapsed = time.perf_counter() - start

        assert len(results) == 5
        assert elapsed < 3.0
    finally:
        store.close()


def test_memory_summarizer_compresses_fifty_events_to_three_to_five_semantic_memories() -> None:
    summarizer = MemorySummarizer()
    events = [_memory_at(index, f"Episode {index} in the dormitory simulation.") for index in range(50)]

    summaries = summarizer.summarize(events)

    assert 3 <= len(summaries) <= 5
    assert all(summary.memory_type == "semantic" for summary in summaries)


def test_memory_summarizer_keeps_agent_context() -> None:
    summarizer = MemorySummarizer()
    events = [_memory_at(index, f"Interaction {index} with roommate.") for index in range(15)]

    summaries = summarizer.summarize(events)

    assert all(summary.agent_id == "alice" for summary in summaries)
    assert all(summary.content for summary in summaries)
