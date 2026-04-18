"""Phase 42 tests for the deterministic 500-agent metropolis experiment."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path("experiments/500_agent_metropolis")


def test_phase42_experiment_files_exist() -> None:
    expected = [
        "config.yaml",
        "run.py",
        "README.md",
        "results/runs.jsonl",
        "results/summary.json",
        "results/latency_memory.svg",
    ]

    missing = [path for path in expected if not (ROOT / path).exists()]

    assert missing == []
    assert len(list((ROOT / "seeds").glob("seed_*.txt"))) == 20


def test_phase42_config_declares_five_hundred_agents() -> None:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

    assert config["scenario_name"] == "500_agent_metropolis_rush_hour"
    assert config["agent_count"] == 500
    assert config["ticks_per_run"] == 6
    assert len(config["districts"]) == 10


def test_phase42_results_match_committed_summary() -> None:
    rows = [
        json.loads(line)
        for line in (ROOT / "results/runs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    summary = json.loads((ROOT / "results/summary.json").read_text(encoding="utf-8"))

    assert len(rows) == 20
    assert summary["agent_count"] == 500
    assert summary["seed_count"] == 20
    assert summary["actions_per_seed"] == 3000
    assert summary["total_actions"] == 60000
    assert summary["latency_ms"]["mean_p95"] > 0
    assert summary["memory_mb"]["max_peak"] > 0
    assert summary["reproducibility"]["bit_for_bit_artifacts"] is True


def test_phase42_run_script_replays_bit_for_bit(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    command = [
        sys.executable,
        str(ROOT / "run.py"),
        "--output-dir",
        str(first),
    ]
    subprocess.run(command, check=True, text=True, capture_output=True)
    command[command.index(str(first))] = str(second)
    subprocess.run(command, check=True, text=True, capture_output=True)

    for filename in ["runs.jsonl", "summary.json", "latency_memory.svg"]:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()
