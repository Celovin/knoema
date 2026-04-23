"""Analytics helpers for Parquet export and DuckDB queries."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypeAlias, cast

from luvoire.export.finetuning import RunLogInput, parse_run_log

AnalyticsRow: TypeAlias = dict[str, Any]

_EMPTY_ANALYTICS_COLUMNS: tuple[str, ...] = (
    "tick",
    "timestamp",
    "agent_id",
    "action_type",
    "target",
    "content",
    "location",
    "action_timestamp",
    "metadata_json",
    "raw_json",
)


def flatten_run_log(run_log: RunLogInput) -> list[AnalyticsRow]:
    """Flatten a Luvoire JSONL run log into analytics-friendly rows."""

    return [_flatten_row(row) for row in parse_run_log(run_log)]


def export_run_log_parquet(run_log: RunLogInput, destination: str | Path) -> Path:
    """Write a flattened Luvoire run log as a Parquet file."""

    pyarrow = _require_pyarrow()
    parquet_module = _require_pyarrow_parquet()
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = flatten_run_log(run_log)
    if rows:
        table = pyarrow.Table.from_pylist(rows)
    else:
        table = pyarrow.Table.from_pydict({column: [] for column in _EMPTY_ANALYTICS_COLUMNS})
    parquet_module.write_table(table, path)
    return path


def query_run_parquet(paths: Sequence[str | Path], sql: str) -> list[AnalyticsRow]:
    """Query one or more Parquet run artifacts through DuckDB as `runs`."""

    normalized_paths = [str(Path(path)) for path in paths]
    if not normalized_paths:
        raise ValueError("at least one parquet path is required")
    if not sql.strip():
        raise ValueError("sql must not be blank")
    duckdb = _require_duckdb()
    with duckdb.connect(database=":memory:") as connection:
        relation = connection.read_parquet(normalized_paths)
        relation.create_view("runs")
        cursor = connection.execute(sql)
        columns = [cast(str, description[0]) for description in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def _flatten_row(row: Mapping[str, Any]) -> AnalyticsRow:
    action = row.get("action")
    action_payload = dict(action) if isinstance(action, Mapping) else {}
    metadata = action_payload.get("metadata")
    metadata_json = None
    if isinstance(metadata, Mapping) and metadata:
        metadata_json = json.dumps(dict(metadata), ensure_ascii=False, sort_keys=True)
    raw_row = dict(row)
    return {
        "tick": int(row.get("tick", 0)),
        "timestamp": str(row.get("timestamp", "")),
        "agent_id": str(row.get("agent_id", "")),
        "action_type": str(action_payload.get("action_type", "")),
        "target": _string_or_none(action_payload.get("target")),
        "content": str(action_payload.get("content", "")),
        "location": str(action_payload.get("location", row.get("location", ""))),
        "action_timestamp": str(action_payload.get("timestamp", row.get("timestamp", ""))),
        "metadata_json": metadata_json,
        "raw_json": json.dumps(raw_row, ensure_ascii=False, sort_keys=True),
    }


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text != "" else None


def _require_duckdb() -> Any:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install luvoire-engine[analytics] to query Parquet analytics.") from exc
    return duckdb


def _require_pyarrow() -> Any:
    try:
        import pyarrow  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install luvoire-engine[analytics] to export Parquet analytics.") from exc
    return pyarrow


def _require_pyarrow_parquet() -> Any:
    try:
        import pyarrow.parquet as parquet  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install luvoire-engine[analytics] to export Parquet analytics.") from exc
    return parquet


__all__ = ["export_run_log_parquet", "flatten_run_log", "query_run_parquet"]
