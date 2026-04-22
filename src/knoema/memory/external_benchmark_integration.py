"""Synthetic local proxy suites inspired by named memory benchmark families."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from knoema.memory.retrieval_benchmark import (
    MemoryBenchmarkCase,
    MemoryBenchmarkQuery,
    run_memory_benchmark_cases,
)
from knoema.types import Memory


@dataclass(frozen=True, slots=True)
class ExternalMemoryBenchmarkRow:
    benchmark_id: str
    benchmark_label: str
    score: float
    target: float
    passed: bool
    evaluation_mode: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ExternalMemoryBenchmarkIntegrationResult:
    rows: tuple[ExternalMemoryBenchmarkRow, ...]

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_json_dict() for row in self.rows]
        return payload


def run_external_memory_benchmark_integration() -> ExternalMemoryBenchmarkIntegrationResult:
    rows = []
    for benchmark_id, label, target, cases in (
        (
            "locomo",
            "LoCoMo-inspired long-term conversational retention proxy",
            0.8,
            _locomo_cases(),
        ),
        (
            "memoryagentbench",
            "MemoryAgentBench-inspired EventQA + FactConsolidation proxy",
            0.8,
            _memoryagentbench_cases(),
        ),
        (
            "memoryarena",
            "MemoryArena-inspired decision-relevant memory proxy",
            0.6,
            _memoryarena_cases(),
        ),
    ):
        result = run_memory_benchmark_cases(cases, target_recall_at_5=target)
        rows.append(
            ExternalMemoryBenchmarkRow(
                benchmark_id=benchmark_id,
                benchmark_label=label,
                score=result.average_recall_at_5,
                target=target,
                passed=result.passed,
                evaluation_mode="synthetic local proxy over SQLite+FAISS retrieval",
            )
        )
    return ExternalMemoryBenchmarkIntegrationResult(rows=tuple(rows))


def write_external_memory_benchmark_summary(output_path: Path) -> ExternalMemoryBenchmarkIntegrationResult:
    result = run_external_memory_benchmark_integration()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _locomo_cases() -> tuple[MemoryBenchmarkCase, ...]:
    base = datetime(2026, 4, 19, 8, 0, tzinfo=UTC)
    return (
        MemoryBenchmarkCase(
            agent_id="locomo_agent",
            memories=(
                _memory("locomo_agent", "locomo-01", base, "During breakfast Mina promised to bring the annotated field notebook to Professor Han."),
                _memory("locomo_agent", "locomo-02", base + timedelta(hours=2), "At lunch Mina repeated that the field notebook stays in the navy canvas tote."),
                _memory("locomo_agent", "locomo-03", base + timedelta(hours=4), "In the evening Mina confirmed the meeting room changed to Seminar Room 3."),
            ),
            queries=(
                MemoryBenchmarkQuery("locomo-q1", "Where does Mina keep the field notebook?", ("locomo-02",)),
                MemoryBenchmarkQuery("locomo-q2", "Which room did the meeting move to?", ("locomo-03",)),
            ),
        ),
    )


def _memoryagentbench_cases() -> tuple[MemoryBenchmarkCase, ...]:
    base = datetime(2026, 4, 19, 9, 0, tzinfo=UTC)
    return (
        MemoryBenchmarkCase(
            agent_id="mab_eventqa",
            memories=(
                _memory("mab_eventqa", "mab-01", base, "Tick 3 outage started in the west hall after the circuit alarm tripped."),
                _memory("mab_eventqa", "mab-02", base + timedelta(minutes=5), "Tick 5 maintenance crew restored power in the west hall."),
                _memory("mab_eventqa", "mab-03", base + timedelta(minutes=10), "Event consolidation note: outage lasted two ticks and affected the projector."),
            ),
            queries=(
                MemoryBenchmarkQuery("mab-q1", "Which hall lost power after the circuit alarm?", ("mab-01",)),
                MemoryBenchmarkQuery("mab-q2", "How long did the outage last and what was affected?", ("mab-03",)),
            ),
        ),
    )


def _memoryarena_cases() -> tuple[MemoryBenchmarkCase, ...]:
    base = datetime(2026, 4, 19, 10, 0, tzinfo=UTC)
    return (
        MemoryBenchmarkCase(
            agent_id="memoryarena_agent",
            memories=(
                _memory("memoryarena_agent", "arena-01", base, "Decision memo: choose the north gate route because it avoids the flooded bridge."),
                _memory("memoryarena_agent", "arena-02", base + timedelta(minutes=5), "Inventory note: the medkit is in locker B-14 next to the flashlight."),
                _memory("memoryarena_agent", "arena-03", base + timedelta(minutes=10), "Reminder: the flooded bridge remains unsafe after dusk."),
            ),
            queries=(
                MemoryBenchmarkQuery(
                    "arena-q1",
                    "Which route should the team choose to avoid the flooded bridge?",
                    ("arena-01",),
                ),
                MemoryBenchmarkQuery(
                    "arena-q2",
                    "Where is the medkit stored for the response plan?",
                    ("arena-02",),
                ),
            ),
        ),
    )


def _memory(agent_id: str, memory_id: str, timestamp: datetime, content: str) -> Memory:
    return Memory(
        id=memory_id,
        agent_id=agent_id,
        timestamp=timestamp,
        content=content,
        memory_type="episodic",
        importance=0.85,
    )


__all__ = [
    "ExternalMemoryBenchmarkIntegrationResult",
    "ExternalMemoryBenchmarkRow",
    "run_external_memory_benchmark_integration",
    "write_external_memory_benchmark_summary",
]
