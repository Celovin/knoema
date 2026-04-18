"""Phase 19 tests for the deterministic 50-agent village experiment."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path("experiments/50_agent_village")


def test_phase19_experiment_files_exist() -> None:
    expected = [
        "config.yaml",
        "run.py",
        "README.md",
        "analysis.ipynb",
        "results/sim_log.jsonl",
        "results/metrics.json",
        "results/trace_sample.json",
    ]

    missing = [path for path in expected if not (ROOT / path).exists()]

    assert missing == []
    assert Path("docs/reports/50_agent_benchmark.pdf").exists()


def test_phase19_config_defines_fifty_synthetic_agents() -> None:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

    assert config["scenario_name"] == "50_agent_village_week"
    assert config["duration_days"] == 7
    assert config["tick_duration_minutes"] == 240
    assert len(config["agent_roster"]) == 50


def test_phase19_metrics_match_committed_log() -> None:
    metrics = json.loads((ROOT / "results/metrics.json").read_text(encoding="utf-8"))
    log_lines = (ROOT / "results/sim_log.jsonl").read_text(encoding="utf-8").splitlines()
    trace = json.loads((ROOT / "results/trace_sample.json").read_text(encoding="utf-8"))

    assert metrics["agent_count"] == 50
    assert metrics["tick_count"] == 42
    assert metrics["action_count"] == 2100
    assert len(log_lines) == metrics["action_count"]
    assert len(trace) == 50
    assert metrics["reproducibility"]["bit_for_bit_artifacts"] is True
    assert metrics["cost_estimate"]["usd"] == 0.0


def test_phase19_run_script_replays_bit_for_bit(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    command = [
        sys.executable,
        str(ROOT / "run.py"),
        "--output-dir",
        str(first),
        "--skip-pdf",
    ]
    subprocess.run(command, check=True, text=True, capture_output=True)
    command[command.index(str(first))] = str(second)
    subprocess.run(command, check=True, text=True, capture_output=True)

    for filename in ["sim_log.jsonl", "metrics.json", "trace_sample.json"]:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()
