"""Phase 45 tests for classic ABM reproductions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCHELLING_ROOT = Path("experiments/schelling_segregation")
AXELROD_ROOT = Path("experiments/axelrod_prisoners_dilemma")


def test_phase45_schelling_files_exist() -> None:
    expected = [
        "README.md",
        "config.yaml",
        "run.py",
        "results/runs.jsonl",
        "results/summary.json",
        "results/segregation_curve.svg",
    ]
    missing = [path for path in expected if not (SCHELLING_ROOT / path).exists()]
    assert missing == []


def test_phase45_schelling_summary_hits_expected_bands() -> None:
    summary = json.loads((SCHELLING_ROOT / "results/summary.json").read_text(encoding="utf-8"))

    assert summary["grid_size"] == 50
    assert summary["agent_count"] == 2000
    assert summary["deterministic_alignment"]["threshold_0.3_in_expected_band"] is True
    assert summary["deterministic_alignment"]["threshold_0.7_in_expected_band"] is True
    assert summary["deterministic_results"]["0.3"]["segregation_index"] >= 0.45
    assert summary["deterministic_results"]["0.7"]["segregation_index"] >= 0.90


def test_phase45_schelling_run_script_reproduces_committed_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "schelling_results"
    subprocess.run(
        [
            sys.executable,
            str(SCHELLING_ROOT / "run.py"),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    for relative_path in [
        "runs.jsonl",
        "summary.json",
        "segregation_curve.svg",
    ]:
        assert (output_dir / relative_path).read_bytes() == (
            SCHELLING_ROOT / "results" / relative_path
        ).read_bytes()


def test_phase45_axelrod_files_exist() -> None:
    expected = [
        "README.md",
        "config.yaml",
        "run.py",
        "results/runs.jsonl",
        "results/summary.json",
        "results/scoreboard.svg",
    ]
    missing = [path for path in expected if not (AXELROD_ROOT / path).exists()]
    assert missing == []


def test_phase45_axelrod_summary_keeps_tit_for_tat_in_top_three() -> None:
    summary = json.loads((AXELROD_ROOT / "results/summary.json").read_text(encoding="utf-8"))

    assert summary["rounds"] == 200
    assert summary["strategy_count"] == 10
    assert summary["deterministic_alignment"]["tit_for_tat_in_top_three"] is True
    assert summary["deterministic_alignment"]["tit_for_tat_rank"] <= 3
    assert summary["cooperative_leaders"]["deterministic"]["strategy"] == "Tit for Tat"


def test_phase45_axelrod_run_script_reproduces_committed_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "axelrod_results"
    subprocess.run(
        [
            sys.executable,
            str(AXELROD_ROOT / "run.py"),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    for relative_path in [
        "runs.jsonl",
        "summary.json",
        "scoreboard.svg",
    ]:
        assert (output_dir / relative_path).read_bytes() == (
            AXELROD_ROOT / "results" / relative_path
        ).read_bytes()
