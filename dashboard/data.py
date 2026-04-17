"""Data loading and shaping utilities for the Streamlit dashboard."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ActionRow:
    tick: int
    timestamp: str
    agent_id: str
    action_type: str
    target: str | None
    content: str
    location: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load newline-delimited JSON records from a simulation export."""

    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_number}: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL line {line_number} must be an object")
            records.append(payload)
    return records


def loads_jsonl(text: str) -> list[dict[str, Any]]:
    """Load newline-delimited JSON records from an uploaded file body."""

    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"JSONL line {line_number} must be an object")
        records.append(payload)
    return records


def normalize_log_records(records: list[dict[str, Any]]) -> list[ActionRow]:
    """Flatten simulator JSON records into dashboard-friendly action rows."""

    rows: list[ActionRow] = []
    for index, record in enumerate(records):
        action = record.get("action")
        if not isinstance(action, dict):
            raise ValueError(f"record {index} is missing an action object")
        rows.append(
            ActionRow(
                tick=_as_int(record.get("tick"), default=index),
                timestamp=str(record.get("timestamp") or action.get("timestamp") or ""),
                agent_id=str(record.get("agent_id") or action.get("agent_id") or ""),
                action_type=str(action.get("action_type") or "unknown"),
                target=_optional_string(action.get("target")),
                content=str(action.get("content") or ""),
                location=str(action.get("location") or record.get("location") or ""),
            )
        )
    return rows


def summarize_logs(rows: list[ActionRow]) -> dict[str, object]:
    """Return compact metrics for the dashboard header."""

    agents = {row.agent_id for row in rows}
    ticks = {row.tick for row in rows}
    timestamps = sorted(row.timestamp for row in rows if row.timestamp)
    action_counts = Counter(row.action_type for row in rows)
    agent_counts = Counter(row.agent_id for row in rows)
    return {
        "total_actions": len(rows),
        "agent_count": len(agents),
        "tick_count": len(ticks),
        "time_start": timestamps[0] if timestamps else "",
        "time_end": timestamps[-1] if timestamps else "",
        "action_counts": dict(action_counts.most_common()),
        "agent_counts": dict(agent_counts.most_common()),
    }


def filter_rows(
    rows: list[ActionRow],
    *,
    agent_id: str | None = None,
    search: str = "",
) -> list[ActionRow]:
    """Filter rows by agent and free-text search."""

    query = search.strip().lower()
    filtered = rows
    if agent_id and agent_id != "All":
        filtered = [row for row in filtered if row.agent_id == agent_id]
    if query:
        filtered = [
            row
            for row in filtered
            if query in row.content.lower()
            or query in row.action_type.lower()
            or query in (row.target or "").lower()
            or query in row.location.lower()
        ]
    return filtered


def rows_to_dicts(rows: list[ActionRow]) -> list[dict[str, object]]:
    return [row.to_dict() for row in rows]


def _optional_string(value: object) -> str | None:
    if value in {None, ""}:
        return None
    return str(value)


def _as_int(value: object, *, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
