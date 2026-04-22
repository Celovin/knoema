from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_HISTORY_PATH = Path("site-snapshot/status-history.jsonl")
DEFAULT_OUTPUT_PATH = Path("site-snapshot/uptime.json")
UP_STATES = {"RUNNING", "success", "verified"}
WINDOWS = (7, 30, 90)
COMPONENTS = (
    ("space", "HF Space"),
    ("ci", "CI"),
    ("replay_artifacts", "Replay artifacts"),
)


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def load_history(history_path: Path = DEFAULT_HISTORY_PATH) -> list[dict[str, object]]:
    if not history_path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(history_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"invalid history row at line {line_number}")
        rows.append(payload)
    return rows


def compute_uptime(history: Sequence[Mapping[str, object]]) -> dict[str, object]:
    valid_history = [
        row
        for row in history
        if isinstance(row.get("timestamp"), str)
    ]
    if not valid_history:
        return {
            "components": {
                name: {"label": label, "windows": _empty_windows()}
                for name, label in COMPONENTS
            },
            "generated_at": datetime.now(UTC).isoformat(),
            "sample_count": 0,
        }
    sorted_history = sorted(valid_history, key=lambda row: str(row["timestamp"]))
    now = parse_timestamp(str(sorted_history[-1]["timestamp"]))
    return {
        "components": {
            name: {
                "label": label,
                "windows": {
                    f"{days}d": _window_uptime(sorted_history, component=name, now=now, days=days)
                    for days in WINDOWS
                },
            }
            for name, label in COMPONENTS
        },
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "sample_count": len(sorted_history),
    }


def write_uptime(
    history_path: Path = DEFAULT_HISTORY_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> dict[str, object]:
    payload = compute_uptime(load_history(history_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _window_uptime(
    history: Sequence[Mapping[str, object]],
    *,
    component: str,
    now: datetime,
    days: int,
) -> dict[str, object]:
    cutoff = now - timedelta(days=days)
    rows = [
        row
        for row in history
        if parse_timestamp(str(row["timestamp"])) >= cutoff
    ]
    if not rows:
        return {"insufficient_data": True, "sample_count": 0, "window_days": days}
    first = parse_timestamp(str(rows[0]["timestamp"]))
    if now - first < timedelta(days=7):
        return {
            "insufficient_data": True,
            "sample_count": len(rows),
            "window_days": days,
        }
    up_count = sum(1 for row in rows if _component_status(row, component) in UP_STATES)
    return {
        "insufficient_data": False,
        "sample_count": len(rows),
        "up_samples": up_count,
        "uptime_percent": round((up_count / len(rows)) * 100, 3),
        "window_days": days,
    }


def _empty_windows() -> dict[str, dict[str, object]]:
    return {
        f"{days}d": {"insufficient_data": True, "sample_count": 0, "window_days": days}
        for days in WINDOWS
    }


def _component_status(row: Mapping[str, object], component: str) -> str:
    if component == "space":
        return str(row.get("space_stage") or "UNKNOWN")
    if component == "ci":
        return str(row.get("ci_state") or "unknown")
    if component == "replay_artifacts":
        return "verified" if bool(row.get("replay_verified")) else "failed"
    raise ValueError(f"unknown component: {component}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute rolling uptime from status history.")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    write_uptime(args.history, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
