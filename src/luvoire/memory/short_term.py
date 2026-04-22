"""Short-term in-memory buffer for recent events."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator

from luvoire.types import Memory


class ShortTermMemoryBuffer:
    """FIFO buffer that keeps only the most recent memories."""

    def __init__(self, capacity: int = 50) -> None:
        if capacity < 1:
            raise ValueError(f"capacity must be positive, got {capacity!r}")
        self.capacity = capacity
        self._memories: deque[Memory] = deque(maxlen=capacity)

    def add(self, memory: Memory) -> None:
        self._memories.append(memory)

    def extend(self, memories: Iterable[Memory]) -> None:
        for memory in memories:
            self.add(memory)

    def recent(self, limit: int | None = None) -> list[Memory]:
        items = list(self._memories)
        if limit is None:
            return items
        if limit < 0:
            raise ValueError(f"limit must not be negative, got {limit!r}")
        if limit == 0:
            return []
        return items[-limit:]

    def clear(self) -> None:
        self._memories.clear()

    def __iter__(self) -> Iterator[Memory]:
        return iter(self._memories)

    def __len__(self) -> int:
        return len(self._memories)


__all__ = ["ShortTermMemoryBuffer"]
