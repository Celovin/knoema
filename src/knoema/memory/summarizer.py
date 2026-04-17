"""Utilities for compressing episodic memories into semantic summaries."""

from __future__ import annotations

import math
import uuid
from collections.abc import Sequence
from datetime import datetime
from statistics import fmean

from knoema.types import Memory


class MemorySummarizer:
    """Deterministic summarizer used for compression and tests."""

    def __init__(self, min_summary_count: int = 3, max_summary_count: int = 5) -> None:
        if min_summary_count < 1:
            raise ValueError("min_summary_count must be positive")
        if max_summary_count < min_summary_count:
            raise ValueError("max_summary_count must be greater than or equal to min_summary_count")
        self.min_summary_count = min_summary_count
        self.max_summary_count = max_summary_count

    def summarize(self, events: Sequence[Memory]) -> list[Memory]:
        if not events:
            return []
        summary_count = min(
            self.max_summary_count,
            max(self.min_summary_count, math.ceil(len(events) / 15)),
        )
        summary_count = min(summary_count, len(events))
        chunks = self._chunk_events(events, summary_count)
        return [self._build_summary(chunk) for chunk in chunks]

    @staticmethod
    def _chunk_events(events: Sequence[Memory], chunk_count: int) -> list[list[Memory]]:
        chunk_size, remainder = divmod(len(events), chunk_count)
        chunks: list[list[Memory]] = []
        start = 0
        for chunk_index in range(chunk_count):
            extra = 1 if chunk_index < remainder else 0
            end = start + chunk_size + extra
            chunks.append(list(events[start:end]))
            start = end
        return chunks

    @staticmethod
    def _build_summary(events: Sequence[Memory]) -> Memory:
        first = events[0]
        last = events[-1]
        middle = events[len(events) // 2]
        if len(events) == 1:
            summary_text = first.content
        else:
            summary_text = (
                f"Over {len(events)} events, the agent moved from '{first.content}' "
                f"through '{middle.content}' toward '{last.content}'."
            )
        return Memory(
            id=f"semantic-{uuid.uuid4().hex}",
            agent_id=first.agent_id,
            timestamp=_latest_timestamp(events),
            content=summary_text,
            memory_type="semantic",
            importance=float(fmean(event.importance for event in events)),
        )


def _latest_timestamp(events: Sequence[Memory]) -> datetime:
    return max(event.timestamp for event in events)


__all__ = ["MemorySummarizer"]
