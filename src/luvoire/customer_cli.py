"""Customer onboarding commands for the Luvoire CLI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from luvoire.billing.tenant_registry import TenantRegistry
from luvoire.billing.tiers import TierName
from luvoire.safety.audit_log import AuditLog

VALID_TIERS: set[str] = {"free", "pro", "team", "enterprise"}


def add_customer_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    customer = subparsers.add_parser("customer", help="Manage commercial tenants and API keys.")
    customer_subparsers = customer.add_subparsers(dest="customer_command", required=True)

    create = customer_subparsers.add_parser("create", help="Create a tenant and first API key.")
    create.add_argument("--tenant-id", required=True)
    create.add_argument("--tier", required=True)
    create.add_argument("--display-name", required=True)

    issue = customer_subparsers.add_parser("issue-key", help="Issue an additional tenant API key.")
    issue.add_argument("--tenant-id", required=True)

    rotate = customer_subparsers.add_parser("rotate-key", help="Rotate a tenant API key.")
    rotate.add_argument("--tenant-id", required=True)
    rotate.add_argument("--api-key-id", required=True)

    revoke = customer_subparsers.add_parser("revoke-key", help="Revoke a tenant API key.")
    revoke.add_argument("--tenant-id", required=True)
    revoke.add_argument("--api-key-id", required=True)
    revoke.add_argument("--reason", required=True)

    usage = customer_subparsers.add_parser("show-usage", help="Show monthly tenant usage.")
    usage.add_argument("--tenant-id", required=True)
    usage.add_argument("--month", default=None, help="Month filter in YYYY-MM format.")

    customer_subparsers.add_parser("list", help="List tenants without secrets.")


def handle_customer_command(args: argparse.Namespace) -> int:
    registry = TenantRegistry()
    audit_log = AuditLog(Path("var/audit/commercial.jsonl"))
    command = str(args.customer_command)
    if command == "create":
        tier = _validated_tier(str(args.tier))
        if tier is None:
            return 2
        created = registry.create_tenant(str(args.tenant_id), tier, str(args.display_name))
        if not created:
            return 3
        manager = registry.key_manager(audit_log)
        key_id, token = manager.issue(str(args.tenant_id), "llm:invoke", tier=tier, issuer="customer-cli")
        registry.persist_keys(manager)
        _print_secret_once(key_id, token)
        return 0
    if command == "issue-key":
        tenant = _require_tenant(registry, str(args.tenant_id))
        if tenant is None:
            return 1
        tier = cast(TierName, tenant["tier"])
        manager = registry.key_manager(audit_log)
        key_id, token = manager.issue(str(args.tenant_id), "llm:invoke", tier=tier, issuer="customer-cli")
        registry.persist_keys(manager)
        _print_secret_once(key_id, token)
        return 0
    if command == "rotate-key":
        if not _tenant_owns_key(registry, str(args.tenant_id), str(args.api_key_id)):
            return 1
        manager = registry.key_manager(audit_log)
        key_id, token = manager.rotate(str(args.api_key_id))
        registry.persist_keys(manager)
        _print_secret_once(key_id, token)
        return 0
    if command == "revoke-key":
        if not _tenant_owns_key(registry, str(args.tenant_id), str(args.api_key_id)):
            return 1
        manager = registry.key_manager(audit_log)
        if not manager.revoke(str(args.api_key_id), reason=str(args.reason)):
            return 1
        registry.persist_keys(manager)
        print(f"Revoked API key {args.api_key_id} for tenant {args.tenant_id}.")
        return 0
    if command == "show-usage":
        rows = _usage_rows(Path("var/billing"), str(args.tenant_id), cast(str | None, args.month))
        _print_usage_table(rows)
        return 0
    if command == "list":
        _print_tenant_table(registry.list_tenants())
        return 0
    return 2


def _validated_tier(value: str) -> TierName | None:
    if value not in VALID_TIERS:
        print("Invalid tier. Expected one of: free, pro, team, enterprise.")
        return None
    return cast(TierName, value)


def _require_tenant(registry: TenantRegistry, tenant_id: str) -> dict[str, Any] | None:
    tenant = registry.tenant(tenant_id)
    if tenant is None:
        print(f"Tenant not found: {tenant_id}")
    return tenant


def _tenant_owns_key(registry: TenantRegistry, tenant_id: str, api_key_id: str) -> bool:
    tenant = _require_tenant(registry, tenant_id)
    if tenant is None:
        return False
    for key_payload in tenant.get("keys", []):
        if isinstance(key_payload, dict) and key_payload.get("key_id") == api_key_id:
            return True
    print(f"API key not found for tenant {tenant_id}: {api_key_id}")
    return False


def _print_secret_once(api_key_id: str, token: str) -> None:
    content_width = max(70, len(f"Bearer {token}"))
    border = "+" + "-" * (content_width + 2) + "+"
    print(border)
    print(_box_line("This is the only time you will see this key. Store it now.", content_width))
    print(_box_line(f"API key id: {api_key_id}", content_width))
    print(_box_line("Authorization header:", content_width))
    print(_box_line(f"Bearer {token}", content_width))
    print(border)
    print()


def _box_line(value: str, content_width: int) -> str:
    return f"| {value:<{content_width}} |"


def _print_tenant_table(tenants: Iterable[dict[str, Any]]) -> None:
    print("tenant_id\ttier\tkey_count\tdisplay_name")
    for tenant in tenants:
        keys = tenant.get("keys", [])
        key_count = len(keys) if isinstance(keys, list) else 0
        print(f"{tenant['tenant_id']}\t{tenant['tier']}\t{key_count}\t{tenant['display_name']}")


def _usage_rows(spool_dir: Path, tenant_id: str, month: str | None) -> list[dict[str, object]]:
    aggregates: dict[str, dict[str, Decimal | int | str]] = {}
    for path in sorted(spool_dir.glob("usage_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            payload = json.loads(line)
            if payload.get("tenant_id") != tenant_id:
                continue
            recorded_at = str(payload.get("recorded_at", ""))
            if month is not None and not recorded_at.startswith(month):
                continue
            model = str(payload["model"])
            row = aggregates.setdefault(
                model,
                {"model": model, "input_tokens": 0, "output_tokens": 0, "cost_usd": Decimal("0")},
            )
            row["input_tokens"] = int(row["input_tokens"]) + int(payload["input_tokens"])
            row["output_tokens"] = int(row["output_tokens"]) + int(payload["output_tokens"])
            row["cost_usd"] = cast(Decimal, row["cost_usd"]) + Decimal(str(payload["cost_usd"]))
    return [
        {
            "model": row["model"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "cost_usd": row["cost_usd"],
        }
        for row in sorted(aggregates.values(), key=lambda item: str(item["model"]))
    ]


def _print_usage_table(rows: list[dict[str, object]]) -> None:
    print("model\tinput_tokens\toutput_tokens\tcost_usd")
    total = Decimal("0")
    for row in rows:
        cost = cast(Decimal, row["cost_usd"])
        total += cost
        print(f"{row['model']}\t{row['input_tokens']}\t{row['output_tokens']}\t{cost}")
    print(f"TOTAL\t\t\t{total}")


__all__ = ["TenantRegistry", "add_customer_subparser", "handle_customer_command"]
