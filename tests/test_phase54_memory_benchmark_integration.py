from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from luvoire.memory.external_benchmark_integration import (
    run_external_memory_benchmark_integration,
)


def test_phase54_memory_benchmark_integration_covers_three_named_suites() -> None:
    result = run_external_memory_benchmark_integration()

    assert [row.benchmark_id for row in result.rows] == [
        "locomo",
        "memoryagentbench",
        "memoryarena",
    ]
    assert all(row.passed for row in result.rows)


def test_phase54_memoryarena_meets_sixty_percent_target() -> None:
    result = run_external_memory_benchmark_integration()
    memoryarena = next(row for row in result.rows if row.benchmark_id == "memoryarena")

    assert memoryarena.target == 0.6
    assert memoryarena.score >= 0.6
    assert "synthetic local proxy" in memoryarena.evaluation_mode


def test_phase54_benchmark_labels_disclose_proxy_status() -> None:
    result = run_external_memory_benchmark_integration()

    assert all("proxy" in row.benchmark_label.lower() for row in result.rows)
    assert all("inspired" in row.benchmark_label.lower() for row in result.rows)


def test_phase54_memory_benchmark_script_writes_summary() -> None:
    subprocess.run(
        [sys.executable, "benchmarks/memory_benchmark_integration/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    summary = json.loads(
        Path("benchmarks/memory_benchmark_integration/results/summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert {row["benchmark_id"] for row in summary["rows"]} == {
        "locomo",
        "memoryagentbench",
        "memoryarena",
    }
    assert next(row for row in summary["rows"] if row["benchmark_id"] == "memoryarena")[
        "score"
    ] >= 0.6
