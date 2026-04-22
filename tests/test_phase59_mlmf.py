from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from knoema.memory.multi_layer import (
    MEMORY_LAYERS,
    MultiLayerMemoryRecord,
    MultiLayerMemoryStore,
    SharedDecayScheduler,
    run_mlmf_retention_benchmark,
)


def test_phase59_store_supports_four_layers_with_shared_scheduler() -> None:
    scheduler = SharedDecayScheduler()
    store = MultiLayerMemoryStore(decay_scheduler=scheduler)
    base = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    store.add_many(
        [
            MultiLayerMemoryRecord(
                memory_id="episodic-1",
                agent_id="agent_a",
                layer="episodic",
                timestamp=base,
                importance=0.6,
                content="Mira stored the brass key in drawer seven.",
            ),
            MultiLayerMemoryRecord(
                memory_id="semantic-1",
                agent_id="agent_a",
                layer="semantic",
                timestamp=base + timedelta(days=1),
                importance=0.8,
                content="Reference note: the brass key is in drawer seven.",
            ),
            MultiLayerMemoryRecord(
                memory_id="procedural-1",
                agent_id="agent_a",
                layer="procedural",
                timestamp=base + timedelta(days=2),
                importance=0.9,
                content="Procedure step two: take the radio from the east cabinet.",
            ),
            MultiLayerMemoryRecord(
                memory_id="emotional-1",
                agent_id="agent_a",
                layer="emotional",
                timestamp=base + timedelta(days=3),
                importance=0.85,
                content="The south bridge felt unsafe after dusk.",
            ),
        ]
    )

    results = store.retrieve(
        "Where is the brass key stored?",
        agent_id="agent_a",
        as_of=base + timedelta(days=10),
        top_k=4,
    )

    assert store.shared_decay_scheduler is scheduler
    assert {result.record.layer for result in results} == set(MEMORY_LAYERS)
    assert results[0].record.memory_id == "semantic-1"
    assert {result.record.agent_id for result in results} == {"agent_a"}


def test_phase59_shared_decay_scheduler_preserves_procedural_memory_longer_than_episodic() -> None:
    scheduler = SharedDecayScheduler()
    timestamp = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    as_of = timestamp + timedelta(days=10)

    procedural = scheduler.retention_score("procedural", timestamp, as_of, importance=0.8)
    episodic = scheduler.retention_score("episodic", timestamp, as_of, importance=0.8)

    assert procedural > episodic


def test_phase59_mlmf_retention_benchmark_beats_published_baseline() -> None:
    result = run_mlmf_retention_benchmark()

    assert result.layers_covered == MEMORY_LAYERS
    assert result.passed is True
    assert result.measured_retention > result.published_baseline
    assert len(result.per_query) == 8
    assert sum(1 for row in result.per_query if row.hit) >= 7
    assert {row.retrieved_layer for row in result.per_query} == set(MEMORY_LAYERS)
    assert all(
        row.retrieved_memory_id.split("-", 1)[0]
        == row.relevant_memory_id.split("-", 1)[0]
        for row in result.per_query
    )


def test_phase59_mlmf_script_writes_summary() -> None:
    subprocess.run(
        [sys.executable, "experiments/mlmf_retention_benchmark/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    summary = json.loads(
        Path("experiments/mlmf_retention_benchmark/results/summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert tuple(summary["layers_covered"]) == MEMORY_LAYERS
    assert summary["measured_retention"] > summary["published_baseline"]
    assert summary["passed"] is True
