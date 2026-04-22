from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = (
    ROOT / "dist" / "didimdol_onepager_ko.pdf",
    ROOT / "dist" / "didimdol_onepager_en.pdf",
)


def _run_builder() -> None:
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = "0"
    subprocess.run(
        [sys.executable, "scripts/build_grant_summary.py"],
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


def test_build_grant_summary_outputs_two_single_page_pdfs() -> None:
    _run_builder()

    for pdf_path in OUTPUTS:
        assert pdf_path.exists(), pdf_path
        assert 50_000 <= pdf_path.stat().st_size <= 400_000
        reader = PdfReader(pdf_path)
        assert len(reader.pages) == 1


def test_build_grant_summary_is_deterministic_with_fixed_source_date_epoch() -> None:
    _run_builder()
    first = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUTS}
    _run_builder()
    second = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in OUTPUTS}

    assert first == second


def test_build_grant_summary_text_has_source_citations_and_matching_values() -> None:
    _run_builder()
    extracted = "\n".join(
        (page.extract_text() or "")
        for pdf_path in OUTPUTS
        for page in PdfReader(pdf_path).pages
    )

    for value in ("1.000 / target 0.800", "1.000 / target 0.600", "7642.50", "13.085"):
        assert value in extracted
    assert "benchmarks/memory_benchmark_integration/results/summary.json rows[0].score,target" in extracted
    assert "benchmarks/city_scale_1k_report.md lines" in extracted
    assert extracted.count("arXiv:<pending>") == 2
