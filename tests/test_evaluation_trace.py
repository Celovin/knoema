from __future__ import annotations

import json
from pathlib import Path

from luvoire.cli import main
from luvoire.evaluation import grade_trace_report


def _trace_jsonl(action_types: list[str]) -> str:
    rows = []
    for tick, action_type in enumerate(action_types):
        rows.append(
            {
                "tick": tick,
                "timestamp": f"2026-04-23T09:{tick:02d}:00",
                "agent_id": "agent-0" if tick % 2 == 0 else "agent-1",
                "action": {
                    "action_type": action_type,
                    "target": "agent-1" if action_type == "speak" else None,
                    "content": f"{action_type} content",
                    "location": "Room 201",
                    "timestamp": f"2026-04-23T09:{tick:02d}:00",
                },
            }
        )
    return "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"


def test_grade_trace_report_scores_varied_trace_above_gate() -> None:
    report = grade_trace_report(_trace_jsonl(["speak", "observe", "help", "wait"]), trace_id="demo")

    assert report.trace_id == "demo"
    assert report.item_count == 4
    assert report.passes_default_gate is True
    assert report.weighted_score >= 0.65
    assert {criterion.name for criterion in report.criteria} == {
        "structural_validity",
        "timeline_continuity",
        "interaction_richness",
        "behavioral_variety",
    }


def test_cli_evaluate_trace_reports_json(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    trace_path = tmp_path / "trace.jsonl"
    trace_path.write_text(_trace_jsonl(["observe", "observe", "observe"]), encoding="utf-8")

    exit_code = main(["evaluate", "trace", str(trace_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["trace_id"] == "trace"
    assert payload["item_count"] == 3
    assert payload["criteria"][0]["name"] == "structural_validity"
