"""Generate deterministic offline msgpack replay artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import msgpack  # type: ignore[import-untyped]
import yaml

from knoema.scaling import CityScaleConfig, CityScaleRunner
from knoema.scaling.city_scale import replay_timestamp

REPLAY_DIR = Path(__file__).resolve().parent
DEFAULT_SCENARIOS = ("100", "1k")
VERIFY_SCENARIOS = ("100", "1k", "5k")
SCENARIOS: dict[str, dict[str, object]] = {
    "100": {
        "agent_count": 100,
        "filename": "replay_100agents_gangnam_7pm.msgpack",
    },
    "1k": {
        "agent_count": 1000,
        "filename": "replay_1000agents_gangnam_7pm.msgpack",
    },
    "5k": {
        "agent_count": 5000,
        "filename": "replay_5000agents_gangnam_7pm.msgpack",
        "config": "scenario_config_40x40.yaml",
        "compact_initial_memories": True,
        "include_memory_deltas": False,
    },
}
MEMORY_LABELS = (
    "Recent cue",
    "Routine anchor",
    "Place memory",
    "Social expectation",
    "Risk perception",
    "Current intent",
)
GENERAL_TEMPLATES = (
    "Noted evening crowding near transit Exit 3 three days ago.",
    "Usually takes the main-road corridor after work.",
    "Prefers bright storefront edges when walking alone.",
    "Remembers a neighbor recommending the commercial strip route.",
    "Tracks whether the next block feels crowded or isolated.",
    "Plans to finish one errand before heading home.",
)
OFFENDER_TEMPLATES = (
    "Noted blind corners while passing back-alley storefronts.",
    "Usually loiters near commercial edges after rush hour.",
    "Remembers which side street has low pedestrian flow.",
    "Watches for abrupt changes in guardian patrol rhythm.",
    "Avoids blocks where groups cluster near entrances.",
    "Plans to keep moving unless convergence looks favorable.",
)
GUARDIAN_TEMPLATES = (
    "Logged a patrol note near the main-road crossing.",
    "Usually walks a visible route through commercial cells.",
    "Remembers crowding around the transit corridor.",
    "Checks alleys when footfall thins after commute peaks.",
    "Treats isolated convergence as a reason to approach.",
    "Plans to complete one loop before the next time marker.",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=REPLAY_DIR)
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), default=None)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, str] = {}
    scenario_names = _selected_scenarios(args.scenario, verify_existing=args.verify_existing)
    for scenario_name in scenario_names:
        scenario = SCENARIOS[scenario_name]
        filename = str(scenario["filename"])
        payload = build_replay_payload(
            agent_count=int(scenario["agent_count"]),
            scenario_config=(
                REPLAY_DIR / str(scenario["config"])
                if "config" in scenario
                else None
            ),
            compact_initial_memories=bool(scenario.get("compact_initial_memories", False)),
            include_memory_deltas=bool(scenario.get("include_memory_deltas", True)),
        )
        encoded = msgpack.packb(payload, use_bin_type=True, strict_types=True)
        output_path = args.output_dir / filename
        digest = hashlib.sha256(encoded).hexdigest()
        if args.verify_existing:
            existing = output_path.read_bytes()
            existing_digest = hashlib.sha256(existing).hexdigest()
            if existing_digest != digest:
                raise SystemExit(
                    f"{filename} is not byte-identical: existing={existing_digest} generated={digest}"
                )
        else:
            output_path.write_bytes(encoded)
        generated[filename] = digest

    if args.scenario is None and not args.verify_existing:
        (args.output_dir / "SHA256SUMS.json").write_text(
            json.dumps(generated, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _selected_scenarios(scenario: str | None, *, verify_existing: bool) -> tuple[str, ...]:
    if scenario is not None:
        return (scenario,)
    if verify_existing:
        return VERIFY_SCENARIOS
    return DEFAULT_SCENARIOS


def build_replay_payload(
    *,
    agent_count: int,
    scenario_config: Path | None = None,
    compact_initial_memories: bool = False,
    include_memory_deltas: bool = True,
) -> dict[str, Any]:
    scenario_values = _scenario_values(scenario_config)
    config = CityScaleConfig(
        agent_count=agent_count,
        tick_count=int(scenario_values["tick_count"]),
        seed=int(scenario_values["seed"]),
        workers=min(8, agent_count),
        backend="single",
        grid_width=int(scenario_values["grid_width"]),
        grid_height=int(scenario_values["grid_height"]),
        tick_minutes=int(scenario_values["tick_minutes"]),
        start_time_iso=str(scenario_values["start_time_iso"]),
    )
    result = CityScaleRunner(config).run()
    memory_snapshots: dict[str, dict[str, Any]] = {}
    initial_by_agent = {
        frame.agent_id: frame
        for frame in result.frames
        if frame.tick == 0
    }
    agents = []
    for agent in result.final_agents:
        agent_payload = agent.to_json_dict()
        agents.append(
            _agent_static(
                agent_payload,
                initial_by_agent[str(agent_payload["agent_id"])],
                memory_snapshots,
                config,
                compact_initial_memories=compact_initial_memories,
            )
        )
    frames = _frames_by_tick(
        result,
        memory_snapshots,
        config,
        include_memory_deltas=include_memory_deltas,
    )
    return {
        "metadata": {
            "scenario_id": "gangnam_7pm_offline_replay",
            "seed": config.seed,
            "agent_count": agent_count,
            "tick_count": config.tick_count,
            "start_time_iso": config.start_time_iso,
            "grid_bounds": {"width": config.grid_width, "height": config.grid_height},
            "runner_output_hash": result.output_hash,
        },
        "agents": agents,
        "frames": frames,
        "memory_snapshots": memory_snapshots,
        "events": list(result.events),
    }


def _agent_static(
    agent: dict[str, Any],
    initial_frame: Any,
    memory_snapshots: dict[str, dict[str, Any]],
    config: CityScaleConfig,
    *,
    compact_initial_memories: bool = False,
) -> dict[str, Any]:
    agent_id = str(agent["agent_id"])
    role = str(agent["role"])
    memories = (
        [_compact_initial_memory(agent_id, role, config)]
        if compact_initial_memories
        else _initial_memories(agent_id, role, config)
    )
    for memory in memories:
        memory_snapshots[str(memory["memory_id"])] = memory
    return {
        "id": agent_id,
        "role": role,
        "demographics": _demographics(agent_id, role),
        "initial_position": list(initial_frame.position),
        "initial_status_flags": list(initial_frame.status_flags),
        "initial_memory_snapshot": [str(memory["memory_id"]) for memory in memories],
    }


def _scenario_values(scenario_config: Path | None) -> dict[str, object]:
    values: dict[str, object] = {
        "seed": 20260421,
        "tick_count": 30,
        "tick_minutes": 1,
        "start_time_iso": "2026-04-21T19:00:00",
        "grid_width": 20,
        "grid_height": 20,
    }
    if scenario_config is None:
        return values
    with scenario_config.open("r", encoding="utf-8") as file:
        scenario = yaml.safe_load(file)
    if not isinstance(scenario, dict):
        raise ValueError(f"invalid scenario config: {scenario_config}")
    grid = scenario.get("grid")
    if not isinstance(grid, dict):
        raise ValueError(f"missing grid block in scenario config: {scenario_config}")
    values.update(
        {
            "seed": scenario["seed"],
            "tick_count": scenario["tick_count"],
            "tick_minutes": scenario["tick_minutes"],
            "start_time_iso": scenario["start_time_iso"],
            "grid_width": grid["width"],
            "grid_height": grid["height"],
        }
    )
    return values


def _initial_memories(agent_id: str, role: str, config: CityScaleConfig) -> list[dict[str, Any]]:
    templates = {
        "general": GENERAL_TEMPLATES,
        "motivated_offender": OFFENDER_TEMPLATES,
        "guardian": GUARDIAN_TEMPLATES,
    }[role]
    offset = _stable_int(agent_id, config.seed) % len(templates)
    memories: list[dict[str, Any]] = []
    for slot in range(6):
        template = templates[(slot + offset) % len(templates)]
        memories.append(
            {
                "memory_id": f"{agent_id}-m{slot + 1}",
                "agent_id": agent_id,
                "label": MEMORY_LABELS[slot],
                "timestamp": replay_timestamp(config, max(0, slot - 5)),
                "content": template,
            }
        )
    return memories


def _compact_initial_memory(agent_id: str, role: str, config: CityScaleConfig) -> dict[str, Any]:
    content_by_role = {
        "general": "Scaled evening route.",
        "motivated_offender": "Scaled edge scan.",
        "guardian": "Scaled corridor patrol.",
    }
    memory_id = f"{agent_id}-m1"
    return {
        "memory_id": memory_id,
        "agent_id": agent_id,
        "label": "Routine anchor",
        "timestamp": replay_timestamp(config, 0),
        "content": content_by_role[role],
    }


def _frames_by_tick(
    result: Any,
    memory_snapshots: dict[str, dict[str, Any]],
    config: CityScaleConfig,
    *,
    include_memory_deltas: bool = True,
) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    by_tick: dict[int, dict[str, Any]] = {}
    last_by_agent: dict[str, dict[str, Any]] = {}
    for frame in result.frames:
        frame_payload = frame.to_json_dict()
        if include_memory_deltas:
            for memory_id in frame_payload["memory_delta_ids"]:
                memory_snapshots[str(memory_id)] = {
                    "memory_id": str(memory_id),
                    "agent_id": frame.agent_id,
                    "label": "Simulation update",
                    "timestamp": replay_timestamp(config, frame.tick),
                    "content": _memory_delta_content(str(memory_id)),
                }
        by_tick.setdefault(
            frame.tick,
            {
                "tick_id": frame.tick,
                "timestamp": replay_timestamp(config, frame.tick),
                "deltas": {},
            },
        )
        previous = last_by_agent.get(frame.agent_id)
        delta: dict[str, Any] = {}
        if previous is None:
            if include_memory_deltas and frame_payload["memory_delta_ids"]:
                delta["memory_delta_ids"] = frame_payload["memory_delta_ids"]
        else:
            if frame_payload["position"] != previous["position"]:
                delta["position"] = frame_payload["position"]
            if frame_payload["status_flags"] != previous["status_flags"]:
                delta["status_flags"] = frame_payload["status_flags"]
            if include_memory_deltas and frame_payload["memory_delta_ids"]:
                delta["memory_delta_ids"] = frame_payload["memory_delta_ids"]
        if delta:
            by_tick[frame.tick]["deltas"][frame.agent_id] = delta
        last_by_agent[frame.agent_id] = {
            "position": frame_payload["position"],
            "status_flags": frame_payload["status_flags"],
        }
    for tick in range(config.tick_count):
        frames.append(by_tick[tick])
    return frames


def _memory_delta_content(memory_id: str) -> str:
    if "-msg" in memory_id:
        return "Received a deterministic encounter note from a nearby simulated agent."
    return "Updated routine memory after one replay tick in the Gangnam-style grid."


def _demographics(agent_id: str, role: str) -> dict[str, Any]:
    index = int(agent_id.rsplit("-", 1)[1])
    return {
        "age_band": ("20s", "30s", "40s", "50s")[index % 4],
        "commute_pattern": ("transit", "walking", "mixed")[index % 3],
        "role_tag": role,
    }


def _stable_int(*parts: object) -> int:
    text = ":".join(str(part) for part in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


if __name__ == "__main__":
    main()
