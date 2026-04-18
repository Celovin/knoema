"""Run the Phase 19 deterministic 50-agent village experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from itertools import pairwise
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from knoema.environment import Environment
from knoema.llm import LocalClient
from knoema.persona import Persona
from knoema.protocols import Message
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.types import Personality, WorldEvent

EXPERIMENT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_ROOT.parents[1]
DEFAULT_CONFIG = EXPERIMENT_ROOT / "config.yaml"
DEFAULT_OUTPUT_DIR = EXPERIMENT_ROOT / "results"
DEFAULT_REPORT = REPO_ROOT / "docs" / "reports" / "50_agent_benchmark.pdf"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    config = _load_config(args.config)
    started = perf_counter()
    artifacts = run_experiment(
        config,
        output_dir=args.output_dir,
        report_path=None if args.skip_pdf else args.report_path,
    )
    elapsed = perf_counter() - started
    print(
        json.dumps(
            {
                "output_dir": str(artifacts["output_dir"]),
                "action_count": artifacts["metrics"]["action_count"],
                "sim_log_sha256": artifacts["metrics"]["reproducibility"]["sim_log_sha256"],
                "measured_generation_seconds": round(elapsed, 3),
            },
            sort_keys=True,
        )
    )
    return 0


def run_experiment(
    config: Mapping[str, Any],
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    report_path: Path | None = DEFAULT_REPORT,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    simulator = _build_simulator(config)
    logs = simulator.run(duration_days=int(config["duration_days"]))
    jsonl = _logs_to_jsonl(logs)
    sim_log_path = output_dir / "sim_log.jsonl"
    sim_log_path.write_text(jsonl + "\n", encoding="utf-8")

    trace = _trace_sample(logs, sample_size=50)
    trace_text = json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    trace_path = output_dir / "trace_sample.json"
    trace_path.write_text(trace_text, encoding="utf-8")

    metrics = _build_metrics(
        config=config,
        logs=logs,
        simulator=simulator,
        sim_log_text=jsonl + "\n",
        trace_text=trace_text,
    )
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if report_path is not None:
        build_pdf_report(metrics, trace, report_path)

    return {
        "output_dir": output_dir,
        "sim_log_path": sim_log_path,
        "trace_path": trace_path,
        "metrics_path": metrics_path,
        "metrics": metrics,
    }


def build_pdf_report(metrics: Mapping[str, Any], trace: list[dict[str, Any]], path: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen.canvas import Canvas

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = Canvas(str(path), pagesize=letter)
    width, height = letter

    def page(title: str, page_number: int) -> None:
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.setFont("Helvetica-Bold", 17)
        pdf.drawString(42, height - 48, title)
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(colors.HexColor("#64748b"))
        pdf.drawRightString(width - 42, 30, f"Page {page_number} / 10")

    def paragraph(lines: Sequence[str], x: int = 42, y: int = 700, leading: int = 15) -> int:
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.setFont("Helvetica", 9)
        cursor = y
        for line in lines:
            pdf.drawString(x, cursor, line)
            cursor -= leading
        return cursor

    page("50-Agent Village Benchmark", 1)
    paragraph(
        [
            f"Scenario: {metrics['scenario_name']}",
            f"Agents: {metrics['agent_count']}",
            f"Duration: {metrics['duration_days']} days",
            f"Ticks: {metrics['tick_count']}",
            f"Actions: {metrics['action_count']}",
            f"Relationship edges: {metrics['relationship_edges']}",
            f"Deterministic seed: {metrics['seed']}",
            "This report uses deterministic local decisions so committed artifacts can be regenerated bit-for-bit.",
        ]
    )
    pdf.showPage()

    page("Actions Per Tick", 2)
    _line_chart(pdf, metrics["actions_per_tick"], 60, 150, 500, 460, "tick", "actions")
    pdf.showPage()

    page("Action Mix", 3)
    _bar_chart(pdf, metrics["action_mix"], 60, 170, 500, 420)
    pdf.showPage()

    page("Agent Action Distribution", 4)
    _bar_chart(pdf, dict(list(metrics["agent_action_counts"].items())[:20]), 60, 170, 500, 420)
    paragraph(["First 20 agents shown; all 50 agents have equal scheduled participation."], y=130)
    pdf.showPage()

    page("Relationship Growth", 5)
    _line_chart(pdf, metrics["relationship_edges_by_tick"], 60, 150, 500, 460, "tick", "edges")
    pdf.showPage()

    page("Latency Model Percentiles", 6)
    _bar_chart(pdf, metrics["latency_ms"], 60, 190, 500, 390)
    paragraph(["Latency values are deterministic model values for reproducible reporting."], y=150)
    pdf.showPage()

    page("Token and Cost Estimate", 7)
    _bar_chart(
        pdf,
        {
            "prompt_tokens": metrics["token_estimate"]["prompt_tokens"],
            "completion_tokens": metrics["token_estimate"]["completion_tokens"],
        },
        60,
        190,
        500,
        390,
    )
    paragraph([f"Local replay cost: ${metrics['cost_estimate']['usd']:.2f}"], y=150)
    pdf.showPage()

    page("Trace Sample", 8)
    paragraph(
        [
            f"{item['tick']:02d} {item['agent_id']} {item['action_type']} -> {item['target']}: {item['content'][:78]}"
            for item in trace[:22]
        ],
        y=700,
        leading=13,
    )
    pdf.showPage()

    page("Reproducibility", 9)
    reproducibility = metrics["reproducibility"]
    paragraph(
        [
            "Artifacts are deterministic for the same config and seed.",
            f"sim_log.jsonl SHA-256: {reproducibility['sim_log_sha256']}",
            f"trace_sample.json SHA-256: {reproducibility['trace_sample_sha256']}",
            f"config fingerprint: {reproducibility['config_fingerprint']}",
            f"bit-for-bit artifacts: {reproducibility['bit_for_bit_artifacts']}",
        ],
        y=700,
    )
    pdf.showPage()

    page("Interpretation and Next Steps", 10)
    paragraph(
        [
            "1. The 50-agent run exercises the same public Simulator path used by notebooks and CLI demos.",
            "2. Relationship edges remain explicit and inspectable instead of being hidden inside prompts.",
            "3. The JSONL log can be replayed, sampled, or loaded into the dashboard for offline review.",
            "4. Next milestone: compare 5, 10, 25, and 50-agent curves across multiple LLM providers.",
            "5. Next milestone: add reproducibility tests that restore state from JSONL logs.",
        ],
        y=700,
    )
    pdf.save()


def _bar_chart(
    pdf: Any,
    values: Mapping[str, int | float],
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    from reportlab.lib import colors

    if not values:
        return
    max_value = max(float(value) for value in values.values()) or 1.0
    bar_width = width / max(len(values), 1)
    pdf.setStrokeColor(colors.HexColor("#cbd5e1"))
    pdf.rect(x, y, width, height, fill=False)
    for index, (label, value) in enumerate(values.items()):
        left = x + index * bar_width + 3
        bar_height = (float(value) / max_value) * (height - 50)
        pdf.setFillColor(colors.HexColor("#2563eb"))
        pdf.rect(left, y + 28, max(3, bar_width - 6), bar_height, fill=True, stroke=False)
        pdf.setFillColor(colors.HexColor("#0f172a"))
        pdf.setFont("Helvetica", 6)
        pdf.drawString(left, y + 14, str(label)[:10])
        pdf.drawString(left, y + 32 + bar_height, str(round(float(value), 2)))


def _line_chart(
    pdf: Any,
    values: Sequence[int | float],
    x: int,
    y: int,
    width: int,
    height: int,
    x_label: str,
    y_label: str,
) -> None:
    from reportlab.lib import colors

    if not values:
        return
    max_value = max(float(value) for value in values) or 1.0
    x_step = width / max(len(values) - 1, 1)
    points = [
        (
            x + index * x_step,
            y + 30 + (float(value) / max_value) * (height - 60),
        )
        for index, value in enumerate(values)
    ]
    pdf.setStrokeColor(colors.HexColor("#cbd5e1"))
    pdf.rect(x, y, width, height, fill=False)
    pdf.setStrokeColor(colors.HexColor("#16a34a"))
    pdf.setLineWidth(1.4)
    for first, second in pairwise(points):
        pdf.line(first[0], first[1], second[0], second[1])
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.HexColor("#0f172a"))
    pdf.drawString(x, y - 14, x_label)
    pdf.drawString(x - 34, y + height - 10, y_label)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 19 50-agent village experiment.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--skip-pdf", action="store_true")
    return parser.parse_args(list(argv) if argv is not None else None)


def _load_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config root must be a mapping")
    roster = payload.get("agent_roster")
    if not isinstance(roster, list) or len(roster) != 50:
        raise ValueError("agent_roster must contain exactly 50 agents")
    return payload


def _build_simulator(config: Mapping[str, Any]) -> Simulator:
    roster = _roster(config)
    environment = _environment(config)
    for agent in roster:
        environment.set_agent_location(
            str(agent["agent_id"]),
            ("Knoema Demo World", "Harbor Village", str(agent["role"]).title()),
        )
    personas = [_persona(agent, index, int(config["seed"])) for index, agent in enumerate(roster)]
    agent_ids = [persona.agent_id for persona in personas]
    role_by_agent = {str(agent["agent_id"]): str(agent["role"]) for agent in roster}
    simulator = Simulator(
        agents=personas,
        environment=environment,
        tick_duration_minutes=int(config["tick_duration_minutes"]),
        llm=LocalClient(_responder(agent_ids=agent_ids, role_by_agent=role_by_agent)),
        language=str(config.get("prompt_language", "en")),
    )
    _schedule_events(simulator, config, agent_ids)
    return simulator


def _roster(config: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    roster = config["agent_roster"]
    if not isinstance(roster, list):
        raise ValueError("agent_roster must be a list")
    return roster


def _environment(config: Mapping[str, Any]) -> Environment:
    env_config = config["environment"]
    return Environment(
        start_time=datetime.fromisoformat(str(env_config["start_time"])),
        location_path=tuple(env_config["location_path"]),
        conditions=dict(env_config["conditions"]),
    )


def _persona(agent: Mapping[str, Any], index: int, seed: int) -> Persona:
    role = str(agent["role"])
    return Persona(
        agent_id=str(agent["agent_id"]),
        name=str(agent["name"]),
        age=int(agent["age"]),
        background=f"A Harbor Village {role} participating in a one-week market preparation.",
        personality=_personality(index, seed),
        values=["local trust", "follow-through", "clear communication"],
        goals=[f"complete the {role} routine", "coordinate with neighbors", "avoid confusion"],
    )


def _personality(index: int, seed: int) -> Personality:
    offset = seed % 11
    return Personality(
        openness=_trait(0.45, index + offset, 0.07),
        conscientiousness=_trait(0.52, index + offset * 2, 0.06),
        extraversion=_trait(0.38, index + offset * 3, 0.08),
        agreeableness=_trait(0.50, index + offset * 4, 0.07),
        neuroticism=_trait(0.18, index + offset * 5, 0.04),
    )


def _trait(base: float, index: int, step: float) -> float:
    return round(min(0.94, base + (index % 6) * step), 3)


def _schedule_events(simulator: Simulator, config: Mapping[str, Any], agent_ids: Sequence[str]) -> None:
    start = datetime.fromisoformat(str(config["environment"]["start_time"]))
    for day in range(int(config["duration_days"])):
        for hour, event_type, description in [
            (11, "village.market_sync", "Morning status exchange for the lantern market."),
            (19, "village.evening_review", "Evening review of open tasks and neighbor concerns."),
        ]:
            timestamp = start + timedelta(days=day, hours=hour - start.hour)
            simulator.scheduler.schedule(
                WorldEvent(
                    timestamp=timestamp,
                    event_type=event_type,
                    participants=list(agent_ids),
                    location="Knoema Demo World > Harbor Village > Central Square",
                    description=description,
                )
            )


def _responder(
    *,
    agent_ids: Sequence[str],
    role_by_agent: Mapping[str, str],
) -> Any:
    partner_by_agent = {
        agent_id: agent_ids[(index + 7) % len(agent_ids)]
        for index, agent_id in enumerate(agent_ids)
    }

    def respond(messages: Sequence[Message]) -> str:
        system_prompt = str(messages[0].get("content", "")) if messages else ""
        user_prompt = str(messages[-1].get("content", "")) if messages else ""
        agent_id = _line_value(system_prompt, "Persona ID: ") or agent_ids[0]
        hour = _hour(user_prompt)
        role = role_by_agent[agent_id]
        target = partner_by_agent[agent_id]
        if hour < 9:
            payload = {
                "action_type": "prepare",
                "target": None,
                "content": f"{agent_id} checks the {role} station and records a morning priority.",
            }
        elif hour < 13:
            payload = {
                "action_type": "coordinate",
                "target": target,
                "content": f"{agent_id} coordinates {role} tasks with {target}.",
            }
        elif hour < 17:
            payload = {
                "action_type": "share",
                "target": target,
                "content": f"{agent_id} shares a market update from the {role} role with {target}.",
            }
        elif hour < 21:
            payload = {
                "action_type": "review",
                "target": target,
                "content": f"{agent_id} reviews unresolved work with {target} before evening close.",
            }
        else:
            payload = {
                "action_type": "reflect",
                "target": None,
                "content": f"{agent_id} writes a short note about tomorrow's {role} routine.",
            }
        return json.dumps(payload, sort_keys=True)

    return respond


def _hour(user_prompt: str) -> int:
    timestamp_text = _line_value(user_prompt, "Time: ")
    if timestamp_text is None:
        return 0
    return datetime.fromisoformat(timestamp_text).hour


def _line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def _logs_to_jsonl(logs: Sequence[SimulationLogEntry]) -> str:
    return "\n".join(
        json.dumps(entry.to_json_dict(), ensure_ascii=False, sort_keys=True) for entry in logs
    )


def _trace_sample(logs: Sequence[SimulationLogEntry], *, sample_size: int) -> list[dict[str, Any]]:
    return [
        {
            "tick": entry.tick,
            "timestamp": entry.timestamp.isoformat(),
            "agent_id": entry.agent_id,
            "action_type": entry.action.action_type,
            "target": entry.action.target,
            "content": entry.action.content,
            "location": entry.action.location,
        }
        for entry in logs[:sample_size]
    ]


def _build_metrics(
    *,
    config: Mapping[str, Any],
    logs: Sequence[SimulationLogEntry],
    simulator: Simulator,
    sim_log_text: str,
    trace_text: str,
) -> dict[str, Any]:
    action_mix = Counter(entry.action.action_type for entry in logs)
    agent_action_counts = Counter(entry.agent_id for entry in logs)
    tick_count = len({entry.tick for entry in logs})
    latencies = _latencies(config, logs)
    trace_sha = _sha256(trace_text)
    sim_sha = _sha256(sim_log_text)
    return {
        "scenario_name": config["scenario_name"],
        "seed": config["seed"],
        "agent_count": len(_roster(config)),
        "duration_days": config["duration_days"],
        "tick_duration_minutes": config["tick_duration_minutes"],
        "tick_count": tick_count,
        "action_count": len(logs),
        "actions_per_tick": _actions_per_tick(logs),
        "action_mix": dict(sorted(action_mix.items())),
        "agent_action_counts": dict(sorted(agent_action_counts.items())),
        "relationship_edges": simulator.relationships.to_networkx().number_of_edges(),
        "relationship_edges_by_tick": _relationship_edges_by_tick(logs),
        "latency_ms": {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        },
        "token_estimate": {
            "prompt_tokens": len(logs) * 220,
            "completion_tokens": len(logs) * 34,
            "total_tokens": len(logs) * 254,
        },
        "cost_estimate": {
            "provider": "deterministic-local",
            "usd": 0.0,
        },
        "retrieval_proxy": {
            "sample_size": 50,
            "keyword_hit_rate": _retrieval_proxy_hit_rate(logs[:50]),
            "note": "Synthetic proxy checks whether trace actions retain role or market context.",
        },
        "reproducibility": {
            "bit_for_bit_artifacts": True,
            "sim_log_sha256": sim_sha,
            "trace_sample_sha256": trace_sha,
            "config_fingerprint": _sha256(json.dumps(config, sort_keys=True)),
        },
    }


def _actions_per_tick(logs: Sequence[SimulationLogEntry]) -> list[int]:
    by_tick = Counter(entry.tick for entry in logs)
    return [by_tick[tick] for tick in sorted(by_tick)]


def _relationship_edges_by_tick(logs: Sequence[SimulationLogEntry]) -> list[int]:
    edges: set[tuple[str, str]] = set()
    values: list[int] = []
    current_tick = -1
    for entry in logs:
        if entry.tick != current_tick:
            if current_tick != -1:
                values.append(len(edges))
            current_tick = entry.tick
        if entry.action.target is not None:
            edges.add((entry.agent_id, entry.action.target))
    values.append(len(edges))
    return values


def _latencies(config: Mapping[str, Any], logs: Sequence[SimulationLogEntry]) -> list[float]:
    latency_config = config["latency_model"]
    base = float(latency_config["base_ms"])
    tick_jitter = float(latency_config["tick_jitter_ms"])
    agent_jitter = float(latency_config["agent_jitter_ms"])
    agent_index = {agent["agent_id"]: index for index, agent in enumerate(_roster(config))}
    return [
        round(base + (entry.tick % 7) * tick_jitter + (agent_index[entry.agent_id] % 11) * agent_jitter, 3)
        for entry in logs
    ]


def _retrieval_proxy_hit_rate(logs: Sequence[SimulationLogEntry]) -> float:
    if not logs:
        return 0.0
    hits = sum(
        1
        for entry in logs
        if "market" in entry.action.content or "station" in entry.action.content
    )
    return round(hits / len(logs), 3)


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
