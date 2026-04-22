"""Cron-like event scheduler for simulation ticks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from heapq import heappop, heappush

from luvoire.types import WorldEvent


@dataclass(order=True, slots=True)
class ScheduledEvent:
    run_at: datetime
    event: WorldEvent = field(compare=False)


class EventScheduler:
    """Priority-queue scheduler keyed by event timestamp."""

    def __init__(self) -> None:
        self._queue: list[ScheduledEvent] = []

    def schedule(self, event: WorldEvent) -> None:
        heappush(self._queue, ScheduledEvent(run_at=event.timestamp, event=event))

    def due(self, now: datetime) -> list[WorldEvent]:
        events: list[WorldEvent] = []
        while self._queue and self._queue[0].run_at <= now:
            events.append(heappop(self._queue).event)
        return events

    def __len__(self) -> int:
        return len(self._queue)


__all__ = ["EventScheduler", "ScheduledEvent"]
