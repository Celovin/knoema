"""Run the deterministic 5K-agent city-scale benchmark on a 40x40 grid."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

from knoema.scaling import CityScaleConfig, CityScaleRunner

REPORT_PATH = Path("benchmarks/city_scale_5k_report.md")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("tmp/city_scale_5k"))
    parser.add_argument("--backend", choices=["single", "multiprocessing", "ray"], default="single")
    parser.add_argument("--agents", type=int, default=5000)
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260421)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--grid-width", type=int, default=40)
    parser.add_argument("--grid-height", type=int, default=40)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    run_summaries: list[dict[str, object]] = []
    hashes: list[str] = []
    jsonl_hashes: list[str] = []
    for repetition in range(1, args.repetitions + 1):
        config = CityScaleConfig(
            agent_count=args.agents,
            tick_count=args.ticks,
            repetitions=args.repetitions,
            seed=args.seed,
            workers=args.workers,
            backend=args.backend,
            grid_width=args.grid_width,
            grid_height=args.grid_height,
        )
        result = CityScaleRunner(config).run()
        jsonl_path = args.output / f"run_{repetition:02d}.jsonl"
        result.write_jsonl(jsonl_path)
        jsonl_hash = _file_sha256(jsonl_path)
        run_summaries.append(
            {
                "repetition": repetition,
                "backend": result.backend,
                "effective_backend": result.effective_backend,
                "wall_clock_seconds": result.wall_clock_seconds,
                "peak_rss_mb": result.peak_rss_mb,
                "throughput_agent_ticks_per_second": result.throughput_agent_ticks_per_second,
                "inter_shard_messages": result.inter_shard_messages,
                "event_count": len(result.events),
                "output_hash": result.output_hash,
                "jsonl_sha256": jsonl_hash,
            }
        )
        hashes.append(result.output_hash)
        jsonl_hashes.append(jsonl_hash)

    summary = _summary_payload(args, run_summaries, hashes, jsonl_hashes)
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(_format_report(summary), encoding="utf-8")


def _summary_payload(
    args: argparse.Namespace,
    run_summaries: list[dict[str, object]],
    hashes: list[str],
    jsonl_hashes: list[str],
) -> dict[str, object]:
    wall_times = [_as_float(row["wall_clock_seconds"]) for row in run_summaries]
    throughputs = [_as_float(row["throughput_agent_ticks_per_second"]) for row in run_summaries]
    peak_rss = [_as_float(row["peak_rss_mb"]) for row in run_summaries]
    return {
        "scenario": "gangnam-5k-city-scale-40x40",
        "agent_count": args.agents,
        "tick_count": args.ticks,
        "repetitions": args.repetitions,
        "backend": args.backend,
        "seed": args.seed,
        "grid_width": args.grid_width,
        "grid_height": args.grid_height,
        "runs": run_summaries,
        "summary": {
            "median_wall_clock_seconds": statistics.median(wall_times),
            "median_throughput_agent_ticks_per_second": statistics.median(throughputs),
            "peak_rss_mb": max(peak_rss),
            "deterministic_output_hash": hashes[0],
            "all_repetition_hashes_match": len(set(hashes)) == 1,
            "deterministic_jsonl_sha256": jsonl_hashes[0],
            "all_jsonl_hashes_match": len(set(jsonl_hashes)) == 1,
        },
        "comparison": [
            {
                "framework": "Knoema",
                "status": "measured",
                "agents": args.agents,
                "ticks": args.ticks,
                "median_wall_clock_seconds": statistics.median(wall_times),
                "agent_ticks_per_second": statistics.median(throughputs),
                "notes": "Deterministic local city-scale runner; no live LLM calls.",
            },
            {
                "framework": "Concordia",
                "status": "not-measured",
                "agents": None,
                "ticks": None,
                "median_wall_clock_seconds": None,
                "agent_ticks_per_second": None,
                "notes": "External adapter was not benchmarked in this run.",
            },
            {
                "framework": "Mesa",
                "status": "not-measured",
                "agents": None,
                "ticks": None,
                "median_wall_clock_seconds": None,
                "agent_ticks_per_second": None,
                "notes": "External adapter was not benchmarked in this run.",
            },
        ],
    }


def _format_report(summary: dict[str, object]) -> str:
    summary_block = summary["summary"]
    assert isinstance(summary_block, dict)
    comparison = summary["comparison"]
    assert isinstance(comparison, list)
    lines = [
        "# 5K Agent City-Scale Benchmark Report",
        "",
        f"Scenario: `{summary['scenario']}`",
        f"Agents: {summary['agent_count']}",
        f"Ticks: {summary['tick_count']}",
        f"Repetitions: {summary['repetitions']}",
        f"Backend: `{summary['backend']}`",
        f"Seed: `{summary['seed']}`",
        f"Grid: {summary['grid_width']}x{summary['grid_height']}",
        "",
        "## Summary",
        "",
        f"- Median wall-clock time: {float(summary_block['median_wall_clock_seconds']):.6f} seconds",
        "- Median throughput: "
        f"{float(summary_block['median_throughput_agent_ticks_per_second']):.2f} agent-ticks/sec",
        f"- Peak RSS: {float(summary_block['peak_rss_mb']):.3f} MB",
        f"- Deterministic output hash: `{summary_block['deterministic_output_hash']}`",
        f"- Repetition hashes match: `{summary_block['all_repetition_hashes_match']}`",
        f"- Deterministic JSONL SHA256: `{summary_block['deterministic_jsonl_sha256']}`",
        f"- JSONL hashes match: `{summary_block['all_jsonl_hashes_match']}`",
        "",
        "## Framework Comparison",
        "",
        "| Framework | Status | Agents | Ticks | Median seconds | Agent-ticks/sec | Notes |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in comparison:
        assert isinstance(row, dict)
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["framework"]),
                    str(row["status"]),
                    _format_optional(row["agents"]),
                    _format_optional(row["ticks"]),
                    _format_optional(row["median_wall_clock_seconds"], precision=6),
                    _format_optional(row["agent_ticks_per_second"], precision=2),
                    str(row["notes"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Concordia and Mesa are deliberately marked `not-measured`; this report does not invent external framework numbers.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_optional(value: object, *, precision: int = 0) -> str:
    if value is None:
        return "not-measured"
    if isinstance(value, float):
        return f"{value:.{precision}f}"
    return str(value)


def _as_float(value: object) -> float:
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"expected numeric value, got {type(value).__name__}")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
