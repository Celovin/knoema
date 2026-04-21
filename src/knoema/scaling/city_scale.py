"""Deterministic city-scale runner for large offline agent simulations."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import multiprocessing
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

try:  # pragma: no cover - psutil is present in the project dev environment.
    import psutil  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    psutil = None


CityScaleBackend = Literal["single", "multiprocessing", "ray"]
CityRole = Literal["general", "motivated_offender", "guardian"]


@dataclass(frozen=True, slots=True)
class CityScaleConfig:
    """Configuration for a deterministic city-scale run."""

    agent_count: int = 1000
    tick_count: int = 100
    repetitions: int = 1
    seed: int = 20260421
    workers: int | None = None
    backend: CityScaleBackend = "multiprocessing"
    grid_width: int = 20
    grid_height: int = 20
    tick_minutes: int = 1
    start_time_iso: str = "2026-04-21T19:00:00"

    def __post_init__(self) -> None:
        if self.agent_count < 1:
            raise ValueError("agent_count must be positive")
        if self.tick_count < 1:
            raise ValueError("tick_count must be positive")
        if self.repetitions < 1:
            raise ValueError("repetitions must be positive")
        if self.workers is not None and self.workers < 1:
            raise ValueError("workers must be positive when provided")
        if self.grid_width < 2 or self.grid_height < 2:
            raise ValueError("grid dimensions must be at least 2x2")
        if self.tick_minutes < 1:
            raise ValueError("tick_minutes must be positive")
        datetime.fromisoformat(self.start_time_iso)

    @property
    def resolved_workers(self) -> int:
        requested = self.workers or multiprocessing.cpu_count()
        return max(1, min(requested, self.agent_count))

    @property
    def agent_ticks(self) -> int:
        return self.agent_count * self.tick_count

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["resolved_workers"] = self.resolved_workers
        return payload


@dataclass(frozen=True, slots=True)
class CityAgentState:
    """Mutable-by-replacement state owned by one shard at a time."""

    agent_id: str
    role: CityRole
    x: int
    y: int
    memory_ids: tuple[str, ...]
    status_flags: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "position": [self.x, self.y],
            "memory_ids": list(self.memory_ids),
            "status_flags": list(self.status_flags),
        }


@dataclass(frozen=True, slots=True)
class CityScaleMessage:
    tick: int
    sender_id: str
    target_id: str
    kind: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CityScaleTraceFrame:
    """One per-agent delta for a tick."""

    tick: int
    agent_id: str
    position: tuple[int, int]
    status_flags: tuple[str, ...]
    memory_delta_ids: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "tick": self.tick,
            "agent_id": self.agent_id,
            "position": list(self.position),
            "status_flags": list(self.status_flags),
            "memory_delta_ids": list(self.memory_delta_ids),
        }


@dataclass(frozen=True, slots=True)
class CityScaleShardResult:
    """A pure shard step result returned to the coordinator."""

    shard_id: int
    agents: tuple[CityAgentState, ...]
    frames: tuple[CityScaleTraceFrame, ...]
    outbox: tuple[CityScaleMessage, ...]


@dataclass(frozen=True, slots=True)
class CityScaleResult:
    """Complete city-scale run result."""

    config: CityScaleConfig
    backend: CityScaleBackend
    effective_backend: CityScaleBackend
    wall_clock_seconds: float
    peak_rss_mb: float
    frames: tuple[CityScaleTraceFrame, ...]
    events: tuple[dict[str, object], ...]
    final_agents: tuple[CityAgentState, ...]
    inter_shard_messages: int
    output_hash: str

    @property
    def throughput_agent_ticks_per_second(self) -> float:
        elapsed = self.wall_clock_seconds if self.wall_clock_seconds > 0 else 1e-12
        return self.config.agent_ticks / elapsed

    def to_json_dict(self, *, include_frames: bool = True) -> dict[str, object]:
        payload: dict[str, object] = {
            "config": self.config.to_json_dict(),
            "backend": self.backend,
            "effective_backend": self.effective_backend,
            "wall_clock_seconds": self.wall_clock_seconds,
            "peak_rss_mb": self.peak_rss_mb,
            "throughput_agent_ticks_per_second": self.throughput_agent_ticks_per_second,
            "inter_shard_messages": self.inter_shard_messages,
            "output_hash": self.output_hash,
            "event_count": len(self.events),
        }
        if include_frames:
            payload["frames"] = [frame.to_json_dict() for frame in self.frames]
            payload["events"] = list(self.events)
        return payload

    def write_jsonl(self, path: str | Path) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            for frame in self.frames:
                file.write(json.dumps(frame.to_json_dict(), sort_keys=True) + "\n")


class CityScaleRunner:
    """Run deterministic city-scale simulations with shard-isolated state."""

    def __init__(self, config: CityScaleConfig | None = None) -> None:
        self.config = config or CityScaleConfig()

    def run(self) -> CityScaleResult:
        config = self.config
        effective_backend = _effective_backend(config.backend)
        shards = _shard_agents(_initial_agents(config), config.resolved_workers)
        inbox_by_shard: dict[int, tuple[CityScaleMessage, ...]] = dict.fromkeys(range(len(shards)), ())
        agent_to_shard = _agent_to_shard(shards)
        frames: list[CityScaleTraceFrame] = []
        events: list[dict[str, object]] = []
        inter_shard_messages = 0
        peak_rss_mb = _rss_mb()
        start = time.perf_counter()

        if effective_backend == "multiprocessing":
            with ProcessPoolExecutor(max_workers=config.resolved_workers) as executor:
                for tick in range(config.tick_count):
                    payloads = [
                        (shard_id, tuple(agents), tick, inbox_by_shard.get(shard_id, ()), config)
                        for shard_id, agents in sorted(shards.items())
                    ]
                    results = tuple(executor.map(_process_shard_tick, payloads))
                    shards, inbox_by_shard, tick_messages = _merge_shard_results(
                        results,
                        agent_to_shard=agent_to_shard,
                        shard_count=len(shards),
                    )
                    agent_to_shard = _agent_to_shard(shards)
                    for result in sorted(results, key=lambda item: item.shard_id):
                        frames.extend(result.frames)
                    events.extend(_convergence_events(tick, shards, config))
                    inter_shard_messages += tick_messages
                    peak_rss_mb = max(peak_rss_mb, _rss_mb())
        else:
            for tick in range(config.tick_count):
                results = tuple(
                    _process_shard_tick(
                        (shard_id, tuple(agents), tick, inbox_by_shard.get(shard_id, ()), config)
                    )
                    for shard_id, agents in sorted(shards.items())
                )
                shards, inbox_by_shard, tick_messages = _merge_shard_results(
                    results,
                    agent_to_shard=agent_to_shard,
                    shard_count=len(shards),
                )
                agent_to_shard = _agent_to_shard(shards)
                for result in sorted(results, key=lambda item: item.shard_id):
                    frames.extend(result.frames)
                events.extend(_convergence_events(tick, shards, config))
                inter_shard_messages += tick_messages
                peak_rss_mb = max(peak_rss_mb, _rss_mb())

        elapsed = time.perf_counter() - start
        final_agents = tuple(
            sorted(
                (agent for shard_agents in shards.values() for agent in shard_agents),
                key=lambda agent: agent.agent_id,
            )
        )
        sorted_frames = tuple(sorted(frames, key=lambda frame: (frame.tick, frame.agent_id)))
        sorted_events = tuple(sorted(events, key=_event_sort_key))
        output_hash = city_scale_output_hash(sorted_frames, sorted_events, config)
        return CityScaleResult(
            config=config,
            backend=config.backend,
            effective_backend=effective_backend,
            wall_clock_seconds=round(elapsed, 6),
            peak_rss_mb=round(peak_rss_mb, 3),
            frames=sorted_frames,
            events=sorted_events,
            final_agents=final_agents,
            inter_shard_messages=inter_shard_messages,
            output_hash=output_hash,
        )


def city_scale_output_hash(
    frames: tuple[CityScaleTraceFrame, ...],
    events: tuple[dict[str, object], ...],
    config: CityScaleConfig,
) -> str:
    """Hash deterministic run outputs without wall-clock measurements."""

    canonical = {
        "config": {
            "agent_count": config.agent_count,
            "tick_count": config.tick_count,
            "seed": config.seed,
            "grid_width": config.grid_width,
            "grid_height": config.grid_height,
            "tick_minutes": config.tick_minutes,
            "start_time_iso": config.start_time_iso,
        },
        "frames": [frame.to_json_dict() for frame in frames],
        "events": list(events),
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _effective_backend(backend: CityScaleBackend) -> CityScaleBackend:
    if backend == "ray":
        if importlib.util.find_spec("ray") is None:
            return "multiprocessing"
        return "multiprocessing"
    return backend


def _initial_agents(config: CityScaleConfig) -> tuple[CityAgentState, ...]:
    offender_count = max(1, round(config.agent_count * 0.03))
    guardian_count = max(1, round(config.agent_count * 0.05))
    general_count = config.agent_count - offender_count - guardian_count
    roles: list[CityRole] = []
    roles.extend("general" for _ in range(general_count))
    roles.extend("motivated_offender" for _ in range(offender_count))
    roles.extend("guardian" for _ in range(guardian_count))
    agents: list[CityAgentState] = []
    for index, role in enumerate(roles):
        agent_id = f"agent-{index:04d}"
        x, y = _initial_position(index, role, config)
        agents.append(
            CityAgentState(
                agent_id=agent_id,
                role=role,
                x=x,
                y=y,
                memory_ids=tuple(f"{agent_id}-m{slot}" for slot in range(1, 7)),
                status_flags=_status_flags(role, x, y, config),
            )
        )
    return tuple(agents)


def _initial_position(index: int, role: CityRole, config: CityScaleConfig) -> tuple[int, int]:
    digest = _digest_int(config.seed, index, role)
    if role == "guardian":
        return digest % config.grid_width, (digest // 7) % 3
    if role == "motivated_offender":
        return 6 + digest % 8, 6 + (digest // 11) % 8
    return digest % config.grid_width, (digest // config.grid_width) % config.grid_height


def _event_sort_key(event: dict[str, object]) -> tuple[int, str]:
    return int(str(event["tick_id"])), str(event["id"])


def _shard_agents(
    agents: tuple[CityAgentState, ...],
    workers: int,
) -> dict[int, tuple[CityAgentState, ...]]:
    shards: dict[int, list[CityAgentState]] = {index: [] for index in range(workers)}
    for offset, agent in enumerate(sorted(agents, key=lambda item: item.agent_id)):
        shards[offset % workers].append(agent)
    return {shard_id: tuple(shard_agents) for shard_id, shard_agents in shards.items()}


def _agent_to_shard(shards: dict[int, tuple[CityAgentState, ...]]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for shard_id, agents in shards.items():
        for agent in agents:
            mapping[agent.agent_id] = shard_id
    return mapping


def _process_shard_tick(
    payload: tuple[int, tuple[CityAgentState, ...], int, tuple[CityScaleMessage, ...], CityScaleConfig],
) -> CityScaleShardResult:
    shard_id, agents, tick, inbox, config = payload
    inbox_by_agent: dict[str, list[CityScaleMessage]] = defaultdict(list)
    for message in inbox:
        inbox_by_agent[message.target_id].append(message)

    updated_agents: list[CityAgentState] = []
    frames: list[CityScaleTraceFrame] = []
    outbox: list[CityScaleMessage] = []
    for agent in agents:
        x, y = _move_agent(agent, tick, config)
        memory_delta_ids = _memory_delta_ids(agent, tick, inbox_by_agent.get(agent.agent_id, []))
        memory_ids = (*agent.memory_ids, *memory_delta_ids)[-6:]
        status_flags = _status_flags(agent.role, x, y, config)
        updated = replace(agent, x=x, y=y, memory_ids=memory_ids, status_flags=status_flags)
        updated_agents.append(updated)
        frames.append(
            CityScaleTraceFrame(
                tick=tick,
                agent_id=agent.agent_id,
                position=(x, y),
                status_flags=status_flags,
                memory_delta_ids=memory_delta_ids,
            )
        )
        if tick % 7 == 0:
            target_index = (_agent_index(agent.agent_id) + tick + 1) % config.agent_count
            outbox.append(
                CityScaleMessage(
                    tick=tick,
                    sender_id=agent.agent_id,
                    target_id=f"agent-{target_index:04d}",
                    kind="encounter-note",
                )
            )
    return CityScaleShardResult(
        shard_id=shard_id,
        agents=tuple(updated_agents),
        frames=tuple(frames),
        outbox=tuple(outbox),
    )


def _merge_shard_results(
    results: tuple[CityScaleShardResult, ...],
    *,
    agent_to_shard: dict[str, int],
    shard_count: int,
) -> tuple[dict[int, tuple[CityAgentState, ...]], dict[int, tuple[CityScaleMessage, ...]], int]:
    shards = {result.shard_id: result.agents for result in results}
    inbox: dict[int, list[CityScaleMessage]] = {shard_id: [] for shard_id in range(shard_count)}
    inter_shard_messages = 0
    ordered_messages = sorted(
        (message for result in results for message in result.outbox),
        key=lambda message: (message.tick, message.sender_id, message.target_id),
    )
    for message in ordered_messages:
        target_shard = agent_to_shard[message.target_id]
        inbox[target_shard].append(message)
        if agent_to_shard[message.sender_id] != target_shard:
            inter_shard_messages += 1
    return shards, {key: tuple(value) for key, value in inbox.items()}, inter_shard_messages


def _move_agent(agent: CityAgentState, tick: int, config: CityScaleConfig) -> tuple[int, int]:
    digest = _digest_int(config.seed, _agent_index(agent.agent_id), tick)
    if agent.role == "guardian":
        route = tick % (2 * config.grid_width)
        x = route if route < config.grid_width else (2 * config.grid_width - route - 1)
        y = (tick // config.grid_width + digest) % config.grid_height
        return x, y
    if agent.role == "motivated_offender":
        dx = (digest % 3) - 1
        dy = ((digest // 3) % 3) - 1
        return _clamp(agent.x + dx, 5, 14), _clamp(agent.y + dy, 5, 14)

    commute_phase = tick % 30
    if commute_phase < 10:
        target = (10, 10)
    elif commute_phase < 20:
        target = (15, 12)
    else:
        target = (_digest_int(config.seed, agent.agent_id) % config.grid_width, 18)
    return _step_toward((agent.x, agent.y), target, config)


def _memory_delta_ids(
    agent: CityAgentState,
    tick: int,
    inbox: list[CityScaleMessage],
) -> tuple[str, ...]:
    deltas: list[str] = []
    if tick % 6 == 0:
        deltas.append(f"{agent.agent_id}-t{tick:03d}-routine")
    if inbox:
        deltas.append(f"{agent.agent_id}-t{tick:03d}-msg{len(inbox)}")
    return tuple(deltas)


def _convergence_events(
    tick: int,
    shards: dict[int, tuple[CityAgentState, ...]],
    config: CityScaleConfig,
) -> tuple[dict[str, object], ...]:
    agents = tuple(agent for shard in shards.values() for agent in shard)
    guardians = [agent for agent in agents if agent.role == "guardian"]
    targets = [agent for agent in agents if agent.role == "general"]
    events: list[dict[str, object]] = []
    for offender in (agent for agent in agents if agent.role == "motivated_offender"):
        nearby_target = next(
            (
                target
                for target in targets
                if abs(target.x - offender.x) <= 1 and abs(target.y - offender.y) <= 1
            ),
            None,
        )
        if nearby_target is None:
            continue
        guardian_present = any(
            abs(guardian.x - offender.x) <= 1 and abs(guardian.y - offender.y) <= 1
            for guardian in guardians
        )
        if not guardian_present:
            events.append(
                {
                    "id": f"evt-{tick:03d}-{offender.agent_id}-{nearby_target.agent_id}",
                    "tick_id": tick,
                    "agent_a": offender.agent_id,
                    "agent_b": nearby_target.agent_id,
                    "type": "unguarded_convergence",
                    "position": [offender.x, offender.y],
                    "seed": config.seed,
                }
            )
    return tuple(events)


def _status_flags(role: CityRole, x: int, y: int, config: CityScaleConfig) -> tuple[str, ...]:
    flags: list[str] = [role]
    if 7 <= x <= 13 and 7 <= y <= 13:
        flags.append("commercial-zone")
    if x in {0, config.grid_width - 1} or y in {0, config.grid_height - 1}:
        flags.append("edge")
    return tuple(flags)


def _step_toward(
    current: tuple[int, int],
    target: tuple[int, int],
    config: CityScaleConfig,
) -> tuple[int, int]:
    x, y = current
    target_x, target_y = target
    if x < target_x:
        x += 1
    elif x > target_x:
        x -= 1
    if y < target_y:
        y += 1
    elif y > target_y:
        y -= 1
    return _clamp(x, 0, config.grid_width - 1), _clamp(y, 0, config.grid_height - 1)


def _agent_index(agent_id: str) -> int:
    return int(agent_id.rsplit("-", 1)[1])


def _digest_int(*parts: object) -> int:
    text = ":".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return min(maximum, max(minimum, value))


def _rss_mb() -> float:
    if psutil is None:
        return 0.0
    process = psutil.Process()
    return float(process.memory_info().rss / (1024 * 1024))


def replay_timestamp(config: CityScaleConfig, tick: int) -> str:
    """Return the wall-clock timestamp for a simulated tick."""

    start = datetime.fromisoformat(config.start_time_iso)
    return (start + timedelta(minutes=tick * config.tick_minutes)).isoformat()


__all__ = [
    "CityAgentState",
    "CityScaleBackend",
    "CityScaleConfig",
    "CityScaleResult",
    "CityScaleRunner",
    "CityScaleShardResult",
    "CityScaleTraceFrame",
    "city_scale_output_hash",
    "replay_timestamp",
]
