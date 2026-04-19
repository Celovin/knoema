"""Run the deterministic MLMF retention benchmark."""

from __future__ import annotations

from pathlib import Path

from knoema.memory.multi_layer import write_mlmf_retention_benchmark_summary

SUMMARY_PATH = Path("experiments/mlmf_retention_benchmark/results/summary.json")


def main() -> None:
    result = write_mlmf_retention_benchmark_summary(SUMMARY_PATH)
    print(
        "MLMF retention="
        f"{result.measured_retention:.3f} "
        f"(baseline {result.published_baseline:.3f})"
    )


if __name__ == "__main__":
    main()
