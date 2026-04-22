from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.build_status_page import sla_badge_class
from scripts.compute_uptime import compute_uptime, write_uptime


def _row(timestamp: datetime, *, ci_state: str = "success") -> dict[str, object]:
    return {
        "ci_state": ci_state,
        "replay_verified": True,
        "space_stage": "RUNNING",
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
    }


def test_uptime_one_fifteen_minute_outage_in_thirty_days() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [
        _row(start + timedelta(minutes=15 * index), ci_state="failure" if index == 120 else "success")
        for index in range(30 * 24 * 4)
    ]

    payload = compute_uptime(rows)
    ci_30d = payload["components"]["ci"]["windows"]["30d"]  # type: ignore[index]

    assert ci_30d["insufficient_data"] is False
    assert ci_30d["uptime_percent"] == 99.965


def test_sparse_history_reports_insufficient_data() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    rows = [_row(start + timedelta(hours=12 * index)) for index in range(6)]

    payload = compute_uptime(rows)
    space_30d = payload["components"]["space"]["windows"]["30d"]  # type: ignore[index]

    assert space_30d["insufficient_data"] is True
    assert "uptime_percent" not in space_30d


def test_sla_badge_boundaries() -> None:
    assert sla_badge_class({"insufficient_data": False, "uptime_percent": 99.9}) == "green"
    assert sla_badge_class({"insufficient_data": False, "uptime_percent": 99.5}) == "amber"
    assert sla_badge_class({"insufficient_data": False, "uptime_percent": 99.499}) == "red"
    assert sla_badge_class({"insufficient_data": True}) == "gray"


def test_uptime_output_is_deterministic(tmp_path: Path) -> None:
    history = tmp_path / "history.jsonl"
    first_output = tmp_path / "uptime_a.json"
    second_output = tmp_path / "uptime_b.json"
    start = datetime(2026, 1, 1, tzinfo=UTC)
    history.write_text(
        "\n".join(json.dumps(_row(start + timedelta(days=index)), sort_keys=True) for index in range(8))
        + "\n",
        encoding="utf-8",
    )

    write_uptime(history, first_output)
    write_uptime(history, second_output)

    assert first_output.read_bytes() == second_output.read_bytes()
