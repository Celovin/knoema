from __future__ import annotations

import json
import subprocess
import sys

from knoema.benchmark import BenchmarkConfig, format_markdown_report, run_knoema_benchmark


def test_phase14_benchmark_report_records_expected_actions() -> None:
    config = BenchmarkConfig(agent_count=3, duration_days=1, tick_minutes=360, repetitions=1)

    report = run_knoema_benchmark(config)

    assert report.action_count == 12
    assert report.config.expected_action_count == 12
    assert report.runs[0].actions_per_second > 0
    assert report.runs[0].relationship_edges >= 3


def test_phase14_benchmark_markdown_keeps_external_comparison_slots() -> None:
    report = run_knoema_benchmark(
        BenchmarkConfig(agent_count=2, duration_days=1, tick_minutes=360, repetitions=1)
    )

    markdown = format_markdown_report(report)

    assert "| Knoema | measured |" in markdown
    assert "| Concordia | not-measured |" in markdown
    assert "| Mesa | not-measured |" in markdown


def test_phase14_benchmark_script_writes_json_and_markdown(tmp_path) -> None:  # type: ignore[no-untyped-def]
    json_path = tmp_path / "benchmark.json"
    markdown_path = tmp_path / "benchmark.md"

    subprocess.run(
        [
            sys.executable,
            "benchmarks/run_benchmark.py",
            "--agents",
            "2",
            "--duration-days",
            "1",
            "--tick-minutes",
            "360",
            "--repetitions",
            "1",
            "--json-output",
            str(json_path),
            "--markdown-output",
            str(markdown_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert payload["engine"] == "Knoema"
    assert payload["summary"]["action_count"] == 8
    assert "Framework Comparison" in markdown
