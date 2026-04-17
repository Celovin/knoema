"""Run the Knoema deterministic simulation benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from knoema.benchmark import BenchmarkConfig, format_markdown_report, run_knoema_benchmark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Knoema village benchmark.")
    parser.add_argument("--agents", type=int, default=10, help="Number of simulated agents.")
    parser.add_argument("--duration-days", type=int, default=1, help="Simulation duration in days.")
    parser.add_argument("--tick-minutes", type=int, default=60, help="Minutes per simulation tick.")
    parser.add_argument("--repetitions", type=int, default=3, help="Number of timed repetitions.")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path for the JSON benchmark report.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=None,
        help="Optional path for the Markdown benchmark report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = BenchmarkConfig(
        agent_count=args.agents,
        duration_days=args.duration_days,
        tick_minutes=args.tick_minutes,
        repetitions=args.repetitions,
        scenario_name=f"village-{args.agents}-agents-{args.tick_minutes}m",
    )
    report = run_knoema_benchmark(config)
    json_text = json.dumps(report.to_json_dict(), indent=2)
    markdown_text = format_markdown_report(report)

    if args.json_output is not None:
        _write_text(args.json_output, json_text + "\n")
    else:
        print(json_text)

    if args.markdown_output is not None:
        _write_text(args.markdown_output, markdown_text)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
