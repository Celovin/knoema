from __future__ import annotations

from datetime import UTC, datetime

import pytest

from knoema import AuditEvent, AuditLogWriter, validate_audit_record


def test_phase53_audit_log_jsonl_round_trip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "safety.jsonl"
    writer = AuditLogWriter(path)
    event = AuditEvent.create(
        event_id="evt-001",
        actor_id="demo-user",
        category="prompt_injection",
        outcome="blocked",
        reason="blocked by deterministic content filter",
        timestamp=datetime(2026, 4, 19, 0, 0, tzinfo=UTC),
    )

    writer.append(event)
    events = writer.read_events()

    assert events == [event]
    validate_audit_record(events[0].to_record())
    assert path.read_text(encoding="utf-8").count("\n") == 1


def test_phase53_audit_schema_rejects_missing_or_invalid_fields() -> None:
    with pytest.raises(ValueError, match="missing required keys"):
        validate_audit_record({"event_id": "evt-001"})
    with pytest.raises(ValueError, match="audit outcome"):
        validate_audit_record(
            {
                "event_id": "evt-001",
                "timestamp": "2026-04-19T00:00:00+00:00",
                "actor_id": "demo-user",
                "category": "prompt_injection",
                "outcome": "ignored",
                "reason": "bad outcome",
                "source": "knoema",
            }
        )
