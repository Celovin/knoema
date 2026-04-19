"""Measure replay and OpenAI playground tick latency for the formal report."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from latency_comparison import write_latency_comparison_report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure playground tick latency.")
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path(__file__).resolve().parent / "results" / "latency_comparison.json",
    )
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--scenario-name", default="Dorm: two agents")
    parser.add_argument("--ticks", type=int, default=2)
    parser.add_argument("--repetitions", type=int, default=2)
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = write_latency_comparison_report(
        args.output_path,
        model=args.model,
        scenario_name=args.scenario_name,
        ticks=args.ticks,
        repetitions=args.repetitions,
    )
    print(json.dumps(report.to_json_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
