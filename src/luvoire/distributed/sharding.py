"""Location-based sharding utilities for distributed simulation."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from luvoire.types import AgentID


@dataclass(frozen=True, slots=True)
class Shard:
    shard_id: str
    location: str
    agent_ids: tuple[AgentID, ...]

    @property
    def load(self) -> int:
        return len(self.agent_ids)


@dataclass(frozen=True, slots=True)
class ShardPlan:
    shards: tuple[Shard, ...]

    @property
    def total_agents(self) -> int:
        return sum(shard.load for shard in self.shards)

    @property
    def max_load(self) -> int:
        return max((shard.load for shard in self.shards), default=0)


def shard_agents_by_location(
    agent_locations: dict[AgentID, str],
    *,
    max_shards: int = 16,
) -> ShardPlan:
    if max_shards < 1:
        raise ValueError("max_shards must be positive")
    grouped: dict[str, list[AgentID]] = defaultdict(list)
    for agent_id, location in agent_locations.items():
        if not agent_id.strip():
            raise ValueError("agent_id must not be blank")
        if not location.strip():
            raise ValueError("location must not be blank")
        grouped[location].append(agent_id)

    shards: list[Shard] = []
    for index, location in enumerate(sorted(grouped), start=1):
        agents = tuple(sorted(grouped[location]))
        if len(shards) < max_shards:
            shards.append(Shard(f"shard-{index:02d}", location, agents))
        else:
            lightest_index = min(range(len(shards)), key=lambda offset: shards[offset].load)
            lightest = shards[lightest_index]
            merged_agents = tuple(sorted((*lightest.agent_ids, *agents)))
            shards[lightest_index] = Shard(lightest.shard_id, lightest.location, merged_agents)
    return ShardPlan(tuple(shards))


def detect_hot_shards(plan: ShardPlan, *, threshold: int) -> tuple[Shard, ...]:
    if threshold < 1:
        raise ValueError("threshold must be positive")
    return tuple(shard for shard in plan.shards if shard.load > threshold)


def rebalance_hot_shards(plan: ShardPlan, *, threshold: int) -> ShardPlan:
    hot_shards = set(detect_hot_shards(plan, threshold=threshold))
    if not hot_shards:
        return plan

    rebalanced: list[Shard] = []
    next_index = 1
    for shard in plan.shards:
        if shard not in hot_shards:
            rebalanced.append(shard)
            continue
        midpoint = max(1, shard.load // 2)
        parts = (shard.agent_ids[:midpoint], shard.agent_ids[midpoint:])
        for part in parts:
            if part:
                rebalanced.append(
                    Shard(f"{shard.shard_id}-r{next_index}", shard.location, tuple(part))
                )
                next_index += 1
    return ShardPlan(tuple(rebalanced))
