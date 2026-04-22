"""Long-term memory store backed by SQLite and FAISS."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

import faiss  # type: ignore[import-untyped]
import numpy as np

from knoema.types import Memory

_TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


class HashEmbeddingEncoder:
    """Small deterministic embedder for local development and tests."""

    def __init__(self, dimension: int = 64) -> None:
        if dimension < 1:
            raise ValueError(f"dimension must be positive, got {dimension!r}")
        self.dimension = dimension

    def encode(self, text: str) -> list[float]:
        tokens = _TOKEN_PATTERN.findall(text.lower())
        if not tokens:
            tokens = ["<empty>"]
        vector = np.zeros(self.dimension, dtype=np.float32)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            first_index = int.from_bytes(digest[0:4], "little") % self.dimension
            second_index = int.from_bytes(digest[4:8], "little") % self.dimension
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            vector[first_index] += sign
            vector[second_index] += sign * 0.5
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            vector[0] = 1.0
        else:
            vector /= norm
        return vector.tolist()


@dataclass(frozen=True, slots=True)
class RetrievalWeights:
    """Weights for semantic-temporal memory reranking."""

    semantic: float = 0.65
    temporal: float = 0.30
    importance: float = 0.05

    def __post_init__(self) -> None:
        values = {
            "semantic": self.semantic,
            "temporal": self.temporal,
            "importance": self.importance,
        }
        for name, value in values.items():
            if value < 0.0 or not math.isfinite(value):
                raise ValueError(f"{name} weight must be a non-negative finite value")
        if sum(values.values()) == 0.0:
            raise ValueError("at least one retrieval weight must be positive")

    def normalized(self) -> RetrievalWeights:
        total = self.semantic + self.temporal + self.importance
        return RetrievalWeights(
            semantic=self.semantic / total,
            temporal=self.temporal / total,
            importance=self.importance / total,
        )

    def score(
        self,
        *,
        semantic_score: float,
        temporal_score: float,
        importance_score: float,
    ) -> float:
        return (
            self.semantic * semantic_score
            + self.temporal * temporal_score
            + self.importance * importance_score
        )


@dataclass(frozen=True, slots=True)
class MemorySearchResult:
    """A retrieved memory with reranking diagnostics."""

    memory: Memory
    semantic_score: float
    temporal_score: float
    importance_score: float
    final_score: float


@dataclass(frozen=True, slots=True)
class SelectiveForgettingResult:
    """Summary of a selective forgetting pass."""

    dropped_ids: tuple[str, ...]
    retained_count: int

    @property
    def dropped_count(self) -> int:
        return len(self.dropped_ids)


class SQLiteFaissMemoryStore:
    """Persistent store that combines metadata in SQLite with vector search in FAISS."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        encoder: HashEmbeddingEncoder | None = None,
    ) -> None:
        self.encoder = encoder or HashEmbeddingEncoder()
        database = str(db_path)
        self._path = None if database == ":memory:" else Path(database)
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._configure_connection()
        self._index = faiss.IndexFlatIP(self.encoder.dimension)
        self._memory_ids: list[str] = []
        self._records: dict[str, Memory] = {}
        self._ensure_schema()
        self._load_existing()

    def _configure_connection(self) -> None:
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA temp_store = MEMORY")
        if self._path is not None:
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA synchronous = NORMAL")

    def _ensure_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                importance REAL NOT NULL,
                embedding_json TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def _load_existing(self) -> None:
        rows = self._connection.execute(
            """
            SELECT id, agent_id, timestamp, content, memory_type, importance, embedding_json
            FROM memories
            ORDER BY timestamp ASC, id ASC
            """
        ).fetchall()
        embeddings: list[list[float]] = []
        for row in rows:
            embedding = json.loads(row["embedding_json"])
            memory = Memory(
                id=row["id"],
                agent_id=row["agent_id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                content=row["content"],
                memory_type=row["memory_type"],
                importance=float(row["importance"]),
                embedding=list(embedding),
            )
            self._records[memory.id] = memory
            self._memory_ids.append(memory.id)
            embeddings.append(memory.embedding or self.encoder.encode(memory.content))
        if embeddings:
            self._index.add(np.asarray(embeddings, dtype=np.float32))

    def add(self, memory: Memory) -> None:
        if memory.id in self._records:
            raise ValueError(f"memory id already exists: {memory.id}")
        embedding = memory.embedding or self.encoder.encode(memory.content)
        stored_memory = replace(memory, embedding=embedding)
        self._connection.execute(
            """
            INSERT INTO memories (id, agent_id, timestamp, content, memory_type, importance, embedding_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stored_memory.id,
                stored_memory.agent_id,
                stored_memory.timestamp.isoformat(),
                stored_memory.content,
                stored_memory.memory_type,
                stored_memory.importance,
                json.dumps(stored_memory.embedding),
            ),
        )
        self._connection.commit()
        self._records[stored_memory.id] = stored_memory
        self._memory_ids.append(stored_memory.id)
        self._index.add(np.asarray([stored_memory.embedding], dtype=np.float32))

    def add_many(self, memories: Iterable[Memory]) -> None:
        pending: list[Memory] = []
        embeddings: list[list[float]] = []
        seen_ids: set[str] = set()
        for memory in memories:
            if memory.id in self._records or memory.id in seen_ids:
                raise ValueError(f"memory id already exists: {memory.id}")
            embedding = memory.embedding or self.encoder.encode(memory.content)
            stored_memory = replace(memory, embedding=embedding)
            pending.append(stored_memory)
            embeddings.append(embedding)
            seen_ids.add(memory.id)

        if not pending:
            return

        self._connection.executemany(
            """
            INSERT INTO memories (id, agent_id, timestamp, content, memory_type, importance, embedding_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    memory.id,
                    memory.agent_id,
                    memory.timestamp.isoformat(),
                    memory.content,
                    memory.memory_type,
                    memory.importance,
                    json.dumps(memory.embedding),
                )
                for memory in pending
            ],
        )
        self._connection.commit()
        for memory in pending:
            self._records[memory.id] = memory
            self._memory_ids.append(memory.id)
        self._index.add(np.asarray(embeddings, dtype=np.float32))

    def apply_selective_forgetting(
        self,
        *,
        as_of: datetime | None = None,
        temporal_half_life_hours: float = 72.0,
        importance_floor: float = 0.45,
        retention_threshold: float = 0.50,
        retain_at_least: int = 8,
        preserve_memory_types: tuple[str, ...] = ("semantic", "procedural"),
    ) -> SelectiveForgettingResult:
        if temporal_half_life_hours <= 0.0 or not math.isfinite(temporal_half_life_hours):
            raise ValueError("temporal_half_life_hours must be a positive finite value")
        if not 0.0 <= importance_floor <= 1.0:
            raise ValueError("importance_floor must be between 0.0 and 1.0")
        if not 0.0 <= retention_threshold <= 1.0:
            raise ValueError("retention_threshold must be between 0.0 and 1.0")
        if retain_at_least < 0:
            raise ValueError("retain_at_least must be non-negative")
        if not self._memory_ids:
            return SelectiveForgettingResult(dropped_ids=(), retained_count=0)

        reference_time = as_of or max(memory.timestamp for memory in self._records.values())
        candidate_scores: list[tuple[float, float, datetime, str]] = []
        for memory_id in self._memory_ids:
            memory = self._records[memory_id]
            if memory.memory_type in preserve_memory_types:
                continue
            temporal_score = self._temporal_score(
                memory.timestamp,
                reference_time,
                temporal_half_life_hours=temporal_half_life_hours,
            )
            retention_score = (0.6 * temporal_score) + (0.4 * memory.importance)
            if memory.importance < importance_floor and retention_score < retention_threshold:
                candidate_scores.append(
                    (retention_score, memory.importance, memory.timestamp, memory_id)
                )

        if not candidate_scores:
            return SelectiveForgettingResult(
                dropped_ids=(),
                retained_count=len(self._memory_ids),
            )

        drop_budget = max(0, len(self._memory_ids) - retain_at_least)
        if drop_budget == 0:
            return SelectiveForgettingResult(
                dropped_ids=(),
                retained_count=len(self._memory_ids),
            )

        candidate_scores.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
        dropped_ids = tuple(memory_id for *_, memory_id in candidate_scores[:drop_budget])
        self._delete_memories(dropped_ids)
        return SelectiveForgettingResult(
            dropped_ids=dropped_ids,
            retained_count=len(self._memory_ids),
        )

    def retrieve(self, query: str, k: int = 5, recency_bias: float = 0.3) -> list[Memory]:
        if k < 1:
            raise ValueError(f"k must be positive, got {k!r}")
        if not 0.0 <= recency_bias <= 1.0:
            raise ValueError(
                f"recency_bias must be between 0.0 and 1.0, got {recency_bias!r}"
            )
        weights = RetrievalWeights(
            semantic=1.0 - recency_bias,
            temporal=recency_bias,
            importance=0.05,
        )
        return [result.memory for result in self.retrieve_with_scores(query, k=k, weights=weights)]

    def retrieve_with_scores(
        self,
        query: str,
        k: int = 5,
        *,
        weights: RetrievalWeights | None = None,
        as_of: datetime | None = None,
        temporal_half_life_hours: float = 24.0,
        candidate_multiplier: int = 5,
    ) -> list[MemorySearchResult]:
        if k < 1:
            raise ValueError(f"k must be positive, got {k!r}")
        if temporal_half_life_hours <= 0.0 or not math.isfinite(temporal_half_life_hours):
            raise ValueError("temporal_half_life_hours must be a positive finite value")
        if candidate_multiplier < 1:
            raise ValueError(f"candidate_multiplier must be positive, got {candidate_multiplier!r}")
        if not self._memory_ids:
            return []

        query_vector = np.asarray([self.encoder.encode(query)], dtype=np.float32)
        candidate_count = min(len(self._memory_ids), max(k, k * candidate_multiplier))
        similarities, indices = self._index.search(query_vector, candidate_count)
        reference_time = as_of or max(memory.timestamp for memory in self._records.values())
        rerank_weights = (weights or RetrievalWeights()).normalized()
        scored_memories: list[MemorySearchResult] = []

        for similarity, raw_index in zip(
            similarities[0].tolist(),
            indices[0].tolist(),
            strict=True,
        ):
            if raw_index < 0:
                continue
            memory_id = self._memory_ids[raw_index]
            memory = self._records[memory_id]
            semantic_score = self._normalize_similarity(float(similarity))
            temporal_score = self._temporal_score(
                memory.timestamp,
                reference_time,
                temporal_half_life_hours=temporal_half_life_hours,
            )
            importance_score = memory.importance
            final_score = rerank_weights.score(
                semantic_score=semantic_score,
                temporal_score=temporal_score,
                importance_score=importance_score,
            )
            scored_memories.append(
                MemorySearchResult(
                    memory=memory,
                    semantic_score=semantic_score,
                    temporal_score=temporal_score,
                    importance_score=importance_score,
                    final_score=final_score,
                )
            )

        scored_memories.sort(
            key=lambda result: (
                result.final_score,
                result.semantic_score,
                result.temporal_score,
                result.memory.timestamp,
                result.memory.id,
            ),
            reverse=True,
        )
        return scored_memories[:k]

    def all(self) -> list[Memory]:
        return [self._records[memory_id] for memory_id in self._memory_ids]

    def _delete_memories(self, memory_ids: tuple[str, ...]) -> None:
        if not memory_ids:
            return
        self._connection.executemany(
            "DELETE FROM memories WHERE id = ?",
            [(memory_id,) for memory_id in memory_ids],
        )
        self._connection.commit()
        removed = set(memory_ids)
        self._memory_ids = [memory_id for memory_id in self._memory_ids if memory_id not in removed]
        for memory_id in memory_ids:
            self._records.pop(memory_id, None)
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        self._index = faiss.IndexFlatIP(self.encoder.dimension)
        if not self._memory_ids:
            return
        embeddings = [
            self._records[memory_id].embedding or self.encoder.encode(self._records[memory_id].content)
            for memory_id in self._memory_ids
        ]
        self._index.add(np.asarray(embeddings, dtype=np.float32))

    def close(self) -> None:
        self._connection.close()

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        with suppress(Exception):
            self.close()

    def __len__(self) -> int:
        return len(self._memory_ids)

    @staticmethod
    def _recency_score(timestamp: datetime, newest_timestamp: datetime) -> float:
        return SQLiteFaissMemoryStore._temporal_score(
            timestamp,
            newest_timestamp,
            temporal_half_life_hours=24.0,
        )

    @staticmethod
    def _temporal_score(
        timestamp: datetime,
        reference_time: datetime,
        *,
        temporal_half_life_hours: float,
    ) -> float:
        age_seconds = max((reference_time - timestamp).total_seconds(), 0.0)
        half_life_seconds = temporal_half_life_hours * 3_600.0
        return math.pow(0.5, age_seconds / half_life_seconds)

    @staticmethod
    def _normalize_similarity(similarity: float) -> float:
        return max(0.0, min(1.0, (similarity + 1.0) / 2.0))


__all__ = [
    "HashEmbeddingEncoder",
    "MemorySearchResult",
    "RetrievalWeights",
    "SQLiteFaissMemoryStore",
    "SelectiveForgettingResult",
]
