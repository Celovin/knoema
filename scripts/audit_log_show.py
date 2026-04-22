"""Read-only commercial audit log filter."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from luvoire.safety.audit_log import AuditLog


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show commercial audit log records for a tenant.")
    parser.add_argument("tenant_id", help="Tenant ID to filter by.")
    parser.add_argument("--since", default=None, help="Inclusive ISO date or datetime filter.")
    parser.add_argument("--path", type=Path, default=Path("var/audit/commercial.jsonl"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    since = _parse_since(args.since)
    log = AuditLog(args.path)
    for record in log.read_records():
        if record["subject"] != args.tenant_id:
            continue
        if since is not None and datetime.fromisoformat(str(record["timestamp"])) < since:
            continue
        print(json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


def _parse_since(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


if __name__ == "__main__":
    raise SystemExit(main())
