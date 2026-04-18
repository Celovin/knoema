"""Phase 20 tests for the formal benchmark report bundle."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("benchmarks/formal_report")


def test_phase20_formal_report_files_exist() -> None:
    expected = [
        "README.md",
        "runner.py",
        "scenarios/scenario_A_memory_recall.py",
        "scenarios/scenario_B_relationship_dynamics.py",
        "scenarios/scenario_C_narrative_branching.py",
        "scenarios/scenario_D_scalability.py",
        "baselines/naive_llm.py",
        "baselines/mesa_stub.py",
        "baselines/concordia_reference.md",
        "baselines/stanford_reference.md",
        "results/raw.jsonl",
        "results/summary.md",
        "results/figures/memory_recall.svg",
        "results/figures/token_efficiency.svg",
        "results/figures/scalability.svg",
        "results/figures/branching.svg",
        "results/figures/metropolis_scale.svg",
        "report.pdf",
    ]

    missing = [path for path in expected if not (ROOT / path).exists()]

    assert missing == []


def test_phase20_raw_matrix_has_twenty_four_runs() -> None:
    rows = _raw_rows()

    assert len(rows) == 24
    assert {row["scenario_id"] for row in rows} == {"A", "B", "C", "D"}
    assert {row["approach"] for row in rows} == {"knoema", "naive_llm"}
    assert {row["model_profile"] for row in rows} == {
        "local-large",
        "local-medium",
        "local-small",
    }
    assert all(row["prompt_tokens"] > row["completion_tokens"] for row in rows)
    assert all(row["memory_recall_top_k"] > 0 for row in rows)


def test_phase20_summary_records_statistics_and_baseline_discipline() -> None:
    summary = (ROOT / "results/summary.md").read_text(encoding="utf-8")

    assert "| Scenario | Approach | Recall@k | Token efficiency |" in summary
    assert "Paired sign-test p-value: 0.000244" in summary
    assert "Mesa stub status: not-measured" in summary
    assert "Concordia is documented as an external reference" in summary
    assert "Stanford Generative Agents is documented as an external reference" in summary
    assert "Knoema 500-Agent Metropolis" in summary
    assert "results/figures/metropolis_scale.svg" in summary
    assert "Sally-Anne reproduction" in summary
    assert "Theory-of-mind source" in summary
    assert "Classic Reproductions" in summary
    assert "Schelling threshold 0.3" in summary
    assert "Axelrod cooperative leader" in summary


def test_phase20_report_pdf_has_twenty_pages() -> None:
    payload = (ROOT / "report.pdf").read_bytes()

    assert payload.startswith(b"%PDF")
    assert payload.count(b"/Type /Page") - payload.count(b"/Type /Pages") == 20


def test_phase20_runner_regenerates_deterministic_text_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "formal_results"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "runner.py"),
            "--output-dir",
            str(output_dir),
            "--skip-pdf",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    for relative_path in [
        "raw.jsonl",
        "summary.md",
        "figures/memory_recall.svg",
        "figures/token_efficiency.svg",
        "figures/scalability.svg",
        "figures/branching.svg",
        "figures/metropolis_scale.svg",
    ]:
        assert (output_dir / relative_path).read_bytes() == (
            ROOT / "results" / relative_path
        ).read_bytes()


def _raw_rows() -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in (ROOT / "results/raw.jsonl").read_text(encoding="utf-8").splitlines()
    ]
