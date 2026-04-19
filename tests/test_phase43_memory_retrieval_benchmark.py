from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from knoema.memory.retrieval_benchmark import run_memory_retrieval_benchmark


def test_phase43_memory_retrieval_benchmark_meets_recall_gate() -> None:
    result = run_memory_retrieval_benchmark()

    assert result.passed is True
    assert result.average_recall_at_5 >= 0.85
    assert len(result.per_agent) == 2
    assert all(agent.recall_at_5 >= 0.85 for agent in result.per_agent)


def test_phase43_memory_retrieval_benchmark_is_reproducible() -> None:
    first = run_memory_retrieval_benchmark().to_json_dict()
    second = run_memory_retrieval_benchmark().to_json_dict()

    assert first == second


def test_phase43_memory_retrieval_script_writes_summary() -> None:
    subprocess.run(
        [sys.executable, "experiments/memory_retrieval_benchmark/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    summary = json.loads(
        Path("experiments/memory_retrieval_benchmark/results/summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["average_recall_at_5"] >= 0.85
    assert summary["passed"] is True
    assert {agent["agent_id"] for agent in summary["per_agent"]} == {"agent_alpha", "agent_beta"}
