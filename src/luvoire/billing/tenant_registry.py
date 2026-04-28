"""File-backed tenant registry for commercial onboarding."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from luvoire.billing.api_keys import APIKeyManager, APIKeyRecord, InMemoryAPIKeyStore
from luvoire.billing.tiers import ApiKeySource, TierName
from luvoire.safety.audit_log import CommercialAuditLogger

_FERNET_PREFIX = b"luvoire-tenants-v1\n"
"""Magic prefix that distinguishes Fernet-encrypted registry files from
plain JSON. Encrypted files begin with this header followed by the
Fernet token; plain JSON files begin with ``{``. The prefix lets
:meth:`TenantRegistry.load` auto-detect format without an explicit flag.
"""


def _fernet_key_from_env() -> str | None:
    """Return the configured Fernet key, or ``None`` when unset.

    Reads ``LUVOIRE_TENANT_REGISTRY_KEY`` and treats empty / whitespace
    as unset so accidental ``KEY=""`` deploys cannot silently switch the
    registry into plaintext mode.
    """

    raw = os.environ.get("LUVOIRE_TENANT_REGISTRY_KEY", "").strip()
    return raw or None


class TenantRegistry:
    """JSON tenant registry with optional Fernet encryption-at-rest.

    When the ``LUVOIRE_TENANT_REGISTRY_KEY`` environment variable is set
    to a valid Fernet key (44 base64-url chars from
    ``cryptography.fernet.Fernet.generate_key()``), the on-disk file is
    encrypted with AES-128-CBC + HMAC-SHA256 (Fernet's standard
    construction). Without the variable the registry falls back to
    plaintext JSON for development and existing deployments — encryption
    is opt-in to avoid silently breaking on-disk fixtures.

    The registry stores only API key **hashes**, never raw secrets, so
    encryption-at-rest is defense-in-depth: even hash exfiltration is
    prevented if the host disk is read by an attacker without the
    runtime key.
    """

    def __init__(
        self,
        path: Path = Path("var/billing/tenants.json"),
        *,
        encryption_key: str | None = None,
    ) -> None:
        self.path = path
        # Explicit kwarg wins over env so tests can pin a key without
        # touching the global environment.
        self._encryption_key = encryption_key or _fernet_key_from_env()

    @property
    def encryption_enabled(self) -> bool:
        return self._encryption_key is not None

    def _fernet(self) -> Any:
        if self._encryption_key is None:
            raise RuntimeError("encryption is not configured")
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise RuntimeError(
                "tenant registry encryption requested but the "
                "``cryptography`` package is not installed"
            ) from exc
        return Fernet(self._encryption_key.encode("utf-8"))

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"tenants": {}}
        raw = self.path.read_bytes()
        # Auto-detect format: encrypted files begin with our prefix,
        # plain JSON files begin with ``{``. This lets the same registry
        # path coexist across encrypted-mode and plaintext-mode deploys
        # during a rollout.
        if raw.startswith(_FERNET_PREFIX):
            if self._encryption_key is None:
                raise RuntimeError(
                    f"tenant registry {self.path} is Fernet-encrypted but no "
                    "LUVOIRE_TENANT_REGISTRY_KEY is configured"
                )
            token = raw[len(_FERNET_PREFIX):]
            try:
                plaintext_bytes = self._fernet().decrypt(token)
            except Exception as exc:
                raise ValueError(
                    f"failed to decrypt tenant registry {self.path}: "
                    f"{type(exc).__name__}"
                ) from exc
            payload = json.loads(plaintext_bytes.decode("utf-8"))
        else:
            payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("tenants"), dict):
            raise ValueError(f"invalid tenant registry: {self.path}")
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        plaintext = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        if self.encryption_enabled:
            token = self._fernet().encrypt(plaintext)
            # Atomic-write: stage to a sibling tmp path then rename.
            # Without this, an interrupted write would leave a half-
            # finished encrypted file that fails to decrypt on next
            # load (Fernet's HMAC catches the truncation but the
            # tenant registry stays wedged until manually purged).
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_bytes(_FERNET_PREFIX + token)
            tmp.replace(self.path)
        else:
            self.path.write_text(plaintext.decode("utf-8"), encoding="utf-8")

    def create_tenant(self, tenant_id: str, tier: TierName, display_name: str) -> bool:
        payload = self.load()
        tenants = cast(dict[str, Any], payload["tenants"])
        if tenant_id in tenants:
            return False
        tenants[tenant_id] = {
            "created_at": datetime.now(UTC).isoformat(),
            "display_name": display_name,
            "keys": [],
            "tenant_id": tenant_id,
            "tier": tier,
        }
        self.save(payload)
        return True

    def tenant(self, tenant_id: str) -> dict[str, Any] | None:
        tenants = cast(dict[str, Any], self.load()["tenants"])
        tenant = tenants.get(tenant_id)
        if isinstance(tenant, dict):
            return tenant
        return None

    def list_tenants(self) -> list[dict[str, Any]]:
        tenants = cast(dict[str, Any], self.load()["tenants"])
        return [cast(dict[str, Any], tenants[tenant_id]) for tenant_id in sorted(tenants)]

    def key_manager(self, audit_log: CommercialAuditLogger | None = None) -> APIKeyManager:
        store = InMemoryAPIKeyStore()
        for tenant in self.list_tenants():
            for key_payload in tenant.get("keys", []):
                if isinstance(key_payload, dict):
                    store.put(_record_from_json(key_payload))
        return APIKeyManager(store, audit_log=audit_log)

    def persist_keys(self, manager: APIKeyManager) -> None:
        payload = self.load()
        tenants = cast(dict[str, Any], payload["tenants"])
        grouped: dict[str, list[dict[str, object]]] = {}
        for record in sorted(manager.store.all(), key=lambda item: item.key_id):
            grouped.setdefault(record.tenant_id, []).append(_record_to_json(record))
        for tenant_id, tenant in tenants.items():
            if isinstance(tenant, dict):
                tenant["keys"] = grouped.get(str(tenant_id), [])
        self.save(payload)


def _record_to_json(record: APIKeyRecord) -> dict[str, object]:
    payload = asdict(record)
    payload["created_at"] = record.created_at.isoformat()
    payload["revoked_at"] = None if record.revoked_at is None else record.revoked_at.isoformat()
    payload["expires_at"] = None if record.expires_at is None else record.expires_at.isoformat()
    return cast(dict[str, object], payload)


def _record_from_json(payload: dict[str, object]) -> APIKeyRecord:
    return APIKeyRecord(
        key_id=str(payload["key_id"]),
        tenant_id=str(payload["tenant_id"]),
        scope=str(payload["scope"]),
        tier=cast(TierName, payload["tier"]),
        api_key_source=cast(ApiKeySource, payload["api_key_source"]),
        secret_hash=str(payload["secret_hash"]),
        created_at=datetime.fromisoformat(str(payload["created_at"])),
        revoked_at=_optional_datetime(payload.get("revoked_at")),
        expires_at=_optional_datetime(payload.get("expires_at")),
        rotated_to_key_id=cast(str | None, payload.get("rotated_to_key_id")),
    )


def _optional_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(str(value))


__all__ = ["TenantRegistry"]
