"""Command line interface for Knoema simulation runs."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from knoema.dsl import collect_validation_issues, load_scenario
from knoema.environment import Environment
from knoema.llm import LocalClient
from knoema.metrics import score_log
from knoema.persona import Persona
from knoema.prompts import PromptLanguage, normalize_prompt_language
from knoema.simulator import Simulator
from knoema.telemetry import (
    NullTelemetryClient,
    TelemetryClient,
    build_cli_properties,
    build_env_telemetry_client,
    telemetry_opt_in_from_env,
)
from knoema.types import Personality, WorldEvent


class CliPersonalityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)

    def to_domain(self) -> Personality:
        return Personality(
            openness=self.openness,
            conscientiousness=self.conscientiousness,
            extraversion=self.extraversion,
            agreeableness=self.agreeableness,
            neuroticism=self.neuroticism,
        )


class CliAgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str
    name: str
    age: int = Field(gt=0)
    background: str
    personality: CliPersonalityConfig
    values: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    location_path: tuple[str, ...] | None = None

    def to_domain(self) -> Persona:
        return Persona(
            agent_id=self.agent_id,
            name=self.name,
            age=self.age,
            background=self.background,
            personality=self.personality.to_domain(),
            values=list(self.values),
            goals=list(self.goals),
        )


class CliEnvironmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: datetime
    location_path: tuple[str, ...]
    conditions: dict[str, Any] = Field(default_factory=dict)

    def to_domain(self) -> Environment:
        return Environment(
            start_time=self.start_time,
            location_path=self.location_path,
            conditions=dict(self.conditions),
        )


class CliEventConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    event_type: str
    participants: list[str]
    location: str
    description: str

    def to_domain(self) -> WorldEvent:
        return WorldEvent(
            timestamp=self.timestamp,
            event_type=self.event_type,
            participants=list(self.participants),
            location=self.location,
            description=self.description,
        )


class CliRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_days: int = Field(default=1, ge=1)
    tick_duration_minutes: int = Field(default=30, ge=1)
    output_path: Path = Path("runs/knoema_cli.jsonl")
    prompt_language: str = "en"


class SimulationRunConfig(BaseModel):
    """YAML schema for `knoema run config.yaml`."""

    model_config = ConfigDict(extra="forbid")

    runtime: CliRuntimeConfig = Field(default_factory=CliRuntimeConfig)
    environment: CliEnvironmentConfig
    agents: list[CliAgentConfig] = Field(min_length=1)
    events: list[CliEventConfig] = Field(default_factory=list)
    local_response: str = '{"action_type": "wait", "target": null, "content": "observes the situation."}'
    description_ko: str | None = None
    description_en: str | None = None
    ethics_tag: str | None = None

    @property
    def prompt_language(self) -> PromptLanguage:
        return normalize_prompt_language(self.runtime.prompt_language)


@dataclass(frozen=True, slots=True)
class CliRunSummary:
    config_path: str
    output_path: str
    agent_count: int
    duration_days: int
    tick_duration_minutes: int
    log_count: int
    scheduled_events: int
    prompt_language: str
    started_at: str
    ended_at: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


def load_run_config(path: str | Path) -> SimulationRunConfig:
    """Load a CLI run config from YAML."""

    config_path = Path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Run config must contain a mapping at the root: {config_path}")
    return SimulationRunConfig.model_validate(payload)


def run_config(
    config_path: str | Path,
    *,
    output_path: str | Path | None = None,
    dry_run: bool = False,
) -> CliRunSummary:
    """Run a simulation from a CLI config file."""

    path = Path(config_path)
    config = load_run_config(path)
    resolved_output = _resolve_output_path(
        output_path=Path(output_path) if output_path is not None else None,
        configured_output=config.runtime.output_path,
        config_dir=path.resolve().parent,
    )
    environment = config.environment.to_domain()
    agents = [agent.to_domain() for agent in config.agents]
    for agent in config.agents:
        if agent.location_path is not None:
            environment.set_agent_location(agent.agent_id, agent.location_path)

    simulator = Simulator(
        agents=agents,
        environment=environment,
        tick_duration_minutes=config.runtime.tick_duration_minutes,
        llm=LocalClient(lambda messages: config.local_response),
        language=config.prompt_language,
    )
    for event in config.events:
        simulator.scheduler.schedule(event.to_domain())

    if not dry_run:
        simulator.run(duration_days=config.runtime.duration_days)
        simulator.export_logs(resolved_output)

    return CliRunSummary(
        config_path=str(path),
        output_path=str(resolved_output),
        agent_count=len(agents),
        duration_days=config.runtime.duration_days,
        tick_duration_minutes=config.runtime.tick_duration_minutes,
        log_count=len(simulator.logs),
        scheduled_events=len(config.events),
        prompt_language=config.prompt_language,
        started_at=config.environment.start_time.isoformat(),
        ended_at=environment.current_time.isoformat(),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="knoema", description="Knoema Engine CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a simulation from a YAML config.")
    run_parser.add_argument("config", type=Path, help="Path to a Knoema run YAML config.")
    run_parser.add_argument("--output", type=Path, default=None, help="Override JSONL output path.")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and print a summary without running or writing logs.",
    )
    run_parser.add_argument("--json", action="store_true", help="Print summary as JSON.")
    run_parser.add_argument(
        "--telemetry",
        action="store_true",
        help="Opt in to anonymous usage telemetry for this command.",
    )

    score_parser = subparsers.add_parser("score", help="Score a JSONL simulation log.")
    score_parser.add_argument("logfile", type=Path, help="Path to a JSONL simulation log.")

    validate_parser = subparsers.add_parser("validate", help="Validate Scenario DSL YAML files.")
    validate_parser.add_argument("path", type=Path, help="Scenario YAML file or directory.")
    validate_parser.add_argument("--json", action="store_true", help="Print validation results as JSON.")
    return parser


def main(
    argv: Sequence[str] | None = None,
    telemetry_client: TelemetryClient | NullTelemetryClient | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "run":
        telemetry = _resolve_telemetry_client(
            force_enable=args.telemetry,
            provided_client=telemetry_client,
        )
        base_properties = build_cli_properties(
            dry_run=args.dry_run,
            json_output=args.json,
        )
        telemetry.capture("cli_run_requested", properties=base_properties)
        try:
            summary = run_config(args.config, output_path=args.output, dry_run=args.dry_run)
        except Exception:
            telemetry.capture("cli_run_failed", properties=base_properties)
            raise
        summary_properties = build_cli_properties(
            dry_run=args.dry_run,
            json_output=args.json,
            agent_count=summary.agent_count,
            duration_days=summary.duration_days,
            tick_duration_minutes=summary.tick_duration_minutes,
            scheduled_events=summary.scheduled_events,
            log_count=summary.log_count,
            prompt_language=summary.prompt_language,
        )
        telemetry.capture("cli_run_completed", properties=summary_properties)
        if args.json:
            print(json.dumps(summary.to_json_dict(), ensure_ascii=False, sort_keys=True))
        else:
            print(
                f"Wrote {summary.log_count} actions for {summary.agent_count} agents "
                f"to {summary.output_path}"
            )
        telemetry.capture("cli_summary_emitted", properties=summary_properties)
        return 0
    if args.command == "score":
        payload = score_log(args.logfile)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "validate":
        payload = validate_scenario_path(args.path)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(
                f"Validated {payload['validated']} scenario files; "
                f"{payload['failed']} failed."
            )
        return 0 if payload["failed"] == 0 else 1
    parser.error(f"Unknown command: {args.command}")
    return 2


def _resolve_output_path(
    *,
    output_path: Path | None,
    configured_output: Path,
    config_dir: Path,
) -> Path:
    selected = output_path or configured_output
    if selected.is_absolute():
        return selected
    if output_path is not None:
        return Path.cwd() / selected
    return config_dir / selected


def validate_scenario_path(path: str | Path) -> dict[str, Any]:
    """Validate a Scenario DSL file or all YAML files under a directory."""

    target = Path(path)
    scenario_files = _discover_scenario_files(target)
    results: list[dict[str, Any]] = []
    failed = 0
    for scenario_file in scenario_files:
        try:
            scenario = load_scenario(scenario_file)
            issues = [
                {"path": issue.path, "message": issue.message, "code": issue.code}
                for issue in collect_validation_issues(scenario)
            ]
        except Exception as exc:  # pragma: no cover - defensive CLI surface
            issues = [{"path": str(scenario_file), "message": str(exc), "code": "load_error"}]
        if issues:
            failed += 1
        results.append(
            {
                "path": str(scenario_file),
                "ok": not issues,
                "issues": issues,
            }
        )
    return {
        "path": str(target),
        "validated": len(scenario_files),
        "failed": failed,
        "results": results,
    }


def _discover_scenario_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(f"scenario path does not exist: {path}")
    files = sorted({*path.rglob("*.yaml"), *path.rglob("*.yml")})
    if not files:
        raise ValueError(f"no scenario YAML files found under: {path}")
    return files


def _resolve_telemetry_client(
    *,
    force_enable: bool,
    provided_client: TelemetryClient | NullTelemetryClient | None,
) -> TelemetryClient | NullTelemetryClient:
    if not force_enable and not telemetry_opt_in_from_env():
        return NullTelemetryClient()
    if provided_client is not None:
        return provided_client
    return build_env_telemetry_client(force_enable=True)


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CliRunSummary",
    "SimulationRunConfig",
    "build_parser",
    "load_run_config",
    "main",
    "run_config",
    "validate_scenario_path",
]
