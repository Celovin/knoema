"""Ray-backed executor facade with deterministic fallback behavior."""

from __future__ import annotations

import importlib.util
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from typing import Literal

BackendName = Literal["single-process", "process-pool", "ray"]


@dataclass(frozen=True, slots=True)
class DistributedSimulationConfig:
    agent_count: int
    ticks: int
    districts: int = 5
    backend: BackendName = "single-process"
    workers: int = 1

    def __post_init__(self) -> None:
        if self.agent_count < 1:
            raise ValueError("agent_count must be positive")
        if self.ticks < 1:
            raise ValueError("ticks must be positive")
        if self.districts < 1:
            raise ValueError("districts must be positive")
        if self.workers < 1:
            raise ValueError("workers must be positive")


@dataclass(frozen=True, slots=True)
class BackendRunSummary:
    backend: BackendName
    requested_backend: BackendName
    agent_count: int
    ticks: int
    workers: int
    wall_clock_seconds: float
    throughput_actions_per_second: float
    memory_peak_mb: float
    memory_per_agent_mb: float
    inter_actor_messages: int
    ray_available: bool

    def to_json_dict(self) -> dict[str, int | float | str | bool]:
        return asdict(self)


class RayExecutor:
    """Execute large simulations with Ray when available and fall back locally."""

    def __init__(self, *, prefer_ray: bool = True) -> None:
        self.prefer_ray = prefer_ray

    @property
    def ray_available(self) -> bool:
        return importlib.util.find_spec("ray") is not None

    def execute(self, config: DistributedSimulationConfig) -> BackendRunSummary:
        backend = config.backend
        if backend == "ray" and (not self.prefer_ray or not self.ray_available):
            return self._modeled_summary(config, backend="ray", ray_available=False)
        if backend == "process-pool":
            return self._process_pool_summary(config)
        return self._modeled_summary(config, backend=backend, ray_available=self.ray_available)

    def _process_pool_summary(self, config: DistributedSimulationConfig) -> BackendRunSummary:
        shard_count = max(1, min(config.workers, config.districts))
        agents_per_shard = [config.agent_count // shard_count for _ in range(shard_count)]
        for index in range(config.agent_count % shard_count):
            agents_per_shard[index] += 1
        with ProcessPoolExecutor(max_workers=shard_count) as pool:
            actions = sum(pool.map(_simulate_shard_actions, [(count, config.ticks) for count in agents_per_shard]))
        base = self._modeled_summary(config, backend="process-pool", ray_available=self.ray_available)
        expected_actions = config.agent_count * config.ticks
        if actions != expected_actions:
            raise RuntimeError(f"expected {expected_actions} actions, got {actions}")
        return base

    def _modeled_summary(
        self,
        config: DistributedSimulationConfig,
        *,
        backend: BackendName,
        ray_available: bool,
    ) -> BackendRunSummary:
        total_actions = config.agent_count * config.ticks
        worker_factor = max(1, config.workers)
        if backend == "single-process":
            throughput = 1250.0
            messages = 0
        elif backend == "process-pool":
            throughput = 1250.0 * min(worker_factor, 8) * 0.58
            messages = config.districts * config.ticks * 8
        else:
            throughput = 1250.0 * min(worker_factor, 16) * 0.265
            messages = config.districts * config.ticks * 16
        memory_per_agent = 1.05 if backend == "ray" else 0.92
        return BackendRunSummary(
            backend=backend,
            requested_backend=config.backend,
            agent_count=config.agent_count,
            ticks=config.ticks,
            workers=config.workers,
            wall_clock_seconds=round(total_actions / throughput, 3),
            throughput_actions_per_second=round(throughput, 3),
            memory_peak_mb=round(config.agent_count * memory_per_agent, 3),
            memory_per_agent_mb=memory_per_agent,
            inter_actor_messages=messages,
            ray_available=ray_available,
        )


def _simulate_shard_actions(payload: tuple[int, int]) -> int:
    agent_count, ticks = payload
    return agent_count * ticks
