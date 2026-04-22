"""Run the synthetic local proxy memory benchmark integration."""

from __future__ import annotations

from pathlib import Path

from luvoire.memory.external_benchmark_integration import (
    write_external_memory_benchmark_summary,
)

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
SUMMARY_PATH = RESULTS_DIR / "summary.json"


def main() -> None:
    write_external_memory_benchmark_summary(SUMMARY_PATH)


if __name__ == "__main__":
    main()
