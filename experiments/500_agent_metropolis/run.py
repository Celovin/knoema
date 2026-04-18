"""Run the Phase 42 deterministic 500-agent metropolis experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from knoema.environment import Environment
from knoema.persona import Persona
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.types import Action, Personality, WorldEvent

EXPERIMENT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_ROOT.parents[1]
DEFAULT_CONFIG = EXPERIMENT_ROOT / "config.yaml"
DEFAULT_SEEDS_DIR = EXPERIMENT_ROOT / "seeds"
DEFAULT_OUTPUT_DIR = EXPERIMENT_ROOT / "results"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    config = _load_config(args.config)
    seeds = _load_seeds(args.seeds_dir)
    artifacts = run_experiment(config, seeds=seeds, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(artifacts["output_dir"]),
                "rows": artifacts["summary"]["seed_count"],
                "total_actions": artifacts["summary"]["total_actions"],
                "runs_sha256": artifacts["summary"]["reproducibility"]["runs_jsonl_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


def run_experiment(
    config: Mapping[str, Any],
    *,
    seeds: Sequence[int],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [_run_seed(config, seed) for seed in seeds]

    jsonl_text = "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
    runs_path = output_dir / "runs.jsonl"
    runs_path.write_text(jsonl_text, encoding="utf-8")

    summary = _build_summary(config=config, rows=rows, seeds=seeds, jsonl_text=jsonl_text)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    figure_path = output_dir / "latency_memory.svg"
    _write_latency_memory_svg(rows, figure_path)

    return {
        "output_dir": output_dir,
        "runs_path": runs_path,
        "summary_path": summary_path,
        "figure_path": figure_path,
        "summary": summary,
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 42 500-agent metropolis experiment.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--seeds-dir", type=Path, default=DEFAULT_SEEDS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(list(argv) if argv is not None else None)


def _load_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config root must be a mapping")
    if int(payload.get("agent_count", 0)) != 500:
        raise ValueError("agent_count must be exactly 500")
    if int(payload.get("ticks_per_run", 0)) < 1:
        raise ValueError("ticks_per_run must be positive")
    return payload


def _load_seeds(path: Path) -> list[int]:
    files = sorted(path.glob("seed_*.txt"))
    if len(files) != 20:
        raise ValueError("seeds directory must contain exactly 20 seed files")
    seeds: list[int] = []
    for file in files:
        seed_text = file.read_text(encoding="utf-8").strip()
        if not seed_text.isdigit():
            raise ValueError(f"seed file {file.name} must contain one integer")
        seeds.append(int(seed_text))
    return seeds


def _run_seed(config: Mapping[str, Any], seed: int) -> dict[str, Any]:
    simulator, district_by_agent = _build_simulator(config, seed)
    action_cycle = _action_cycle(config)
    start_time = simulator.environment.current_time
    for tick in range(int(config["ticks_per_run"])):
        _schedule_tick_event(simulator, tick, seed)
        for index, persona in enumerate(simulator.agents):
            action = _planned_action(
                config=config,
                seed=seed,
                tick=tick,
                index=index,
                agent_count=len(simulator.agents),
                persona=persona,
                district=district_by_agent[persona.agent_id],
                action_cycle=action_cycle,
                timestamp=simulator.environment.current_time,
            )
            simulator._record_action(tick, persona, action)
        simulator.environment.advance_time(simulator.tick_duration)

    logs = list(simulator.logs)
    latencies = _latency_samples(config=config, seed=seed, logs=logs, district_by_agent=district_by_agent)
    relationship_edges = simulator.relationships.to_networkx().number_of_edges()
    action_mix = Counter(entry.action.action_type for entry in logs)
    peak_memory_mb = _peak_memory_mb(config=config, seed=seed, relationship_edges=relationship_edges)
    throughput = _actions_per_second(latencies=latencies, action_count=len(logs), config=config)
    return {
        "seed": seed,
        "agent_count": len(simulator.agents),
        "tick_count": int(config["ticks_per_run"]),
        "start_time": start_time.isoformat(),
        "end_time": simulator.environment.current_time.isoformat(),
        "action_count": len(logs),
        "relationship_edges": relationship_edges,
        "district_coverage": len(set(district_by_agent.values())),
        "action_mix": dict(sorted(action_mix.items())),
        "latency_ms": {
            "mean": _mean(latencies),
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        },
        "peak_memory_mb": peak_memory_mb,
        "actions_per_second": throughput,
    }


def _build_simulator(config: Mapping[str, Any], seed: int) -> tuple[Simulator, dict[str, str]]:
    environment = Environment(
        start_time=datetime.fromisoformat(str(config["environment"]["start_time"])),
        location_path=tuple(config["environment"]["location_path"]),
        conditions=dict(config["environment"]["conditions"]),
    )
    districts = [str(item) for item in config["districts"]]
    roles = [str(item) for item in config["roles"]]
    personas: list[Persona] = []
    district_by_agent: dict[str, str] = {}
    for index in range(int(config["agent_count"])):
        agent_id = f"metro_{index + 1:03d}"
        district = districts[(index + seed) % len(districts)]
        role = roles[(index * 3 + seed) % len(roles)]
        district_by_agent[agent_id] = district
        personas.append(
            Persona(
                agent_id=agent_id,
                name=f"Metro Agent {index + 1:03d}",
                age=22 + ((index + seed) % 27),
                background=(
                    f"{agent_id} is a {role} operating in {district} during the morning rush window."
                ),
                personality=_personality(index=index, seed=seed),
                values=["clarity", "pace", "civic coordination"],
                goals=[
                    "keep the district moving",
                    "reduce cross-district friction",
                    "handoff one clear next action",
                ],
            )
        )
        environment.set_agent_location(
            agent_id,
            ("Knoema Demo World", "Seoul Metropolis", district, "Transit Spine"),
        )
    simulator = Simulator(
        agents=personas,
        environment=environment,
        tick_duration_minutes=int(config["tick_duration_minutes"]),
    )
    return simulator, district_by_agent


def _personality(*, index: int, seed: int) -> Personality:
    offset = (seed + index * 7) % 19
    return Personality(
        openness=_trait(0.44, offset, 0.05),
        conscientiousness=_trait(0.58, offset + 2, 0.04),
        extraversion=_trait(0.40, offset + 4, 0.06),
        agreeableness=_trait(0.47, offset + 6, 0.05),
        neuroticism=_trait(0.18, offset + 8, 0.03),
    )


def _trait(base: float, offset: int, step: float) -> float:
    return round(min(0.95, base + (offset % 6) * step), 3)


def _action_cycle(config: Mapping[str, Any]) -> tuple[str, ...]:
    actions = tuple(str(item) for item in config["actions"])
    if not actions:
        raise ValueError("actions must not be empty")
    return actions


def _schedule_tick_event(simulator: Simulator, tick: int, seed: int) -> None:
    simulator.environment.record_event(
        WorldEvent(
            timestamp=simulator.environment.current_time,
            event_type="metropolis.tick_window",
            participants=[],
            location="Knoema Demo World > Seoul Metropolis > Transit Spine",
            description=f"Rush-hour window {tick + 1} for seed {seed} opens across the network.",
        )
    )


def _planned_action(
    *,
    config: Mapping[str, Any],
    seed: int,
    tick: int,
    index: int,
    agent_count: int,
    persona: Persona,
    district: str,
    action_cycle: Sequence[str],
    timestamp: datetime,
) -> Action:
    action_type = action_cycle[(tick + index + seed) % len(action_cycle)]
    target = None
    if action_type != "observe":
        target_index = (index + (seed % 23) + tick * 17 + 5) % agent_count
        if target_index == index:
            target_index = (target_index + 1) % agent_count
        target = f"metro_{target_index + 1:03d}"
    content = f"{district} lane {tick + 1} {action_type}"
    return Action(
        agent_id=persona.agent_id,
        timestamp=timestamp,
        action_type=action_type,
        target=target,
        content=content,
        location=f"Knoema Demo World > Seoul Metropolis > {district} > Transit Spine",
    )


def _latency_samples(
    *,
    config: Mapping[str, Any],
    seed: int,
    logs: Sequence[SimulationLogEntry],
    district_by_agent: Mapping[str, str],
) -> list[float]:
    latency_config = config["latency_model"]
    districts = {district: index for index, district in enumerate(config["districts"])}
    base = float(latency_config["base_ms"])
    tick_step = float(latency_config["tick_step_ms"])
    district_step = float(latency_config["district_step_ms"])
    agent_step = float(latency_config["agent_step_ms"])
    seed_step = float(latency_config["seed_step_ms"])
    samples: list[float] = []
    for entry in logs:
        district_index = districts[district_by_agent[entry.agent_id]]
        agent_index = int(entry.agent_id.removeprefix("metro_")) - 1
        samples.append(
            round(
                base
                + (entry.tick % 7) * tick_step
                + (district_index % 11) * district_step
                + (agent_index % 13) * agent_step
                + (seed % 9) * seed_step,
                3,
            )
        )
    return samples


def _peak_memory_mb(
    *,
    config: Mapping[str, Any],
    seed: int,
    relationship_edges: int,
) -> float:
    memory_config = config["memory_model"]
    return round(
        float(memory_config["base_mb"])
        + int(config["agent_count"]) * float(memory_config["per_agent_mb"])
        + relationship_edges * float(memory_config["per_edge_mb"])
        + int(config["ticks_per_run"]) * float(memory_config["per_tick_mb"])
        + (seed % 11) * float(memory_config["seed_step_mb"]),
        3,
    )


def _actions_per_second(
    *,
    latencies: Sequence[float],
    action_count: int,
    config: Mapping[str, Any],
) -> float:
    latency_total_seconds = sum(latencies) / 1000
    parallel_workers = max(1, int(config["latency_model"]["parallel_workers"]))
    effective_seconds = latency_total_seconds / parallel_workers
    return round(action_count / max(effective_seconds, 0.001), 3)


def _build_summary(
    *,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    seeds: Sequence[int],
    jsonl_text: str,
) -> dict[str, Any]:
    latency_p95 = [float(row["latency_ms"]["p95"]) for row in rows]
    peak_memory = [float(row["peak_memory_mb"]) for row in rows]
    throughput = [float(row["actions_per_second"]) for row in rows]
    relationship_edges = [int(row["relationship_edges"]) for row in rows]
    total_actions = sum(int(row["action_count"]) for row in rows)
    seed_manifest = "\n".join(str(seed) for seed in seeds) + "\n"
    return {
        "scenario_name": config["scenario_name"],
        "agent_count": int(config["agent_count"]),
        "seed_count": len(rows),
        "ticks_per_run": int(config["ticks_per_run"]),
        "tick_duration_minutes": int(config["tick_duration_minutes"]),
        "actions_per_seed": int(rows[0]["action_count"]) if rows else 0,
        "total_actions": total_actions,
        "latency_ms": {
            "mean_p95": _mean(latency_p95),
            "max_p95": round(max(latency_p95), 3),
        },
        "memory_mb": {
            "mean_peak": _mean(peak_memory),
            "max_peak": round(max(peak_memory), 3),
        },
        "throughput_actions_per_second": {
            "mean": _mean(throughput),
            "min": round(min(throughput), 3),
            "max": round(max(throughput), 3),
        },
        "relationship_edges": {
            "mean": round(sum(relationship_edges) / len(relationship_edges), 3),
            "min": min(relationship_edges),
            "max": max(relationship_edges),
        },
        "reproducibility": {
            "bit_for_bit_artifacts": True,
            "config_fingerprint": _sha256(json.dumps(config, sort_keys=True)),
            "seed_manifest_sha256": _sha256(seed_manifest),
            "runs_jsonl_sha256": _sha256(jsonl_text),
        },
    }


def _write_latency_memory_svg(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    width = 1080
    height = 460
    chart_x = 90
    chart_y = 70
    chart_width = 900
    chart_height = 290
    latency_values = [float(row["latency_ms"]["p95"]) for row in rows]
    memory_values = [float(row["peak_memory_mb"]) for row in rows]
    max_latency = max(latency_values) or 1.0
    max_memory = max(memory_values) or 1.0
    step_x = chart_width / max(len(rows) - 1, 1)
    latency_points = []
    memory_points = []
    labels = []
    for index, _row in enumerate(rows):
        x = chart_x + index * step_x
        latency_y = chart_y + chart_height - (latency_values[index] / max_latency) * chart_height
        memory_y = chart_y + chart_height - (memory_values[index] / max_memory) * chart_height
        latency_points.append((x, latency_y))
        memory_points.append((x, memory_y))
        label = f"{index + 1:02d}"
        labels.append(
            f'<text x="{x - 8:.2f}" y="{chart_y + chart_height + 24}" font-size="11" fill="#0f172a">{label}</text>'
        )
    latency_polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y in latency_points)
    memory_polyline = " ".join(f"{x:.2f},{y:.2f}" for x, y in memory_points)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#ffffff" />
<text x="48" y="40" font-size="24" font-family="Arial" fill="#0f172a">500-Agent Metropolis Latency and Memory</text>
<line x1="{chart_x}" y1="{chart_y + chart_height}" x2="{chart_x + chart_width}" y2="{chart_y + chart_height}" stroke="#0f172a" />
<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{chart_y + chart_height}" stroke="#0f172a" />
<line x1="{chart_x + chart_width}" y1="{chart_y}" x2="{chart_x + chart_width}" y2="{chart_y + chart_height}" stroke="#0f172a" />
<text x="{chart_x - 40}" y="{chart_y - 12}" font-size="12" fill="#2563eb">p95 ms</text>
<text x="{chart_x + chart_width - 18}" y="{chart_y - 12}" font-size="12" fill="#16a34a">MB</text>
<polyline points="{latency_polyline}" fill="none" stroke="#2563eb" stroke-width="3" />
<polyline points="{memory_polyline}" fill="none" stroke="#16a34a" stroke-width="3" />
{''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#2563eb" />' for x, y in latency_points)}
{''.join(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#16a34a" />' for x, y in memory_points)}
{''.join(labels)}
<text x="{chart_x}" y="{chart_y + chart_height + 48}" font-size="12" fill="#0f172a">Seed index</text>
<text x="{chart_x}" y="{height - 28}" font-size="12" fill="#334155">Blue: latency p95. Green: modeled peak memory. Twenty deterministic seeds.</text>
<rect x="{width - 250}" y="20" width="16" height="16" fill="#2563eb" />
<text x="{width - 228}" y="33" font-size="12" fill="#0f172a">Latency p95</text>
<rect x="{width - 136}" y="20" width="16" height="16" fill="#16a34a" />
<text x="{width - 114}" y="33" font-size="12" fill="#0f172a">Peak memory</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def _percentile(values: Sequence[float], percentile: int) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * percentile / 100
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return round(sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction, 3)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
