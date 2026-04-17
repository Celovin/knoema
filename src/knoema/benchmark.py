"""Deterministic benchmark utilities for Knoema simulation runs."""

from __future__ import annotations

import json
import platform
import statistics
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime

from knoema.environment import Environment
from knoema.llm import LocalClient
from knoema.persona import Persona
from knoema.protocols import Message
from knoema.simulator import Simulator
from knoema.types import Personality, WorldEvent

BASE_AGENT_SPECS: tuple[tuple[str, str, int, str, str], ...] = (
    ("mira", "Mira", 34, "Village clinic nurse who checks on elders before lunch.", "clinic"),
    ("jun", "Jun", 42, "Bakery owner who opens early and trades local news.", "bakery"),
    ("sol", "Sol", 28, "Irrigation engineer maintaining the central well.", "well"),
    ("hani", "Hani", 19, "Apprentice courier moving notices across the village.", "square"),
    ("toma", "Toma", 51, "Retired guard watching the bridge and mentoring others.", "bridge"),
    ("nari", "Nari", 39, "School teacher preparing a harvest lesson.", "school"),
    ("eden", "Eden", 45, "Carpenter repairing stalls before the market.", "workshop"),
    ("rhea", "Rhea", 31, "Market organizer tracking supplies and stall assignments.", "market"),
    ("ori", "Ori", 23, "Archivist collecting oral histories from villagers.", "archive"),
    ("sena", "Sena", 67, "Village elder keeping weather and conflict records.", "elder_house"),
)


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    """Configuration for a deterministic village benchmark."""

    agent_count: int = 10
    duration_days: int = 1
    tick_minutes: int = 60
    repetitions: int = 3
    scenario_name: str = "village-10-hourly"

    def __post_init__(self) -> None:
        if self.agent_count < 1:
            raise ValueError("agent_count must be positive")
        if self.duration_days < 1:
            raise ValueError("duration_days must be positive")
        if self.tick_minutes < 1:
            raise ValueError("tick_minutes must be positive")
        if self.repetitions < 1:
            raise ValueError("repetitions must be positive")
        if not self.scenario_name.strip():
            raise ValueError("scenario_name must not be blank")

    @property
    def tick_count(self) -> int:
        return int((self.duration_days * 24 * 60) / self.tick_minutes)

    @property
    def expected_action_count(self) -> int:
        return self.agent_count * self.tick_count

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    """One timed benchmark repetition."""

    repetition: int
    wall_time_seconds: float
    action_count: int
    actions_per_second: float
    relationship_edges: int

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Aggregated benchmark output."""

    engine: str
    config: BenchmarkConfig
    runs: list[BenchmarkRun]
    python_version: str
    platform: str

    @property
    def median_wall_time_seconds(self) -> float:
        return statistics.median(run.wall_time_seconds for run in self.runs)

    @property
    def mean_wall_time_seconds(self) -> float:
        return statistics.fmean(run.wall_time_seconds for run in self.runs)

    @property
    def median_actions_per_second(self) -> float:
        return statistics.median(run.actions_per_second for run in self.runs)

    @property
    def best_actions_per_second(self) -> float:
        return max(run.actions_per_second for run in self.runs)

    @property
    def action_count(self) -> int:
        return self.runs[0].action_count

    @property
    def relationship_edges(self) -> int:
        return self.runs[-1].relationship_edges

    def to_json_dict(self) -> dict[str, object]:
        return {
            "engine": self.engine,
            "config": self.config.to_json_dict(),
            "runs": [run.to_json_dict() for run in self.runs],
            "summary": {
                "median_wall_time_seconds": self.median_wall_time_seconds,
                "mean_wall_time_seconds": self.mean_wall_time_seconds,
                "median_actions_per_second": self.median_actions_per_second,
                "best_actions_per_second": self.best_actions_per_second,
                "action_count": self.action_count,
                "relationship_edges": self.relationship_edges,
            },
            "environment": {
                "python_version": self.python_version,
                "platform": self.platform,
            },
        }


@dataclass(frozen=True, slots=True)
class ComparisonRow:
    """A measured or placeholder row in a cross-framework benchmark table."""

    framework: str
    status: str
    scenario: str
    agent_count: int | None
    action_count: int | None
    median_wall_time_seconds: float | None
    actions_per_second: float | None
    notes: str


def build_village_personas(agent_count: int) -> list[Persona]:
    """Create deterministic village personas for benchmarks."""

    if agent_count < 1:
        raise ValueError("agent_count must be positive")
    personas: list[Persona] = []
    for index in range(agent_count):
        agent_id, name, age, background, role = _agent_spec(index)
        personas.append(
            Persona(
                agent_id=agent_id,
                name=name,
                age=age,
                background=background,
                personality=_personality_for_index(index),
                values=["reliability", "local trust", "mutual aid"],
                goals=[f"complete the {role} routine", "coordinate with a neighbor"],
            )
        )
    return personas


def run_knoema_benchmark(config: BenchmarkConfig | None = None) -> BenchmarkReport:
    """Run the deterministic Knoema village benchmark."""

    resolved_config = config or BenchmarkConfig()
    runs = [_run_once(resolved_config, repetition) for repetition in range(1, resolved_config.repetitions + 1)]
    return BenchmarkReport(
        engine="Knoema",
        config=resolved_config,
        runs=runs,
        python_version=platform.python_version(),
        platform=platform.platform(),
    )


def build_comparison_rows(
    report: BenchmarkReport,
    *,
    reference_frameworks: Sequence[str] = ("Concordia", "Mesa"),
) -> list[ComparisonRow]:
    """Build a transparent comparison table without inventing external measurements."""

    rows = [
        ComparisonRow(
            framework=report.engine,
            status="measured",
            scenario=report.config.scenario_name,
            agent_count=report.config.agent_count,
            action_count=report.action_count,
            median_wall_time_seconds=report.median_wall_time_seconds,
            actions_per_second=report.median_actions_per_second,
            notes="Deterministic LocalClient, shared Knoema simulator path.",
        )
    ]
    rows.extend(
        ComparisonRow(
            framework=framework,
            status="not-measured",
            scenario=report.config.scenario_name,
            agent_count=None,
            action_count=None,
            median_wall_time_seconds=None,
            actions_per_second=None,
            notes="External framework adapter is not bundled; run an equivalent scenario separately.",
        )
        for framework in reference_frameworks
    )
    return rows


def format_markdown_report(report: BenchmarkReport) -> str:
    """Render a compact Markdown benchmark report."""

    rows = build_comparison_rows(report)
    lines = [
        "# Knoema Benchmark Report",
        "",
        f"Scenario: `{report.config.scenario_name}`",
        f"Agents: {report.config.agent_count}",
        f"Ticks: {report.config.tick_count}",
        f"Actions: {report.action_count}",
        f"Repetitions: {report.config.repetitions}",
        "",
        "## Summary",
        "",
        f"- Median wall time: {_format_float(report.median_wall_time_seconds)} seconds",
        f"- Mean wall time: {_format_float(report.mean_wall_time_seconds)} seconds",
        f"- Median throughput: {_format_float(report.median_actions_per_second)} actions/sec",
        f"- Relationship edges: {report.relationship_edges}",
        "",
        "## Framework Comparison",
        "",
        "| Framework | Status | Scenario | Agents | Actions | Median seconds | Actions/sec | Notes |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.framework,
                    row.status,
                    row.scenario,
                    _format_optional_int(row.agent_count),
                    _format_optional_int(row.action_count),
                    _format_optional_float(row.median_wall_time_seconds),
                    _format_optional_float(row.actions_per_second),
                    row.notes,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Environment",
            "",
            f"- Python: {report.python_version}",
            f"- Platform: {report.platform}",
        ]
    )
    return "\n".join(lines) + "\n"


def _run_once(config: BenchmarkConfig, repetition: int) -> BenchmarkRun:
    personas = build_village_personas(config.agent_count)
    role_by_agent = {persona.agent_id: _agent_spec(index)[4] for index, persona in enumerate(personas)}
    partner_by_agent = _partner_map([persona.agent_id for persona in personas])
    environment = _build_environment(role_by_agent)
    simulator = Simulator(
        agents=personas,
        environment=environment,
        tick_duration_minutes=config.tick_minutes,
        llm=LocalClient(_make_village_responder(role_by_agent, partner_by_agent)),
    )
    simulator.scheduler.schedule(_public_event([persona.agent_id for persona in personas]))

    start = time.perf_counter()
    logs = simulator.run(duration_days=config.duration_days)
    elapsed = time.perf_counter() - start

    if len(logs) != config.expected_action_count:
        raise RuntimeError(
            f"expected {config.expected_action_count} actions, observed {len(logs)}"
        )
    elapsed_for_rate = elapsed if elapsed > 0 else 1e-12
    return BenchmarkRun(
        repetition=repetition,
        wall_time_seconds=elapsed,
        action_count=len(logs),
        actions_per_second=len(logs) / elapsed_for_rate,
        relationship_edges=simulator.relationships.to_networkx().number_of_edges(),
    )


def _agent_spec(index: int) -> tuple[str, str, int, str, str]:
    if index < len(BASE_AGENT_SPECS):
        return BASE_AGENT_SPECS[index]
    agent_number = index + 1
    return (
        f"agent_{agent_number}",
        f"Agent {agent_number}",
        24 + (index % 35),
        f"Village resident {agent_number} with a rotating civic role.",
        f"station_{agent_number}",
    )


def _personality_for_index(index: int) -> Personality:
    return Personality(
        openness=0.55 + (index % 3) * 0.08,
        conscientiousness=0.62 + (index % 4) * 0.05,
        extraversion=0.42 + (index % 5) * 0.07,
        agreeableness=0.58 + (index % 3) * 0.09,
        neuroticism=0.18 + (index % 4) * 0.04,
    )


def _partner_map(agent_ids: Sequence[str]) -> dict[str, str]:
    return {
        agent_id: agent_ids[(index + 1) % len(agent_ids)]
        for index, agent_id in enumerate(agent_ids)
    }


def _build_environment(role_by_agent: Mapping[str, str]) -> Environment:
    environment = Environment(
        start_time=datetime(2026, 6, 1, 7, 0),
        location_path=("Knoema Demo World", "Harbor Village", "Central Square"),
        conditions={"weather": "clear", "festival_day": True, "market_pressure": "moderate"},
    )
    for agent_id, role in role_by_agent.items():
        environment.set_agent_location(
            agent_id,
            ("Knoema Demo World", "Harbor Village", role.replace("_", " ").title()),
        )
    return environment


def _public_event(agent_ids: Sequence[str]) -> WorldEvent:
    return WorldEvent(
        timestamp=datetime(2026, 6, 1, 12, 0),
        event_type="village.announcement",
        participants=list(agent_ids),
        location="Knoema Demo World > Harbor Village > Central Square",
        description="Noon bell: evening market preparation starts after lunch.",
    )


def _make_village_responder(
    role_by_agent: Mapping[str, str],
    partner_by_agent: Mapping[str, str],
) -> Callable[[Sequence[Message]], str]:
    def respond(messages: Sequence[Message]) -> str:
        system_prompt = _message_content(messages[0]) if messages else ""
        user_prompt = _message_content(messages[-1]) if messages else ""
        agent_id = _line_value(system_prompt, "Persona ID: ") or "unknown"
        hour = _hour_from_prompt(user_prompt)
        partner = partner_by_agent.get(agent_id)
        role = role_by_agent.get(agent_id, "routine")

        if hour < 9:
            payload = {
                "action_type": "prepare",
                "target": None,
                "content": f"{agent_id} opens the {role} station and checks supplies.",
            }
        elif hour < 12:
            payload = {
                "action_type": "coordinate",
                "target": partner,
                "content": f"{agent_id} coordinates morning work with {partner}.",
            }
        elif hour < 15:
            payload = {
                "action_type": "respond",
                "target": partner,
                "content": f"{agent_id} responds to the noon announcement with {partner}.",
            }
        elif hour < 18:
            payload = {
                "action_type": "deliver",
                "target": partner,
                "content": f"{agent_id} delivers an update from the {role} station to {partner}.",
            }
        else:
            payload = {
                "action_type": "reflect",
                "target": None,
                "content": f"{agent_id} records the day outcome for tomorrow.",
            }
        return json.dumps(payload)

    return respond


def _message_content(message: Message) -> str:
    return str(message.get("content", ""))


def _line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def _hour_from_prompt(user_prompt: str) -> int:
    timestamp_text = _line_value(user_prompt, "Time: ")
    if timestamp_text is None:
        return 0
    return datetime.fromisoformat(timestamp_text).hour


def _format_optional_int(value: int | None) -> str:
    return "-" if value is None else str(value)


def _format_optional_float(value: float | None) -> str:
    return "-" if value is None else _format_float(value)


def _format_float(value: float) -> str:
    return f"{value:.6f}"


__all__ = [
    "BenchmarkConfig",
    "BenchmarkReport",
    "BenchmarkRun",
    "ComparisonRow",
    "build_comparison_rows",
    "build_village_personas",
    "format_markdown_report",
    "run_knoema_benchmark",
]
