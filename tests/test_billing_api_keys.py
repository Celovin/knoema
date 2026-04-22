from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from knoema.billing.api_keys import APIKeyManager, InMemoryAPIKeyStore, constant_time_equals


def test_api_key_issue_verify_revoke_and_hash_only_storage() -> None:
    manager = APIKeyManager(InMemoryAPIKeyStore())

    key_id, raw_secret = manager.issue("tenant-a", "llm:invoke")

    assert raw_secret.startswith("knm_")
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


def test_constant_time_comparison_function_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def compare(left: str, right: str) -> bool:
        calls.append((left, right))
        return constant_time_equals(left, right)

    monkeypatch.setattr("knoema.billing.api_keys.constant_time_equals", compare)
    manager = APIKeyManager(InMemoryAPIKeyStore())
    _key_id, raw_secret = manager.issue("tenant-c", "llm:invoke")

    assert manager.verify(raw_secret) == "tenant-c"
    assert calls


def test_billing_slot_files_do_not_contain_obvious_raw_secrets() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "src/knoema/billing", "tests/test_billing_*.py", "docs/billing.md"],
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
