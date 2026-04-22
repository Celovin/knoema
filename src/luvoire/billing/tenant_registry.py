"""File-backed tenant registry for commercial onboarding."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from luvoire.billing.api_keys import APIKeyManager, APIKeyRecord, InMemoryAPIKeyStore
from luvoire.billing.tiers import ApiKeySource, TierName
from luvoire.safety.audit_log import CommercialAuditLogger


class TenantRegistry:
    """Simple JSON tenant registry for the commercial PoC."""

    def __init__(self, path: Path = Path("var/billing/tenants.json")) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"tenants": {}}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("tenants"), dict):
            raise ValueError(f"invalid tenant registry: {self.path}")
        return payload

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

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
