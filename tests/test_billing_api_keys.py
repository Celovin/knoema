from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from luvoire.billing.api_keys import APIKeyManager, InMemoryAPIKeyStore, constant_time_equals


def test_api_key_issue_verify_revoke_and_hash_only_storage() -> None:
    manager = APIKeyManager(InMemoryAPIKeyStore())

    key_id, raw_secret = manager.issue("tenant-a", "llm:invoke")

    assert raw_secret.startswith(f"luvoire_{key_id}_")
    assert manager.verify(raw_secret) == "tenant-a"
    stored = manager.store.get(key_id)
    assert stored is not None
    assert stored.secret_hash != raw_secret
    assert raw_secret not in repr(stored)
    assert manager.revoke(key_id) is True
    assert manager.verify(raw_secret) is None


def test_api_key_rotation_keeps_old_key_temporarily_valid() -> None:
    manager = APIKeyManager(InMemoryAPIKeyStore())
    key_id, old_secret = manager.issue("tenant-b", "llm:invoke")

    new_key_id, new_secret = manager.rotate(key_id)

    assert new_key_id != key_id
    assert manager.verify(old_secret) == "tenant-b"
    assert manager.verify(new_secret) == "tenant-b"
    old_record = manager.store.get(key_id)
    assert old_record is not None
    assert old_record.expires_at is not None
    assert old_record.rotated_to_key_id == new_key_id
    assert new_secret.startswith(f"luvoire_{new_key_id}_")


def test_constant_time_comparison_function_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def compare(left: str, right: str) -> bool:
        calls.append((left, right))
        return constant_time_equals(left, right)

    monkeypatch.setattr("luvoire.billing.api_keys.constant_time_equals", compare)
    manager = APIKeyManager(InMemoryAPIKeyStore())
    _key_id, raw_secret = manager.issue("tenant-c", "llm:invoke")

    assert manager.verify(raw_secret) == "tenant-c"
    assert calls


# --- Round-5 audit: rotation grace tightened to 1h, configurable -------


def test_rotation_default_grace_is_one_hour() -> None:
    """The previous 24h grace was too long when rotation is triggered
    by suspected leak. New default is 1 hour. Round-5 audit fix.
    """

    from datetime import UTC, datetime, timedelta

    manager = APIKeyManager(InMemoryAPIKeyStore())
    key_id, _ = manager.issue("tenant-d", "llm:invoke")
    before = datetime.now(UTC)
    manager.rotate(key_id)
    after = datetime.now(UTC)

    record = manager.store.get(key_id)
    assert record is not None
    assert record.expires_at is not None
    delta = record.expires_at - before
    # Allow a small clock skew window around the 1h target.
    assert timedelta(minutes=59) <= delta <= timedelta(hours=1) + (after - before) + timedelta(seconds=1)


def test_rotation_grace_zero_for_known_compromise() -> None:
    """Operators rotating a known-compromised key MUST be able to set
    ``grace_period=timedelta(0)`` for an immediate cut.
    """

    from datetime import UTC, datetime, timedelta

    manager = APIKeyManager(InMemoryAPIKeyStore())
    key_id, old_secret = manager.issue("tenant-e", "llm:invoke")
    manager.rotate(key_id, grace_period=timedelta(0))

    record = manager.store.get(key_id)
    assert record is not None
    assert record.expires_at is not None
    assert record.expires_at <= datetime.now(UTC)
    # The old token must already be invalid.
    assert manager.verify(old_secret) is None


def test_rotation_rejects_negative_grace() -> None:
    from datetime import timedelta

    manager = APIKeyManager(InMemoryAPIKeyStore())
    key_id, _ = manager.issue("tenant-f", "llm:invoke")
    with pytest.raises(ValueError, match="non-negative"):
        manager.rotate(key_id, grace_period=timedelta(seconds=-1))


def test_rotation_audit_log_includes_grace_metadata() -> None:
    """Audit log must capture grace_period_seconds + severity for SOC
    pipelines that flag short-grace rotations as security events.
    """

    from datetime import timedelta

    class _CapturingAuditLog:
        def __init__(self) -> None:
            self.events: list[dict[str, object]] = []

        def append(self, event_type: str, *, actor: str, subject: str, metadata: dict[str, object]) -> None:
            self.events.append({"event_type": event_type, "metadata": dict(metadata)})

    audit = _CapturingAuditLog()
    manager = APIKeyManager(InMemoryAPIKeyStore(), audit_log=audit)  # type: ignore[arg-type]
    key_id, _ = manager.issue("tenant-g", "llm:invoke")
    manager.rotate(key_id, grace_period=timedelta(minutes=5))

    rotation_events = [e for e in audit.events if e["event_type"] == "commercial.key_rotated"]
    assert rotation_events, "expected a key_rotated audit log entry"
    metadata = rotation_events[0]["metadata"]
    assert metadata["grace_period_seconds"] == 300
    assert metadata["severity"] == "high"


def test_billing_slot_files_do_not_contain_obvious_raw_secrets() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "src/luvoire/billing", "tests/test_billing_*.py", "docs/billing.md"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    patterns = (
        "sk" + "-proj-",
        "sk" + "-live-",
        "ghp" + "_",
        "hf" + "_",
        "BEGIN " + "PRIVATE KEY",
    )
    offenders: list[str] = []
    for rel_path in tracked:
        path = Path(rel_path)
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if any(pattern in text for pattern in patterns):
                offenders.append(rel_path)
    assert offenders == []
