"""Run the Phase 52 deterministic 1000-agent city scale experiment."""

from __future__ import annotations

import json
from pathlib import Path

from luvoire.distributed import DistributedSimulationConfig, RayExecutor

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
SUMMARY_PATH = RESULTS_DIR / "summary.json"
FIGURE_PATH = RESULTS_DIR / "latency_scaling.svg"


def run_experiment() -> dict[str, object]:
    executor = RayExecutor()
    configs = [
        DistributedSimulationConfig(
            agent_count=1000,
            ticks=200,
            districts=5,
            backend="single-process",
            workers=1,
        ),
        DistributedSimulationConfig(
            agent_count=1000,
            ticks=200,
            districts=5,
            backend="process-pool",
            workers=8,
        ),
        DistributedSimulationConfig(
            agent_count=1000,
            ticks=200,
            districts=5,
            backend="ray",
            workers=16,
        ),
    ]
    runs = [executor.execute(config).to_json_dict() for config in configs]
    by_backend = {str(run["backend"]): run for run in runs}
    single = float(by_backend["single-process"]["throughput_actions_per_second"])
    ray = float(by_backend["ray"]["throughput_actions_per_second"])
    max_memory_per_agent = max(float(run["memory_per_agent_mb"]) for run in runs)
    return {
        "scenario_name": "1000_agent_city",
        "agent_count": 1000,
        "district_count": 5,
        "ticks": 200,
        "total_actions": 200000,
        "backends": runs,
        "acceptance": {
            "ray_backend_at_least_3x_single_process": ray / single >= 3.0,
            "max_memory_per_agent_at_most_1_2_mb": max_memory_per_agent <= 1.2,
        },
    }


def write_latency_svg(summary: dict[str, object]) -> None:
    backends = summary["backends"]
    if not isinstance(backends, list):
        raise TypeError("backends must be a list")
    bars = []
    for index, run in enumerate(backends):
        if not isinstance(run, dict):
            raise TypeError("backend run must be a mapping")
        label = str(run["backend"])
        throughput = float(run["throughput_actions_per_second"])
        height = throughput / 5500 * 220
        x = 90 + index * 170
        y = 290 - height
        bars.append(
            f'<rect x="{x}" y="{y:.2f}" width="100" height="{height:.2f}" fill="#2563eb" />'
            f'<text x="{x - 18}" y="326" font-size="13" fill="#0f172a">{label}</text>'
            f'<text x="{x + 8}" y="{y - 10:.2f}" font-size="13" fill="#0f172a">{throughput:.0f}</text>'
        )
    FIGURE_PATH.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="380" viewBox="0 0 640 380">'
        '<rect width="100%" height="100%" fill="#ffffff" />'
        '<text x="36" y="42" font-size="24" font-family="Arial" fill="#0f172a">1000-Agent City Throughput</text>'
        '<line x1="70" y1="290" x2="590" y2="290" stroke="#0f172a" />'
        '<line x1="70" y1="70" x2="70" y2="290" stroke="#0f172a" />'
        f'{"".join(bars)}'
        '<text x="36" y="354" font-size="12" fill="#334155">Values are deterministic local envelope metrics; Ray remains an optional dependency.</text>'
        "</svg>\n",
        encoding="utf-8",
    )


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = run_experiment()
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_latency_svg(summary)


if __name__ == "__main__":
    main()
