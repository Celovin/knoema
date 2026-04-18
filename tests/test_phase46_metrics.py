"""Phase 46 tests for PCS and RCS metrics."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from knoema.metrics import compute_pcs, compute_rcs, score_log

SCORING_ROOT = Path("benchmarks/scoring")


def test_phase46_metric_files_exist() -> None:
    expected = [
        "benchmarks/scoring/README.md",
        "benchmarks/scoring/runner.py",
        "benchmarks/scoring/results/metrics.json",
        "benchmarks/scoring/results/metrics.svg",
        "experiments/500_agent_metropolis/results/representative_log.jsonl",
    ]
    missing = [path for path in expected if not Path(path).exists()]
    assert missing == []


def test_phase46_metrics_hit_acceptance_targets() -> None:
    payload = json.loads((SCORING_ROOT / "results/metrics.json").read_text(encoding="utf-8"))

    assert payload["village_50"]["pcs_average"] >= 0.75
    assert payload["metropolis_500"]["rcs_average"] >= 0.70
    assert payload["acceptance"]["pcs_average_at_least_0_75"] is True
    assert payload["acceptance"]["rcs_average_at_least_0_70"] is True


def test_phase46_metric_edge_cases() -> None:
    empty: list[dict[str, object]] = []
    try:
        compute_pcs(empty, "agent-0")
    except ValueError:
        pass
    else:  # pragma: no cover - defensive branch
        raise AssertionError("empty log must raise ValueError")

    one_row = [
        {
            "agent_id": "agent-0",
            "action": {
                "action_type": "wait",
                "target": None,
                "content": "holds position",
                "location": "Lab",
            },
        }
    ]
    assert 0.0 <= compute_pcs(one_row, "agent-0") <= 1.0
    assert compute_rcs(one_row, "agent-0", "agent-0") == 0.0


def test_phase46_relationship_coherence_and_score_log_cover_pair_summaries(tmp_path: Path) -> None:
    rows = [
        {
            "agent_id": "agent-0",
            "action": {
                "action_type": "speak",
                "target": "agent-1",
                "content": "shares a stable plan with agent-1",
                "location": "Market",
            },
        },
        {
            "agent_id": "agent-1",
            "action": {
                "action_type": "speak",
                "target": "agent-0",
                "content": "shares a stable plan with agent-0",
                "location": "Market",
            },
        },
    ]

    assert compute_rcs(rows, "agent-0", "agent-1") == 1.0
    assert compute_rcs(rows, "agent-0", "agent-2") == 0.0

    try:
        compute_rcs(rows, "agent-0", " ")
    except ValueError:
        pass
    else:  # pragma: no cover - defensive branch
        raise AssertionError("blank agent id must raise ValueError")

    log_path = tmp_path / "pair_log.jsonl"
    log_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    summary = score_log(log_path)
    assert summary["agent_count"] == 2
    assert summary["rcs"]["pair_count"] == 1
    assert summary["rcs"]["sample"]["agent-0|agent-1"] == 1.0

    empty_path = tmp_path / "empty.jsonl"
    empty_path.write_text("", encoding="utf-8")
    try:
        score_log(empty_path)
    except ValueError:
        pass
    else:  # pragma: no cover - defensive branch
        raise AssertionError("empty score log must raise ValueError")


def test_phase46_cli_outputs_json_for_score_command() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "knoema.cli",
            "score",
            "experiments/50_agent_village/results/sim_log.jsonl",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["pcs"]["average"] >= 0.75
    assert payload["rcs"]["pair_count"] > 0
