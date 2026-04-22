from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from luvoire.billing.api_keys import APIKeyManager, InMemoryAPIKeyStore
from luvoire.billing.gateway import LLMGateway, UsageMeter
from luvoire.billing.webhooks import WebhookDispatcher
from luvoire.safety.audit_log import COMMERCIAL_AUDIT_EVENT_TYPES, AuditLog


class MockLiteLLM:
    def __call__(self, **kwargs: object) -> dict[str, object]:
        return {
            "choices": [{"message": {"content": "mock completion"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8},
            "cost_usd": "0.0100",
        }


def _records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_commercial_audit_event_registry_contains_required_types() -> None:
    assert {
        "commercial.key_issued",
        "commercial.key_rotated",
        "commercial.key_revoked",
        "commercial.webhook_dispatched",
        "commercial.webhook_failed",
        "commercial.webhook_exhausted",
        "commercial.tier_limit_exceeded",
        "commercial.cap_exhausted_output_tokens",
    } == COMMERCIAL_AUDIT_EVENT_TYPES


def test_commercial_api_key_lifecycle_writes_secret_safe_audit_rows(tmp_path: Path) -> None:
    audit_path = tmp_path / "commercial.jsonl"
    audit = AuditLog(audit_path)
    manager = APIKeyManager(InMemoryAPIKeyStore(), audit_log=audit)

    key_id, token = manager.issue("tenant-audit", "llm:invoke", tier="pro", issuer="operator")
    new_key_id, new_token = manager.rotate(key_id)
    assert manager.revoke(new_key_id, reason="customer-request") is True

    text = audit_path.read_text(encoding="utf-8")
    assert token not in text
    assert token.split("_", 2)[2] not in text
    assert new_token not in text
    assert new_token.split("_", 2)[2] not in text
    records = _records(audit_path)
    assert [record["event_type"] for record in records] == [
        "commercial.key_issued",
        "commercial.key_issued",
        "commercial.key_rotated",
        "commercial.key_revoked",
    ]
    assert records[0]["metadata"] == {"api_key_id": key_id, "issuer": "operator", "tier": "pro"}
    assert records[2]["metadata"]["old_api_key_id"] == key_id
    assert records[2]["metadata"]["new_api_key_id"] == new_key_id
    assert records[3]["metadata"]["reason"] == "customer-request"


def test_commercial_webhook_audit_rows_hash_endpoint_url(tmp_path: Path) -> None:
    audit_path = tmp_path / "commercial.jsonl"
    audit = AuditLog(audit_path)
    calls = 0

    def post(_url: str, _body: bytes, _headers: dict[str, str], _timeout: float) -> int:
        nonlocal calls
        calls += 1
        return 500

    dispatcher = WebhookDispatcher(
        secret="secret",
        endpoint_url="https://example.invalid/webhook",
        http_post=post,
        sleeper=lambda _delay: None,
        auto_start=False,
        audit_log=audit,
    )

    result = dispatcher.deliver_now("usage.recorded", {"tenant_id": "tenant-webhook"})

    assert result.delivered is False
    assert calls == 4
    text = audit_path.read_text(encoding="utf-8")
    assert "https://example.invalid/webhook" not in text
    records = _records(audit_path)
    assert records[0]["event_type"] == "commercial.webhook_dispatched"
    assert [record["event_type"] for record in records[1:5]] == ["commercial.webhook_failed"] * 4
    assert records[-1]["event_type"] == "commercial.webhook_exhausted"
    assert records[-1]["metadata"]["attempts"] == 4


def test_commercial_gateway_logs_tier_violation_and_cap_exhaustion(tmp_path: Path) -> None:
    audit_path = tmp_path / "commercial.jsonl"
    audit = AuditLog(audit_path)
    meter = UsageMeter(tmp_path / "usage")
    gateway = LLMGateway(meter, completion_client=MockLiteLLM(), audit_log=audit)

    tier_violation = gateway.complete(
        tenant_id="tenant-gateway",
        tier="free",
        api_key_source="pass_through",
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "blocked"}],
    )
    meter.record(
        tenant_id="tenant-gateway",
        model="gpt-5.4-mini",
        input_tokens=1,
        output_tokens=2_000_000,
        cost_usd=Decimal("0"),
        tier="pro",
    )
    cap_exhaustion = gateway.complete(
        tenant_id="tenant-gateway",
        tier="pro",
        api_key_source="pass_through",
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "blocked"}],
        max_tokens=1,
    )

    assert tier_violation.ok is False
    assert cap_exhaustion.ok is False
    records = _records(audit_path)
    assert records[0]["event_type"] == "commercial.tier_limit_exceeded"
    assert records[0]["metadata"]["tier"] == "free"
    assert records[1]["event_type"] == "commercial.cap_exhausted_output_tokens"
    assert records[1]["metadata"]["cap"] == 2_000_000
    assert records[1]["metadata"]["observed"] == 2_000_001


def test_commercial_audit_log_purge_removes_records_older_than_window(tmp_path: Path) -> None:
    path = tmp_path / "commercial.jsonl"
    now = datetime(2026, 4, 22, tzinfo=UTC)
    old = now - timedelta(days=91)
    fresh = now - timedelta(days=2)
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "actor": "system",
                        "event_type": "commercial.key_issued",
                        "metadata": {},
                        "subject": "tenant-old",
                        "timestamp": old.isoformat(),
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "actor": "system",
                        "event_type": "commercial.key_issued",
                        "metadata": {},
                        "subject": "tenant-fresh",
                        "timestamp": fresh.isoformat(),
                    },
                    sort_keys=True,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    audit = AuditLog(path)

    removed = audit.purge_older_than(days=90, now=now)

    assert removed == 1
    records = audit.read_records()
    assert [record["subject"] for record in records] == ["tenant-fresh"]


def test_audit_log_show_filters_by_tenant_and_since(tmp_path: Path) -> None:
    path = tmp_path / "commercial.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "actor": "system",
                        "event_type": "commercial.key_issued",
                        "metadata": {"api_key_id": "ak1"},
                        "subject": "tenant-a",
                        "timestamp": "2026-04-01T00:00:00+00:00",
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "actor": "system",
                        "event_type": "commercial.key_revoked",
                        "metadata": {"api_key_id": "ak2"},
                        "subject": "tenant-b",
                        "timestamp": "2026-04-02T00:00:00+00:00",
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {
                        "actor": "system",
                        "event_type": "commercial.key_rotated",
                        "metadata": {"old_api_key_id": "ak1", "new_api_key_id": "ak3"},
                        "subject": "tenant-a",
                        "timestamp": "2026-04-03T00:00:00+00:00",
                    },
                    sort_keys=True,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/audit_log_show.py",
            "tenant-a",
            "--since",
            "2026-04-02T00:00:00+00:00",
            "--path",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    lines = result.stdout.splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["event_type"] == "commercial.key_rotated"
    assert payload["subject"] == "tenant-a"
