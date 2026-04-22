"""Convert Knoema run logs into fine-tuning JSONL datasets."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast

FineTuningFormat: TypeAlias = Literal["openai", "anthropic", "dpo"]
RunLogInput: TypeAlias = str | Path | Sequence[Mapping[str, Any]]


def parse_run_log(run_log: RunLogInput) -> list[dict[str, Any]]:
    """Parse a Knoema JSONL log or normalize an in-memory row sequence."""

    if isinstance(run_log, Path):
        return _parse_jsonl_text(run_log.read_text(encoding="utf-8"))
    if isinstance(run_log, str):
        return _parse_jsonl_text(run_log)
    return [dict(row) for row in run_log]


def to_openai_jsonl(run_log: RunLogInput) -> list[dict[str, Any]]:
    """Return OpenAI chat fine-tuning rows from a Knoema run log."""

    records: list[dict[str, Any]] = []
    for row in _action_rows(parse_run_log(run_log)):
        records.append(
            {
                "messages": [
                    {"role": "system", "content": _system_prompt(row)},
                    {"role": "user", "content": _user_context(row)},
                    {"role": "assistant", "content": _assistant_content(row)},
                ],
                "metadata": _metadata(row),
            }
        )
    return records


def to_anthropic_jsonl(run_log: RunLogInput) -> list[dict[str, Any]]:
    """Return Anthropic-style chat JSONL rows from a Knoema run log."""

    records: list[dict[str, Any]] = []
    for row in _action_rows(parse_run_log(run_log)):
        records.append(
            {
                "system": _system_prompt(row),
                "messages": [
                    {"role": "user", "content": _user_context(row)},
                    {"role": "assistant", "content": _assistant_content(row)},
                ],
                "metadata": _metadata(row),
            }
        )
    return records


def to_dpo_pairs(
    preferred_run_log: RunLogInput,
    rejected_run_log: RunLogInput,
) -> list[dict[str, Any]]:
    """Return preference pairs by matching rows on `(tick, agent_id)`."""

    preferred_rows = _action_rows(parse_run_log(preferred_run_log))
    rejected_by_key = {_row_key(row): row for row in _action_rows(parse_run_log(rejected_run_log))}
    pairs: list[dict[str, Any]] = []
    for preferred in preferred_rows:
        rejected = rejected_by_key.get(_row_key(preferred))
        if rejected is None:
            continue
        chosen = _assistant_content(preferred)
        rejected_content = _assistant_content(rejected)
        if chosen == rejected_content:
            continue
        pairs.append(
            {
                "messages": [
                    {"role": "system", "content": _system_prompt(preferred)},
                    {"role": "user", "content": _user_context(preferred)},
                ],
                "chosen": [{"role": "assistant", "content": chosen}],
                "rejected": [{"role": "assistant", "content": rejected_content}],
                "metadata": {
                    **_metadata(preferred),
                    "rejected_action_type": _action_type(rejected),
                },
            }
        )
    return pairs


def export_finetuning_jsonl(
    run_log: RunLogInput,
    export_format: str,
    *,
    rejected_run_log: RunLogInput | None = None,
) -> str:
    """Serialize a fine-tuning export as JSONL text."""

    normalized = _normalize_format(export_format)
    if normalized == "openai":
        records = to_openai_jsonl(run_log)
    elif normalized == "anthropic":
        records = to_anthropic_jsonl(run_log)
    else:
        records = to_dpo_pairs(run_log, rejected_run_log or _baseline_rejected_rows(run_log))
    return _records_to_jsonl(records)


def write_finetuning_jsonl(
    run_log: RunLogInput,
    destination: str | Path,
    export_format: str,
    *,
    rejected_run_log: RunLogInput | None = None,
) -> Path:
    """Write a fine-tuning JSONL file and return its path."""

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        export_finetuning_jsonl(
            run_log,
            export_format,
            rejected_run_log=rejected_run_log,
        ),
        encoding="utf-8",
    )
    return path


def _parse_jsonl_text(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(cast("dict[str, Any]", payload))
    return rows


def _records_to_jsonl(records: Sequence[Mapping[str, Any]]) -> str:
    if not records:
        return ""
    return "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n"


def _action_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in rows
        if isinstance(row.get("action"), dict) and str(row.get("agent_id", "")).strip()
    ]


def _row_key(row: Mapping[str, Any]) -> tuple[int, str]:
    return int(row.get("tick", 0)), str(row.get("agent_id", "agent"))


def _action(row: Mapping[str, Any]) -> dict[str, Any]:
    action = row.get("action", {})
    return dict(action) if isinstance(action, Mapping) else {}


def _action_type(row: Mapping[str, Any]) -> str:
    return str(_action(row).get("action_type", "observe")).strip() or "observe"


def _metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    tick, agent_id = _row_key(row)
    action = _action(row)
    return {
        "agent_id": agent_id,
        "tick": tick,
        "timestamp": str(row.get("timestamp", action.get("timestamp", ""))),
        "action_type": _action_type(row),
    }


def _system_prompt(row: Mapping[str, Any]) -> str:
    agent_id = _row_key(row)[1]
    return (
        f"You are {agent_id}, a Knoema simulation agent. "
        "Respond only with a JSON action containing action_type, target, content, and location."
    )


def _user_context(row: Mapping[str, Any]) -> str:
    action = _action(row)
    tick, agent_id = _row_key(row)
    timestamp = str(row.get("timestamp", action.get("timestamp", "")))
    location = str(action.get("location", row.get("location", "unknown")))
    target = action.get("target")
    target_text = str(target) if target is not None else "none"
    return "\n".join(
        [
            f"tick: {tick}",
            f"timestamp: {timestamp}",
            f"agent_id: {agent_id}",
            f"location: {location}",
            f"current_target: {target_text}",
            "Choose the next social action for this agent.",
        ]
    )


def _assistant_content(row: Mapping[str, Any]) -> str:
    action = _action(row)
    payload: dict[str, Any] = {
        "action_type": _action_type(row),
        "target": action.get("target"),
        "content": str(action.get("content", "")).strip(),
        "location": str(action.get("location", row.get("location", "unknown"))),
    }
    metadata = action.get("metadata")
    if isinstance(metadata, Mapping) and metadata:
        payload["metadata"] = dict(metadata)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _baseline_rejected_rows(run_log: RunLogInput) -> list[dict[str, Any]]:
    rows = _action_rows(parse_run_log(run_log))
    rejected_rows: list[dict[str, Any]] = []
    for row in rows:
        action = _action(row)
        rejected = dict(row)
        rejected["action"] = {
            "action_type": "wait",
            "target": None,
            "content": "No context-specific action.",
            "location": str(action.get("location", row.get("location", "unknown"))),
        }
        rejected_rows.append(rejected)
    return rejected_rows


def _normalize_format(export_format: str) -> FineTuningFormat:
    value = export_format.strip().lower().replace("_", "-")
    if value in {"openai", "openai-chat", "openai jsonl", "openai chat jsonl"}:
        return "openai"
    if value in {"anthropic", "claude", "anthropic jsonl", "anthropic chat jsonl"}:
        return "anthropic"
    if value in {"dpo", "dpo-pairs", "preference", "preference pairs"}:
        return "dpo"
    raise ValueError(f"unsupported fine-tuning export format: {export_format}")
