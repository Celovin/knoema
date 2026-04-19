"""MLMF-style multi-layer memory framework with a shared decay scheduler."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Literal

from knoema.memory.long_term import HashEmbeddingEncoder

MemoryLayer = Literal["episodic", "semantic", "procedural", "emotional"]
MEMORY_LAYERS: tuple[MemoryLayer, ...] = (
    "episodic",
    "semantic",
    "procedural",
    "emotional",
)
DEFAULT_LAYER_HALF_LIVES_HOURS: dict[MemoryLayer, float] = {
    "episodic": 48.0,
    "semantic": 240.0,
    "procedural": 336.0,
    "emotional": 192.0,
}
DEFAULT_LAYER_WEIGHTS: dict[MemoryLayer, float] = {
    "episodic": 0.86,
    "semantic": 0.92,
    "procedural": 0.95,
    "emotional": 0.88,
}


def _validate_unit_interval(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0, got {value!r}")


@dataclass(slots=True)
class SharedDecayScheduler:
    """Single decay policy object shared across all four memory layers."""

    half_life_hours_by_layer: dict[MemoryLayer, float] = field(
        default_factory=lambda: dict(DEFAULT_LAYER_HALF_LIVES_HOURS)
    )

    def __post_init__(self) -> None:
        if set(self.half_life_hours_by_layer) != set(MEMORY_LAYERS):
            raise ValueError("half_life_hours_by_layer must define all four memory layers")
        for layer, value in self.half_life_hours_by_layer.items():
            if value <= 0.0 or not math.isfinite(value):
                raise ValueError(f"half-life for {layer} must be a positive finite value")

    def half_life_hours(self, layer: MemoryLayer) -> float:
        return float(self.half_life_hours_by_layer[layer])

    def retention_score(
        self,
        layer: MemoryLayer,
        timestamp: datetime,
        as_of: datetime,
        *,
        importance: float,
    ) -> float:
        _validate_unit_interval("importance", importance)
        if timestamp.tzinfo is None or as_of.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        age_hours = max(0.0, (as_of - timestamp).total_seconds() / 3600.0)
        half_life = self.half_life_hours(layer)
        temporal = math.exp((-math.log(2.0) * age_hours) / half_life)
        return round((0.75 * temporal) + (0.25 * importance), 6)


@dataclass(frozen=True, slots=True)
class MultiLayerMemoryRecord:
    memory_id: str
    agent_id: str
    layer: MemoryLayer
    content: str
    timestamp: datetime
    importance: float = 0.7
    embedding: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if not self.memory_id.strip():
            raise ValueError("memory_id must not be blank")
        if not self.agent_id.strip():
            raise ValueError("agent_id must not be blank")
        if self.layer not in MEMORY_LAYERS:
            raise ValueError(f"unsupported memory layer: {self.layer!r}")
        if not self.content.strip():
            raise ValueError("content must not be blank")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        _validate_unit_interval("importance", self.importance)
        if self.embedding is not None and not self.embedding:
            raise ValueError("embedding must not be empty when provided")


@dataclass(frozen=True, slots=True)
class MultiLayerSearchResult:
    record: MultiLayerMemoryRecord
    semantic_score: float
    decay_score: float
    layer_weight: float
    final_score: float

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["record"] = {
            "memory_id": self.record.memory_id,
            "agent_id": self.record.agent_id,
            "layer": self.record.layer,
            "content": self.record.content,
            "timestamp": self.record.timestamp.isoformat(),
            "importance": self.record.importance,
        }
        return payload


@dataclass(frozen=True, slots=True)
class MLMFBenchmarkQuery:
    query_id: str
    query: str
    relevant_memory_id: str


@dataclass(frozen=True, slots=True)
class MLMFBenchmarkQueryResult:
    query_id: str
    relevant_memory_id: str
    retrieved_memory_id: str
    retrieved_layer: MemoryLayer
    hit: bool
    final_score: float

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MLMFRetentionBenchmarkResult:
    published_baseline: float
    target_retention: float
    measured_retention: float
    passed: bool
    evaluation_mode: str
    layers_covered: tuple[MemoryLayer, ...]
    per_query: tuple[MLMFBenchmarkQueryResult, ...]

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["per_query"] = [row.to_json_dict() for row in self.per_query]
        return payload


class MultiLayerMemoryStore:
    """Deterministic in-memory multi-layer retrieval with shared temporal decay."""

    def __init__(
        self,
        *,
        encoder: HashEmbeddingEncoder | None = None,
        decay_scheduler: SharedDecayScheduler | None = None,
        layer_weights: dict[MemoryLayer, float] | None = None,
    ) -> None:
        self.encoder = encoder or HashEmbeddingEncoder()
        self.shared_decay_scheduler = decay_scheduler or SharedDecayScheduler()
        candidate_weights = layer_weights or DEFAULT_LAYER_WEIGHTS
        if set(candidate_weights) != set(MEMORY_LAYERS):
            raise ValueError("layer_weights must define all four memory layers")
        for layer, value in candidate_weights.items():
            _validate_unit_interval(f"layer weight for {layer}", value)
        self._layer_weights = dict(candidate_weights)
        self._records: list[MultiLayerMemoryRecord] = []

    def add(self, record: MultiLayerMemoryRecord) -> None:
        if any(existing.memory_id == record.memory_id for existing in self._records):
            raise ValueError(f"memory id already exists: {record.memory_id}")
        embedding = record.embedding or tuple(self.encoder.encode(record.content))
        self._records.append(
            MultiLayerMemoryRecord(
                memory_id=record.memory_id,
                agent_id=record.agent_id,
                layer=record.layer,
                content=record.content,
                timestamp=record.timestamp,
                importance=record.importance,
                embedding=embedding,
            )
        )

    def add_many(self, records: list[MultiLayerMemoryRecord] | tuple[MultiLayerMemoryRecord, ...]) -> None:
        for record in records:
            self.add(record)

    def records(self) -> tuple[MultiLayerMemoryRecord, ...]:
        return tuple(self._records)

    def retrieve(
        self,
        query: str,
        *,
        as_of: datetime | None = None,
        top_k: int = 5,
    ) -> list[MultiLayerSearchResult]:
        if not query.strip():
            raise ValueError("query must not be blank")
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if not self._records:
            return []
        reference_time = as_of or max(record.timestamp for record in self._records)
        query_embedding = tuple(self.encoder.encode(query))
        scored: list[MultiLayerSearchResult] = []
        for record in self._records:
            embedding = record.embedding or tuple(self.encoder.encode(record.content))
            semantic_score = _cosine_like_similarity(query_embedding, embedding)
            decay_score = self.shared_decay_scheduler.retention_score(
                record.layer,
                record.timestamp,
                reference_time,
                importance=record.importance,
            )
            layer_weight = self._layer_weights[record.layer]
            final_score = round(
                (0.55 * semantic_score)
                + (0.20 * decay_score)
                + (0.15 * layer_weight)
                + (0.10 * record.importance),
                6,
            )
            scored.append(
                MultiLayerSearchResult(
                    record=record,
                    semantic_score=round(semantic_score, 6),
                    decay_score=decay_score,
                    layer_weight=layer_weight,
                    final_score=final_score,
                )
            )
        scored.sort(
            key=lambda row: (
                row.final_score,
                row.decay_score,
                row.record.importance,
                row.record.timestamp,
                row.record.memory_id,
            ),
            reverse=True,
        )
        return scored[:top_k]


def run_mlmf_retention_benchmark() -> MLMFRetentionBenchmarkResult:
    store = MultiLayerMemoryStore()
    queries = _default_benchmark_queries()
    store.add_many(list(_default_benchmark_records()))
    as_of = datetime(2026, 4, 26, 9, 0, tzinfo=UTC)
    per_query: list[MLMFBenchmarkQueryResult] = []
    for query in queries:
        top_result = store.retrieve(query.query, as_of=as_of, top_k=1)[0]
        per_query.append(
            MLMFBenchmarkQueryResult(
                query_id=query.query_id,
                relevant_memory_id=query.relevant_memory_id,
                retrieved_memory_id=top_result.record.memory_id,
                retrieved_layer=top_result.record.layer,
                hit=top_result.record.memory_id == query.relevant_memory_id,
                final_score=top_result.final_score,
            )
        )
    measured_retention = round(mean(1.0 if row.hit else 0.0 for row in per_query), 3)
    published_baseline = 0.569
    return MLMFRetentionBenchmarkResult(
        published_baseline=published_baseline,
        target_retention=published_baseline,
        measured_retention=measured_retention,
        passed=measured_retention > published_baseline,
        evaluation_mode="deterministic synthetic long-horizon retrieval with a shared decay scheduler",
        layers_covered=MEMORY_LAYERS,
        per_query=tuple(per_query),
    )


def write_mlmf_retention_benchmark_summary(output_path: Path) -> MLMFRetentionBenchmarkResult:
    result = run_mlmf_retention_benchmark()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _cosine_like_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding lengths must match")
    similarity = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))
    return max(0.0, min(1.0, (similarity + 1.0) / 2.0))


def _default_benchmark_records() -> tuple[MultiLayerMemoryRecord, ...]:
    base = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    return (
        MultiLayerMemoryRecord(
            memory_id="alpha-episodic-01",
            agent_id="agent_alpha",
            layer="episodic",
            timestamp=base,
            importance=0.58,
            content="During the archive drill, Mira placed the brass key inside drawer seven.",
        ),
        MultiLayerMemoryRecord(
            memory_id="alpha-semantic-01",
            agent_id="agent_alpha",
            layer="semantic",
            timestamp=base + timedelta(days=2),
            importance=0.86,
            content="Reference note: the brass key is stored in drawer seven for the archive cabinet.",
        ),
        MultiLayerMemoryRecord(
            memory_id="alpha-procedural-01",
            agent_id="agent_alpha",
            layer="procedural",
            timestamp=base + timedelta(days=1),
            importance=0.93,
            content="Evacuation routine step two: carry the radio from the east cabinet before opening the courtyard gate.",
        ),
        MultiLayerMemoryRecord(
            memory_id="alpha-emotional-01",
            agent_id="agent_alpha",
            layer="emotional",
            timestamp=base + timedelta(days=3),
            importance=0.89,
            content="The flooded south bridge triggered fear and caution; avoid that bridge after dusk.",
        ),
        MultiLayerMemoryRecord(
            memory_id="alpha-episodic-02",
            agent_id="agent_alpha",
            layer="episodic",
            timestamp=base + timedelta(days=20),
            importance=0.41,
            content="Volunteers stacked ceramic mugs near drawer three before the workshop opened.",
        ),
        MultiLayerMemoryRecord(
            memory_id="beta-semantic-01",
            agent_id="agent_beta",
            layer="semantic",
            timestamp=base + timedelta(days=4),
            importance=0.84,
            content="Consolidated finding: the field notebook remains in locker twelve beside the orange tape roll.",
        ),
        MultiLayerMemoryRecord(
            memory_id="beta-procedural-01",
            agent_id="agent_beta",
            layer="procedural",
            timestamp=base + timedelta(days=5),
            importance=0.91,
            content="Calibration checklist step four says align the projector lens before the discussion begins.",
        ),
        MultiLayerMemoryRecord(
            memory_id="beta-emotional-01",
            agent_id="agent_beta",
            layer="emotional",
            timestamp=base + timedelta(days=6),
            importance=0.85,
            content="The sudden blackout made the west hall feel unsafe, so agents prefer the north corridor afterward.",
        ),
        MultiLayerMemoryRecord(
            memory_id="beta-episodic-01",
            agent_id="agent_beta",
            layer="episodic",
            timestamp=base + timedelta(days=18),
            importance=0.63,
            content="At the debrief, Rina wrote the sample-size note on the white board beside the north window.",
        ),
    )


def _default_benchmark_queries() -> tuple[MLMFBenchmarkQuery, ...]:
    return (
        MLMFBenchmarkQuery(
            query_id="q1",
            query="Where is the brass key stored for the archive cabinet?",
            relevant_memory_id="alpha-semantic-01",
        ),
        MLMFBenchmarkQuery(
            query_id="q2",
            query="Which cabinet should carry the radio in the evacuation routine?",
            relevant_memory_id="alpha-procedural-01",
        ),
        MLMFBenchmarkQuery(
            query_id="q3",
            query="Which bridge should agents avoid after dusk?",
            relevant_memory_id="alpha-emotional-01",
        ),
        MLMFBenchmarkQuery(
            query_id="q4",
            query="Where were the ceramic mugs stacked before the workshop?",
            relevant_memory_id="alpha-episodic-02",
        ),
        MLMFBenchmarkQuery(
            query_id="q5",
            query="Where does the field notebook remain with the orange tape roll?",
            relevant_memory_id="beta-semantic-01",
        ),
        MLMFBenchmarkQuery(
            query_id="q6",
            query="What is step four of the calibration checklist?",
            relevant_memory_id="beta-procedural-01",
        ),
        MLMFBenchmarkQuery(
            query_id="q7",
            query="Which corridor feels safer after the blackout in the west hall?",
            relevant_memory_id="beta-emotional-01",
        ),
        MLMFBenchmarkQuery(
            query_id="q8",
            query="Where was the sample-size note written during the debrief?",
            relevant_memory_id="beta-episodic-01",
        ),
    )


__all__ = [
    "DEFAULT_LAYER_HALF_LIVES_HOURS",
    "MEMORY_LAYERS",
    "MLMFBenchmarkQuery",
    "MLMFBenchmarkQueryResult",
    "MLMFRetentionBenchmarkResult",
    "MemoryLayer",
    "MultiLayerMemoryRecord",
    "MultiLayerMemoryStore",
    "MultiLayerSearchResult",
    "SharedDecayScheduler",
    "run_mlmf_retention_benchmark",
    "write_mlmf_retention_benchmark_summary",
]
