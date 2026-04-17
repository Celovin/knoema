"""Long-term memory store backed by SQLite and FAISS."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import replace
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
        self._connection = sqlite3.connect(database)
        self._connection.row_factory = sqlite3.Row
        self._index = faiss.IndexFlatIP(self.encoder.dimension)
        self._memory_ids: list[str] = []
        self._records: dict[str, Memory] = {}
        self._ensure_schema()
        self._load_existing()

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

    def retrieve(self, query: str, k: int = 5, recency_bias: float = 0.3) -> list[Memory]:
        if k < 1:
            raise ValueError(f"k must be positive, got {k!r}")
        if not 0.0 <= recency_bias <= 1.0:
            raise ValueError(
                f"recency_bias must be between 0.0 and 1.0, got {recency_bias!r}"
            )
        if not self._memory_ids:
            return []

        query_vector = np.asarray([self.encoder.encode(query)], dtype=np.float32)
        candidate_count = min(len(self._memory_ids), max(k, k * 5))
        similarities, indices = self._index.search(query_vector, candidate_count)
        newest_timestamp = max(memory.timestamp for memory in self._records.values())
        scored_memories: list[tuple[float, Memory]] = []

        for similarity, raw_index in zip(
            similarities[0].tolist(),
            indices[0].tolist(),
            strict=True,
        ):
            if raw_index < 0:
                continue
            memory_id = self._memory_ids[raw_index]
            memory = self._records[memory_id]
            similarity_score = (float(similarity) + 1.0) / 2.0
            recency_score = self._recency_score(memory.timestamp, newest_timestamp)
            final_score = (
                (1.0 - recency_bias) * similarity_score
                + recency_bias * recency_score
                + memory.importance * 0.05
            )
            scored_memories.append((final_score, memory))

        scored_memories.sort(key=lambda item: item[0], reverse=True)
        return [memory for _, memory in scored_memories[:k]]

    def all(self) -> list[Memory]:
        return [self._records[memory_id] for memory_id in self._memory_ids]

    def close(self) -> None:
        self._connection.close()

    def __len__(self) -> int:
        return len(self._memory_ids)

    @staticmethod
    def _recency_score(timestamp: datetime, newest_timestamp: datetime) -> float:
        age_seconds = max((newest_timestamp - timestamp).total_seconds(), 0.0)
        return math.exp(-age_seconds / 86_400.0)


__all__ = ["HashEmbeddingEncoder", "SQLiteFaissMemoryStore"]
