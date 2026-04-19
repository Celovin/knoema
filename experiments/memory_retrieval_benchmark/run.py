"""Run the deterministic memory retrieval benchmark."""

from __future__ import annotations

from pathlib import Path

from knoema.memory.retrieval_benchmark import write_memory_retrieval_benchmark_summary

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
SUMMARY_PATH = RESULTS_DIR / "summary.json"


def main() -> None:
    write_memory_retrieval_benchmark_summary(SUMMARY_PATH)


if __name__ == "__main__":
    main()
