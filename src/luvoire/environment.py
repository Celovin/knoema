"""Time, place, and situational context for simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from luvoire.types import AgentID, WorldEvent


def _validate_location_path(location_path: tuple[str, ...]) -> None:
    if not location_path:
        raise ValueError("location_path must contain at least one segment")
    for index, segment in enumerate(location_path):
        if not segment.strip():
            raise ValueError(f"location_path[{index}] must not be blank")


@dataclass(slots=True)
class EnvironmentContext:
    agent_id: AgentID
    timestamp: datetime
    location_path: tuple[str, ...]
    conditions: dict[str, Any]
    recent_events: list[WorldEvent] = field(default_factory=list)
    routine_note: str | None = None

    @property
    def location(self) -> str:
        return " > ".join(self.location_path)


class Environment:
    """Mutable world state that can be queried from an agent point of view."""

    def __init__(
        self,
        *,
        start_time: datetime,
        location_path: tuple[str, ...],
        conditions: dict[str, Any] | None = None,
    ) -> None:
        _validate_location_path(location_path)
        self.current_time = start_time
        self.location_path = location_path
        self.conditions: dict[str, Any] = dict(conditions or {})
        self._agent_locations: dict[AgentID, tuple[str, ...]] = {}
        self._events: list[WorldEvent] = []

    def set_agent_location(self, agent_id: AgentID, location_path: tuple[str, ...]) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id must not be blank")
        _validate_location_path(location_path)
        self._agent_locations[agent_id] = location_path

    def set_condition(self, key: str, value: Any) -> None:
        if not key.strip():
            raise ValueError("condition key must not be blank")
        self.conditions[key] = value

    def advance_time(self, delta: timedelta) -> None:
        if delta.total_seconds() < 0:
            raise ValueError("delta must not move time backwards")
        self.current_time += delta

    def record_event(self, event: WorldEvent) -> None:
        self._events.append(event)

    def get_context(self, agent_id: AgentID, *, event_limit: int = 10) -> EnvironmentContext:
        if event_limit < 0:
            raise ValueError("event_limit must not be negative")
        location_path = self._agent_locations.get(agent_id, self.location_path)
        recent_events = [
            event
            for event in self._events
            if agent_id in event.participants or event.location == " > ".join(location_path)
        ][-event_limit:]
        return EnvironmentContext(
            agent_id=agent_id,
            timestamp=self.current_time,
            location_path=location_path,
            conditions=dict(self.conditions),
            recent_events=recent_events,
        )

    def apply_event(self, event: WorldEvent, condition_updates: dict[str, Any] | None = None) -> None:
        self.record_event(event)
        for key, value in (condition_updates or {}).items():
            self.set_condition(key, value)


__all__ = ["Environment", "EnvironmentContext"]
