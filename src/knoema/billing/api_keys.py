"""Tenant API key management primitives."""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from knoema.billing.tiers import ApiKeySource, TierName


@dataclass(frozen=True, slots=True)
class APIKeyRecord:
    key_id: str
    tenant_id: str
    scope: str
    tier: TierName
    api_key_source: ApiKeySource
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


@dataclass(frozen=True, slots=True)
class VerifiedAPIKey:
    key_id: str
    tenant_id: str
    scope: str
    tier: TierName
    api_key_source: ApiKeySource


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

    def issue(
        self,
        tenant_id: str,
        scope: str,
        *,
        tier: TierName = "free",
        api_key_source: ApiKeySource | None = None,
    ) -> tuple[str, str]:
        raw_secret = _new_raw_secret()
        key_id = _new_key_id()
        resolved_source = api_key_source or _default_api_key_source(tier)
        self.store.put(
            APIKeyRecord(
                key_id=key_id,
                tenant_id=tenant_id,
                scope=scope,
                tier=tier,
                api_key_source=resolved_source,
                secret_hash=_hash_secret(raw_secret),
                created_at=datetime.now(UTC),
            )
        )
        return key_id, _format_token(key_id, raw_secret)

    def verify(self, token: str) -> str | None:
        verified = self.verify_key(token)
        if verified is None:
            return None
        return verified.tenant_id

    def verify_key(self, token: str) -> VerifiedAPIKey | None:
        parsed = _parse_token(token)
        if parsed is None:
            constant_time_equals(_hash_secret(token), _DUMMY_SECRET_HASH)
            return None
        key_id, raw_secret = parsed
        candidate_hash = _hash_secret(raw_secret)
        record = self.store.get(key_id)
        expected_hash = record.secret_hash if record is not None else _DUMMY_SECRET_HASH
        if not constant_time_equals(candidate_hash, expected_hash):
            return None
        if record is None or not record.active:
            return None
        return VerifiedAPIKey(
            key_id=record.key_id,
            tenant_id=record.tenant_id,
            scope=record.scope,
            tier=record.tier,
            api_key_source=record.api_key_source,
        )

    def revoke(self, key_id: str, *, reason: str | None = None) -> bool:
        record = self.store.get(key_id)
        if record is None:
            return False
        self.store.update(replace(record, revoked_at=datetime.now(UTC)))
        return True

    def rotate(self, key_id: str) -> tuple[str, str]:
        old_record = self.store.get(key_id)
        if old_record is None:
            raise KeyError(key_id)
        new_key_id, new_token = self.issue(
            old_record.tenant_id,
            old_record.scope,
            tier=old_record.tier,
            api_key_source=old_record.api_key_source,
        )
        self.store.update(
            replace(
                old_record,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
                rotated_to_key_id=new_key_id,
            )
        )
        return new_key_id, new_token


_DEFAULT_MANAGER = APIKeyManager()
_DUMMY_SECRET_HASH = sha256(b"knoema-invalid-secret").hexdigest()


def default_manager() -> APIKeyManager:
    return _DEFAULT_MANAGER


def issue(
    tenant_id: str,
    scope: str,
    *,
    tier: TierName = "free",
    api_key_source: ApiKeySource | None = None,
) -> tuple[str, str]:
    return _DEFAULT_MANAGER.issue(
        tenant_id,
        scope,
        tier=tier,
        api_key_source=api_key_source,
    )


def issue_key(
    tenant_id: str,
    scope: str = "llm:invoke",
    *,
    tier: TierName = "free",
    api_key_source: ApiKeySource | None = None,
) -> tuple[str, str]:
    return issue(tenant_id, scope, tier=tier, api_key_source=api_key_source)


def verify(token: str) -> str | None:
    return _DEFAULT_MANAGER.verify(token)


def verify_key(token: str) -> VerifiedAPIKey | None:
    return _DEFAULT_MANAGER.verify_key(token)


def revoke(key_id: str, *, reason: str | None = None) -> bool:
    return _DEFAULT_MANAGER.revoke(key_id, reason=reason)


def revoke_key(key_id: str, *, reason: str | None = None) -> bool:
    return revoke(key_id, reason=reason)


def rotate(key_id: str) -> tuple[str, str]:
    return _DEFAULT_MANAGER.rotate(key_id)


def rotate_key(key_id: str) -> tuple[str, str]:
    return rotate(key_id)


def constant_time_equals(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)


def _hash_secret(raw_secret: str) -> str:
    return sha256(raw_secret.encode("utf-8")).hexdigest()


def _new_key_id() -> str:
    return f"ak{secrets.token_hex(8)}"


def _new_raw_secret() -> str:
    return secrets.token_urlsafe(32)


def _format_token(key_id: str, raw_secret: str) -> str:
    return f"knoema_{key_id}_{raw_secret}"


def _parse_token(token: str) -> tuple[str, str] | None:
    if not token.startswith("knoema_"):
        return None
    parts = token.split("_", 2)
    if len(parts) != 3 or parts[0] != "knoema" or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


def _default_api_key_source(tier: TierName) -> ApiKeySource:
    if tier == "free":
        return "byo_key"
    if tier == "enterprise":
        return "dedicated"
    return "pass_through"


__all__ = [
    "APIKeyManager",
    "APIKeyRecord",
    "InMemoryAPIKeyStore",
    "VerifiedAPIKey",
    "constant_time_equals",
    "default_manager",
    "issue",
    "issue_key",
    "revoke",
    "revoke_key",
    "rotate",
    "rotate_key",
    "verify",
    "verify_key",
]
