from __future__ import annotations

import json
from pathlib import Path

from luvoire.cli import main
from luvoire.export import export_run_log_parquet, flatten_run_log, query_run_parquet


def _sample_run_log() -> str:
    rows = [
        {
            "tick": 0,
            "timestamp": "2026-04-23T09:00:00",
            "agent_id": "mina",
            "action": {
                "action_type": "speak",
                "target": "jiho",
                "content": "Good morning.",
                "location": "Dorm Room 201",
                "timestamp": "2026-04-23T09:00:00",
                "metadata": {"sentiment": "positive"},
            },
        },
        {
            "tick": 1,
            "timestamp": "2026-04-23T09:30:00",
            "agent_id": "jiho",
            "action": {
                "action_type": "observe",
                "target": None,
                "content": "Looks at the notes on the desk.",
                "location": "Dorm Room 201",
                "timestamp": "2026-04-23T09:30:00",
            },
        },
    ]
    return "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n"


def test_flatten_run_log_preserves_core_fields() -> None:
    rows = flatten_run_log(_sample_run_log())

    assert len(rows) == 2
    assert rows[0]["agent_id"] == "mina"
    assert rows[0]["action_type"] == "speak"
    assert rows[0]["metadata_json"] == '{"sentiment": "positive"}'
    assert rows[1]["target"] is None


def test_export_run_log_parquet_and_query(tmp_path: Path) -> None:
    run_log = tmp_path / "run.jsonl"
    parquet_path = tmp_path / "analytics" / "run.parquet"
    run_log.write_text(_sample_run_log(), encoding="utf-8")

    written = export_run_log_parquet(run_log, parquet_path)
    rows = query_run_parquet(
        [written],
        "SELECT agent_id, action_type, tick FROM runs ORDER BY tick ASC",
    )

    assert written == parquet_path
    assert parquet_path.exists()
    assert rows == [
        {"agent_id": "mina", "action_type": "speak", "tick": 0},
        {"agent_id": "jiho", "action_type": "observe", "tick": 1},
    ]


def test_cli_exports_and_queries_analytics_parquet(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    run_log = tmp_path / "run.jsonl"
    parquet_path = tmp_path / "run.parquet"
    run_log.write_text(_sample_run_log(), encoding="utf-8")

    export_exit = main(["export", "parquet", str(run_log), "--out", str(parquet_path)])
    export_output = capsys.readouterr().out
    query_exit = main(
        [
            "query",
            "runs",
            str(parquet_path),
            "--sql",
            "SELECT COUNT(*) AS row_count FROM runs",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert export_exit == 0
    assert "Wrote analytics parquet" in export_output
    assert query_exit == 0
    assert payload == [{"row_count": 2}]
