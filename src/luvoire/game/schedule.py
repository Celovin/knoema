"""Daily routine helpers for game-style NPC scheduling."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from luvoire.types import ActionType


def _validate_hour(name: str, value: int) -> int:
    resolved = int(value)
    if not 0 <= resolved <= 24:
        raise ValueError(f"{name} must be between 0 and 24 inclusive")
    return resolved


def _validate_location_path(location_path: tuple[str, ...]) -> tuple[str, ...]:
    resolved = tuple(str(segment).strip() for segment in location_path)
    if not resolved:
        raise ValueError("location_path must contain at least one segment")
    for index, segment in enumerate(resolved):
        if not segment:
            raise ValueError(f"location_path[{index}] must not be blank")
    return resolved


@dataclass(frozen=True, slots=True)
class RoutineEntry:
    start_hour: int
    end_hour: int
    location_path: tuple[str, ...]
    default_action: ActionType | str
    default_target: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "start_hour", _validate_hour("start_hour", self.start_hour))
        object.__setattr__(self, "end_hour", _validate_hour("end_hour", self.end_hour))
        object.__setattr__(self, "location_path", _validate_location_path(self.location_path))
        object.__setattr__(self, "default_action", str(self.default_action).strip() or "observe")
        if self.default_target is not None:
            target = str(self.default_target).strip()
            object.__setattr__(self, "default_target", target or None)

    def matches_hour(self, hour: int) -> bool:
        resolved_hour = int(hour) % 24
        start = self.start_hour % 24
        end = self.end_hour % 24
        if start == end:
            return True
        if start < end:
            return start <= resolved_hour < end
        return resolved_hour >= start or resolved_hour < end


def active_routine_entry(
    routine: Sequence[RoutineEntry] | None,
    timestamp: datetime,
) -> RoutineEntry | None:
    if not routine:
        return None
    for entry in routine:
        if entry.matches_hour(timestamp.hour):
            return entry
    return None


__all__ = ["RoutineEntry", "active_routine_entry"]
