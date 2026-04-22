from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("benchmarks/cross_framework")


def test_phase57_cross_framework_files_exist() -> None:
    expected = [
        "framework_specs.json",
        "run_comparison.py",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
        "results/summary.json",
        "results/summary.md",
    ]

    for relative_path in expected:
        assert (ROOT / relative_path).exists()


def test_phase57_runner_recreates_summary_and_acceptance() -> None:
    result = subprocess.run(
        [sys.executable, "benchmarks/cross_framework/run_comparison.py"],
        check=True,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    cli_payload = json.loads(result.stdout)
    summary = json.loads((ROOT / "results/summary.json").read_text(encoding="utf-8"))

    assert cli_payload["rows"] == 6
    assert summary["scenario"] == "5-agent dormitory over 7 days"
    assert summary["row_count"] == 6
    assert all(summary["acceptance"].values())


def test_phase57_summary_table_has_six_frameworks_and_required_columns() -> None:
    summary_md = (ROOT / "results/summary.md").read_text(encoding="utf-8")

    for column in [
        "Framework",
        "Throughput",
        "Memory Footprint",
        "PCS",
        "Reproducibility",
        "Code Lines to Configure",
        "License",
    ]:
        assert column in summary_md

    for framework in ["Luvoire", "AutoGen", "CrewAI", "LangGraph", "Mesa", "NetLogo"]:
        assert f"| {framework} |" in summary_md


def test_phase57_luvoire_rank_and_code_line_acceptance() -> None:
    summary = json.loads((ROOT / "results/summary.json").read_text(encoding="utf-8"))
    rows = {row["framework"]: row for row in summary["rows"]}

    assert rows["Luvoire"]["persona_consistency_score"] == max(
        row["persona_consistency_score"] for row in summary["rows"]
    )
    assert rows["Luvoire"]["reproducibility_score"] == max(
        row["reproducibility_score"] for row in summary["rows"]
    )
    assert rows["Luvoire"]["code_lines_to_configure"] <= (
        rows["AutoGen"]["code_lines_to_configure"] * 0.5
    )
    assert rows["Luvoire"]["code_lines_to_configure"] <= (
        rows["CrewAI"]["code_lines_to_configure"] * 0.5
    )


def test_phase57_docs_and_paper_are_linked() -> None:
    assert "Cross-Framework Benchmark: benchmarks/cross_framework.md" in Path(
        "mkdocs.yml"
    ).read_text(encoding="utf-8")
    assert "Cross-framework comparison appendix" in Path(
        "paper/sections/02_related_work.tex"
    ).read_text(encoding="utf-8")
    assert (
        "cross-framework comparison benchmark"
        in Path("README.md").read_text(encoding="utf-8").lower()
    )
