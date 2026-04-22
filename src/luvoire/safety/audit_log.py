"""JSONL safety audit log helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, Protocol, cast

AuditOutcome = Literal["allowed", "blocked", "flagged"]
COMMERCIAL_AUDIT_EVENT_TYPES = frozenset(
    {
        "commercial.key_issued",
        "commercial.key_rotated",
        "commercial.key_revoked",
        "commercial.webhook_dispatched",
        "commercial.webhook_failed",
        "commercial.webhook_exhausted",
        "commercial.tier_limit_exceeded",
        "commercial.cap_exhausted_output_tokens",
    }
)


class CommercialAuditLogger(Protocol):
    def append(
        self,
        event_type: str,
        *,
        actor: str,
        subject: str,
        metadata: dict[str, object] | None = None,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    timestamp: str
    actor_id: str
    category: str
    outcome: AuditOutcome
    reason: str
    source: str = "luvoire"

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        actor_id: str,
        category: str,
        outcome: AuditOutcome,
        reason: str,
        source: str = "luvoire",
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


class NoOpAuditLog:
    """Drop-in audit logger used by tests or offline callers that do not need persistence."""

    def append(
        self,
        event_type: str,
        *,
        actor: str,
        subject: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        _ = event_type, actor, subject, metadata


class AuditLog:
    """Append-only commercial event log with deterministic JSONL records."""

    def __init__(
        self,
        path: str | Path = Path("var/audit/commercial.jsonl"),
        *,
        retention_days: int = 90,
    ) -> None:
        if retention_days <= 0:
            raise ValueError("retention_days must be positive")
        self.path = Path(path)
        self.retention_days = retention_days

    def append(
        self,
        event_type: str,
        *,
        actor: str,
        subject: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if event_type not in COMMERCIAL_AUDIT_EVENT_TYPES:
            raise ValueError(f"unknown commercial audit event type: {event_type}")
        record = {
            "actor": actor,
            "event_type": event_type,
            "metadata": metadata or {},
            "subject": subject,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
            handle.write("\n")

    def read_records(self) -> list[dict[str, object]]:
        if not self.path.exists():
            return []
        records: list[dict[str, object]] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL audit record at line {line_number}") from exc
            validate_commercial_audit_record(payload)
            records.append(cast(dict[str, object], payload))
        return records

    def purge_older_than(self, days: int = 90, *, now: datetime | None = None) -> int:
        if days <= 0:
            raise ValueError("days must be positive")
        cutoff = (now or datetime.now(UTC)) - timedelta(days=days)
        records = self.read_records()
        kept = [
            record
            for record in records
            if datetime.fromisoformat(str(record["timestamp"])) >= cutoff
        ]
        removed = len(records) - len(kept)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            for record in kept:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
                handle.write("\n")
        return removed


def validate_commercial_audit_record(record: object) -> None:
    if not isinstance(record, dict):
        raise ValueError("commercial audit record must be a mapping")
    required = {"actor", "event_type", "metadata", "subject", "timestamp"}
    missing = required - set(record)
    if missing:
        raise ValueError(f"commercial audit record missing required keys: {sorted(missing)}")
    for key in ("actor", "event_type", "subject", "timestamp"):
        value = record[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"commercial audit record field {key} must be a non-empty string")
    if record["event_type"] not in COMMERCIAL_AUDIT_EVENT_TYPES:
        raise ValueError("commercial audit record has unknown event type")
    if not isinstance(record["metadata"], dict):
        raise ValueError("commercial audit metadata must be a mapping")
    try:
        datetime.fromisoformat(str(record["timestamp"]))
    except ValueError as exc:
        raise ValueError("commercial audit timestamp must be ISO-8601") from exc


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
