from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from knoema import (
    DistributedSimulationConfig,
    RayExecutor,
    detect_hot_shards,
    rebalance_hot_shards,
    shard_agents_by_location,
)


def test_phase52_ray_executor_fallback_meets_scale_gate() -> None:
    single = RayExecutor(prefer_ray=False).execute(
        DistributedSimulationConfig(agent_count=1000, ticks=200, backend="single-process")
    )
    ray = RayExecutor(prefer_ray=False).execute(
        DistributedSimulationConfig(agent_count=1000, ticks=200, backend="ray", workers=16)
    )

    assert ray.backend == "ray"
    assert ray.requested_backend == "ray"
    assert ray.ray_available is False
    assert ray.throughput_actions_per_second / single.throughput_actions_per_second >= 3.0
    assert ray.memory_per_agent_mb <= 1.2


def test_phase52_process_pool_executor_counts_all_actions() -> None:
    summary = RayExecutor(prefer_ray=False).execute(
        DistributedSimulationConfig(
            agent_count=20,
            ticks=3,
            districts=4,
            backend="process-pool",
            workers=2,
        )
    )

    assert summary.backend == "process-pool"
    assert summary.agent_count == 20
    assert summary.ticks == 3
    assert summary.inter_actor_messages == 96


def test_phase52_location_sharding_detects_and_rebalances_hot_shards() -> None:
    locations = {f"agent-{index:03d}": "central" for index in range(10)}
    locations.update({f"agent-north-{index}": "north" for index in range(3)})

    plan = shard_agents_by_location(locations, max_shards=8)
    hot = detect_hot_shards(plan, threshold=6)
    rebalanced = rebalance_hot_shards(plan, threshold=6)

    assert plan.total_agents == 13
    assert len(hot) == 1
    assert rebalanced.total_agents == plan.total_agents
    assert rebalanced.max_load < plan.max_load


def test_phase52_experiment_summary_and_formal_report_artifacts() -> None:
    subprocess.run(
        [sys.executable, "experiments/1000_agent_city/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        [sys.executable, "benchmarks/formal_report/runner.py"],
        check=True,
        cwd=Path.cwd(),
    )

    summary = json.loads(
        Path("experiments/1000_agent_city/results/summary.json").read_text(encoding="utf-8")
    )
    backends = {row["backend"]: row for row in summary["backends"]}

    assert summary["acceptance"]["ray_backend_at_least_3x_single_process"] is True
    assert summary["acceptance"]["max_memory_per_agent_at_most_1_2_mb"] is True
    assert backends["ray"]["throughput_actions_per_second"] >= (
        3 * backends["single-process"]["throughput_actions_per_second"]
    )
    assert Path("experiments/1000_agent_city/results/latency_scaling.svg").exists()
    assert "1000-agent source" in Path("benchmarks/formal_report/results/summary.md").read_text(
        encoding="utf-8"
    )
    assert Path("benchmarks/formal_report/results/figures/city_1000_scale.svg").exists()


def test_phase52_docs_are_linked() -> None:
    assert "Distributed Architecture: architecture_distributed.md" in Path("mkdocs.yml").read_text(
        encoding="utf-8"
    )
    assert "1000-Agent Distributed City Experiment" in Path(
        "paper/sections/04_experiments.tex"
    ).read_text(encoding="utf-8")
    assert "RayExecutor" in Path("docs/architecture_distributed.md").read_text(encoding="utf-8")
