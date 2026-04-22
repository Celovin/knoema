"""Deterministic retrieval benchmark for per-agent long-term memory stores."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory

from luvoire.memory.long_term import SQLiteFaissMemoryStore
from luvoire.types import Memory


@dataclass(frozen=True, slots=True)
class MemoryBenchmarkQuery:
    query_id: str
    query: str
    relevant_memory_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MemoryBenchmarkCase:
    agent_id: str
    memories: tuple[Memory, ...]
    queries: tuple[MemoryBenchmarkQuery, ...]


@dataclass(frozen=True, slots=True)
class QueryRecallResult:
    query_id: str
    recall_at_k: float
    retrieved_memory_ids: tuple[str, ...]
    relevant_memory_ids: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AgentRecallBenchmarkResult:
    agent_id: str
    recall_at_5: float
    queries: tuple[QueryRecallResult, ...]

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["queries"] = [query.to_json_dict() for query in self.queries]
        return payload


@dataclass(frozen=True, slots=True)
class MemoryRetrievalBenchmarkResult:
    target_recall_at_5: float
    average_recall_at_5: float
    passed: bool
    per_agent: tuple[AgentRecallBenchmarkResult, ...]

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["per_agent"] = [agent.to_json_dict() for agent in self.per_agent]
        return payload


def run_memory_retrieval_benchmark(
    *,
    k: int = 5,
    target_recall_at_5: float = 0.85,
) -> MemoryRetrievalBenchmarkResult:
    return run_memory_benchmark_cases(
        _default_benchmark_cases(),
        k=k,
        target_recall_at_5=target_recall_at_5,
    )


def run_memory_benchmark_cases(
    cases: tuple[MemoryBenchmarkCase, ...],
    *,
    k: int = 5,
    target_recall_at_5: float = 0.85,
) -> MemoryRetrievalBenchmarkResult:
    if k < 1:
        raise ValueError("k must be positive")
    if not 0.0 <= target_recall_at_5 <= 1.0:
        raise ValueError("target_recall_at_5 must be between 0.0 and 1.0")

    with TemporaryDirectory(prefix="luvoire-memory-benchmark-") as temp_dir:
        temp_root = Path(temp_dir)
        per_agent_results = tuple(
            _run_case(case, root=temp_root, k=k)
            for case in cases
        )
    average_recall = round(mean(result.recall_at_5 for result in per_agent_results), 3)
    return MemoryRetrievalBenchmarkResult(
        target_recall_at_5=target_recall_at_5,
        average_recall_at_5=average_recall,
        passed=average_recall >= target_recall_at_5,
        per_agent=per_agent_results,
    )


def write_memory_retrieval_benchmark_summary(output_path: Path) -> MemoryRetrievalBenchmarkResult:
    result = run_memory_retrieval_benchmark()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _run_case(
    case: MemoryBenchmarkCase,
    *,
    root: Path,
    k: int,
) -> AgentRecallBenchmarkResult:
    store = SQLiteFaissMemoryStore(root / f"{case.agent_id}.sqlite3")
    try:
        store.add_many(case.memories)
        query_results: list[QueryRecallResult] = []
        for query in case.queries:
            retrieved = store.retrieve(query.query, k=k)
            retrieved_ids = tuple(memory.id for memory in retrieved)
            hits = len(set(retrieved_ids).intersection(query.relevant_memory_ids))
            recall_at_k = round(hits / len(query.relevant_memory_ids), 3)
            query_results.append(
                QueryRecallResult(
                    query_id=query.query_id,
                    recall_at_k=recall_at_k,
                    retrieved_memory_ids=retrieved_ids,
                    relevant_memory_ids=query.relevant_memory_ids,
                )
            )
        return AgentRecallBenchmarkResult(
            agent_id=case.agent_id,
            recall_at_5=round(mean(query.recall_at_k for query in query_results), 3),
            queries=tuple(query_results),
        )
    finally:
        store.close()


def _default_benchmark_cases() -> tuple[MemoryBenchmarkCase, ...]:
    base_time = datetime(2026, 4, 19, 9, 0, tzinfo=UTC)
    return (
        MemoryBenchmarkCase(
            agent_id="agent_alpha",
            memories=(
                _memory("agent_alpha", "alpha-01", base_time, "Promised to bring the blue chemistry notebook to the lab review."),
                _memory("agent_alpha", "alpha-02", base_time + timedelta(minutes=5), "Discussed dorm quiet-hours policy with the resident assistant."),
                _memory("agent_alpha", "alpha-03", base_time + timedelta(minutes=10), "Scheduled Friday statistics office hours about mixed-effects homework."),
                _memory("agent_alpha", "alpha-04", base_time + timedelta(minutes=15), "Stored the pantry spare key in the green ceramic mug above the sink."),
                _memory("agent_alpha", "alpha-05", base_time + timedelta(minutes=20), "Wrote an IRB reminder to keep all public-safety scenarios fictional and synthetic."),
                _memory("agent_alpha", "alpha-06", base_time + timedelta(minutes=25), "Promised the soccer captain a ride to the evening practice scrimmage."),
                _memory("agent_alpha", "alpha-07", base_time + timedelta(minutes=30), "Saved the latex export draft for the preregistration appendix."),
            ),
            queries=(
                MemoryBenchmarkQuery("alpha-q1", "Where is the pantry spare key stored?", ("alpha-04",)),
                MemoryBenchmarkQuery("alpha-q2", "What notebook was promised for the lab review?", ("alpha-01",)),
                MemoryBenchmarkQuery("alpha-q3", "Which office hours were scheduled for statistics homework?", ("alpha-03",)),
                MemoryBenchmarkQuery("alpha-q4", "What reminder was written about fictional public-safety scenarios?", ("alpha-05",)),
                MemoryBenchmarkQuery("alpha-q5", "What export draft was saved for the preregistration appendix?", ("alpha-07",)),
            ),
        ),
        MemoryBenchmarkCase(
            agent_id="agent_beta",
            memories=(
                _memory("agent_beta", "beta-01", base_time, "Recorded that the community garden hose hangs behind the west shed latch."),
                _memory("agent_beta", "beta-02", base_time + timedelta(minutes=5), "Promised to email the memory benchmark summary before noon."),
                _memory("agent_beta", "beta-03", base_time + timedelta(minutes=10), "Noted that the Sally-Anne rehearsal uses the red locker and silver drawer."),
                _memory("agent_beta", "beta-04", base_time + timedelta(minutes=15), "Reserved the north study booth for the HEXACO questionnaire pilot."),
                _memory("agent_beta", "beta-05", base_time + timedelta(minutes=20), "Marked the ACE baseline target as 200 ms median cloud latency."),
                _memory("agent_beta", "beta-06", base_time + timedelta(minutes=25), "Tracked that the village quest reward is a copper token and bread loaf."),
                _memory("agent_beta", "beta-07", base_time + timedelta(minutes=30), "Saved the OSF simulation template under the reproducibility folder."),
            ),
            queries=(
                MemoryBenchmarkQuery("beta-q1", "Where does the community garden hose hang?", ("beta-01",)),
                MemoryBenchmarkQuery("beta-q2", "What locker and drawer are used in the Sally-Anne rehearsal?", ("beta-03",)),
                MemoryBenchmarkQuery("beta-q3", "Which booth is reserved for the HEXACO questionnaire pilot?", ("beta-04",)),
                MemoryBenchmarkQuery("beta-q4", "What latency target was marked for the ACE baseline?", ("beta-05",)),
                MemoryBenchmarkQuery("beta-q5", "Where was the OSF simulation template saved?", ("beta-07",)),
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
        importance=0.8,
    )


__all__ = [
    "AgentRecallBenchmarkResult",
    "MemoryBenchmarkCase",
    "MemoryBenchmarkQuery",
    "MemoryRetrievalBenchmarkResult",
    "QueryRecallResult",
    "run_memory_benchmark_cases",
    "run_memory_retrieval_benchmark",
    "write_memory_retrieval_benchmark_summary",
]
