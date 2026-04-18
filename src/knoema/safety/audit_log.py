"""JSONL safety audit log helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

AuditOutcome = Literal["allowed", "blocked", "flagged"]


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    timestamp: str
    actor_id: str
    category: str
    outcome: AuditOutcome
    reason: str
    source: str = "knoema"

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        actor_id: str,
        category: str,
        outcome: AuditOutcome,
        reason: str,
        source: str = "knoema",
        timestamp: datetime | None = None,
    ) -> AuditEvent:
        moment = timestamp or datetime.now(tz=UTC)
        return cls(
            event_id=event_id,
            timestamp=moment.isoformat(),
            actor_id=actor_id,
            category=category,
            outcome=outcome,
            reason=reason,
            source=source,
        )

    def to_record(self) -> dict[str, str]:
        return cast(dict[str, str], asdict(self))


class AuditLogWriter:
    """Append-only JSONL audit writer with schema validation."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: AuditEvent) -> None:
        validate_audit_record(event.to_record())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_record(), sort_keys=True) + "\n")

    def read_events(self) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        events: list[AuditEvent] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL audit record at line {line_number}") from exc
            events.append(audit_event_from_record(payload))
        return events


def audit_event_from_record(record: MappingLike) -> AuditEvent:
    validate_audit_record(record)
    return AuditEvent(
        event_id=str(record["event_id"]),
        timestamp=str(record["timestamp"]),
        actor_id=str(record["actor_id"]),
        category=str(record["category"]),
        outcome=_audit_outcome(str(record["outcome"])),
        reason=str(record["reason"]),
        source=str(record["source"]),
    )


def validate_audit_record(record: MappingLike) -> None:
    required = {"event_id", "timestamp", "actor_id", "category", "outcome", "reason", "source"}
    if not isinstance(record, dict):
        raise ValueError("audit record must be a mapping")
    missing = required - set(record)
    if missing:
        raise ValueError(f"audit record missing required keys: {sorted(missing)}")
    for key in required:
        value = record[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"audit record field {key} must be a non-empty string")
    _audit_outcome(str(record["outcome"]))
    try:
        datetime.fromisoformat(str(record["timestamp"]))
    except ValueError as exc:
        raise ValueError("audit record timestamp must be ISO-8601") from exc


def _audit_outcome(value: str) -> AuditOutcome:
    if value not in {"allowed", "blocked", "flagged"}:
        raise ValueError("audit outcome must be allowed, blocked, or flagged")
    return cast(AuditOutcome, value)


MappingLike = dict[str, Any]
