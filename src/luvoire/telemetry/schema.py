from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
TelemetryProperties: TypeAlias = dict[str, JSONScalar]


def build_cli_properties(
    *,
    dry_run: bool,
    json_output: bool,
    agent_count: int | None = None,
    duration_days: int | None = None,
    tick_duration_minutes: int | None = None,
    scheduled_events: int | None = None,
    log_count: int | None = None,
    prompt_language: str | None = None,
) -> TelemetryProperties:
    properties: TelemetryProperties = {
        "library": "luvoire-engine",
        "surface": "cli",
        "dry_run": dry_run,
        "json_output": json_output,
    }
    if agent_count is not None:
        properties["agent_count"] = agent_count
    if duration_days is not None:
        properties["duration_days"] = duration_days
    if tick_duration_minutes is not None:
        properties["tick_duration_minutes"] = tick_duration_minutes
    if scheduled_events is not None:
        properties["scheduled_events"] = scheduled_events
    if log_count is not None:
        properties["log_count"] = log_count
    if prompt_language is not None:
        properties["prompt_language"] = prompt_language
    return properties


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    event: str
    distinct_id: str
    properties: TelemetryProperties = field(default_factory=dict)

    def to_payload(self, *, api_key: str | None = None) -> dict[str, object]:
        payload: dict[str, object] = {
            "event": self.event,
            "distinct_id": self.distinct_id,
            "properties": dict(self.properties),
        }
        if api_key is not None:
            payload["api_key"] = api_key
        return payload
