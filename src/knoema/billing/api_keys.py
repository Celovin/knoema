"""Tenant API key management primitives."""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256


@dataclass(frozen=True, slots=True)
class APIKeyRecord:
    key_id: str
    tenant_id: str
    scope: str
    secret_hash: str
    created_at: datetime
    revoked_at: datetime | None = None
    expires_at: datetime | None = None
    rotated_to_key_id: str | None = None

    @property
    def active(self) -> bool:
        now = datetime.now(UTC)
        if self.revoked_at is not None:
            return False
        return not (self.expires_at is not None and self.expires_at < now)


class InMemoryAPIKeyStore:
    """Hash-only API key persistence stub that can be replaced by Postgres later."""

    def __init__(self) -> None:
        self.records: dict[str, APIKeyRecord] = {}

    def put(self, record: APIKeyRecord) -> None:
        self.records[record.key_id] = record

    def get(self, key_id: str) -> APIKeyRecord | None:
        return self.records.get(key_id)

    def update(self, record: APIKeyRecord) -> None:
        self.records[record.key_id] = record

    def all(self) -> tuple[APIKeyRecord, ...]:
        return tuple(self.records.values())


class APIKeyManager:
    """Issue, verify, revoke, and rotate tenant API keys without storing raw secrets."""

    def __init__(self, store: InMemoryAPIKeyStore | None = None) -> None:
        self.store = store or InMemoryAPIKeyStore()

    def issue(self, tenant_id: str, scope: str) -> tuple[str, str]:
        raw_secret = _new_raw_secret()
        key_id = _new_key_id()
        self.store.put(
            APIKeyRecord(
                key_id=key_id,
                tenant_id=tenant_id,
                scope=scope,
                secret_hash=_hash_secret(raw_secret),
                created_at=datetime.now(UTC),
            )
        )
        return key_id, raw_secret

    def verify(self, raw_secret: str) -> str | None:
        candidate_hash = _hash_secret(raw_secret)
        for record in self.store.all():
            if record.active and constant_time_equals(candidate_hash, record.secret_hash):
                return record.tenant_id
        return None

    def revoke(self, key_id: str) -> bool:
        record = self.store.get(key_id)
        if record is None:
            return False
        self.store.update(replace(record, revoked_at=datetime.now(UTC)))
        return True

    def rotate(self, key_id: str) -> tuple[str, str]:
        old_record = self.store.get(key_id)
        if old_record is None:
            raise KeyError(key_id)
        new_key_id, new_raw_secret = self.issue(old_record.tenant_id, old_record.scope)
        self.store.update(
            replace(
                old_record,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
                rotated_to_key_id=new_key_id,
            )
        )
        return new_key_id, new_raw_secret


_DEFAULT_MANAGER = APIKeyManager()


def issue(tenant_id: str, scope: str) -> tuple[str, str]:
    return _DEFAULT_MANAGER.issue(tenant_id, scope)


def verify(raw_secret: str) -> str | None:
    return _DEFAULT_MANAGER.verify(raw_secret)


def revoke(key_id: str) -> bool:
    return _DEFAULT_MANAGER.revoke(key_id)


def rotate(key_id: str) -> tuple[str, str]:
    return _DEFAULT_MANAGER.rotate(key_id)


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def _hash_secret(raw_secret: str) -> str:
    return sha256(raw_secret.encode("utf-8")).hexdigest()


def _new_key_id() -> str:
    return f"key_{secrets.token_hex(8)}"


def _new_raw_secret() -> str:
    return f"knm_{secrets.token_urlsafe(32)}"


__all__ = [
    "APIKeyManager",
    "APIKeyRecord",
    "InMemoryAPIKeyStore",
    "constant_time_equals",
    "issue",
    "revoke",
    "rotate",
    "verify",
]
