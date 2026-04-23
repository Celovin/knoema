"""Command line interface for Luvoire simulation runs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

from luvoire.core.replay_cache import inspect_replay_cache
from luvoire.customer_cli import add_customer_subparser, handle_customer_command
from luvoire.dsl import collect_validation_issues, load_scenario
from luvoire.environment import Environment
from luvoire.evaluation import grade_trace_report
from luvoire.export import export_odd_markdown, export_run_log_parquet, query_run_parquet
from luvoire.game.schedule import RoutineEntry
from luvoire.llm import LocalClient
from luvoire.metrics import score_log
from luvoire.persona import Persona
from luvoire.prompts import PromptLanguage, normalize_prompt_language
from luvoire.reproducibility import VerificationReport, verify_run_fingerprint
from luvoire.simulator import Simulator
from luvoire.telemetry import (
    NullTelemetryClient,
    TelemetryClient,
    build_cli_properties,
    build_env_telemetry_client,
    telemetry_opt_in_from_env,
)
from luvoire.types import Personality, WorldEvent

PLAYGROUND_SCENARIOS: tuple[dict[str, str], ...] = (
    {"name": "Dorm: two agents", "filename": "dorm_two_agents.yaml"},
    {"name": "Village: ten agents", "filename": "village_ten.yaml"},
    {"name": "School corridor", "filename": "school_corridor.yaml"},
    {"name": "Office team conflict", "filename": "office_team_conflict.yaml"},
    {"name": "Family dinner table", "filename": "family_dinner_table.yaml"},
    {"name": "Cafe first meeting", "filename": "cafe_first_meeting.yaml"},
    {"name": "Subway rush crowd", "filename": "subway_rush_crowd.yaml"},
    {"name": "School group project", "filename": "school_group_project.yaml"},
    {"name": "Apartment neighbor dispute", "filename": "apartment_neighbor_dispute.yaml"},
    {"name": "Volunteer cleanup team", "filename": "volunteer_cleanup_team.yaml"},
    {"name": "Startup pivot meeting", "filename": "startup_pivot_meeting.yaml"},
    {"name": "Late-night convenience store", "filename": "late_night_convenience_store.yaml"},
    {"name": "Book club debate", "filename": "book_club_debate.yaml"},
    {"name": "Hospital waiting room", "filename": "hospital_waiting_room.yaml"},
    {"name": "Neighborhood festival", "filename": "neighborhood_festival.yaml"},
    {"name": "Classroom pop quiz", "filename": "classroom_pop_quiz.yaml"},
    {"name": "Religious service", "filename": "religious_service.yaml"},
    {"name": "Military barracks morning", "filename": "military_barracks_morning.yaml"},
    {"name": "ER triage", "filename": "er_triage.yaml"},
    {"name": "Courtroom jury deliberation", "filename": "courtroom_jury_deliberation.yaml"},
    {"name": "Election rally", "filename": "election_rally.yaml"},
    {"name": "Refugee shelter arrival", "filename": "refugee_shelter_arrival.yaml"},
    {"name": "Tech demo day", "filename": "tech_demo_day.yaml"},
    {"name": "Wedding after-party", "filename": "wedding_after_party.yaml"},
    {"name": "Funeral wake", "filename": "funeral_wake.yaml"},
    {"name": "Prison yard (fictional)", "filename": "prison_yard_fictional.yaml"},
    {"name": "Zoom team standup", "filename": "zoom_team_standup.yaml"},
    {"name": "Kindergarten storytime", "filename": "kindergarten_storytime.yaml"},
    {"name": "Senior center chess", "filename": "senior_center_chess.yaml"},
    {"name": "Concert lobby intermission", "filename": "concert_lobby_intermission.yaml"},
)


class CliPersonalityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)
    honesty_humility: float = Field(default=0.5, ge=0.0, le=1.0)
    machiavellianism: float = Field(default=0.0, ge=0.0, le=1.0)
    narcissism: float = Field(default=0.0, ge=0.0, le=1.0)
    psychopathy: float = Field(default=0.0, ge=0.0, le=1.0)
    sadism: float = Field(default=0.0, ge=0.0, le=1.0)
    kantianism: float = Field(default=0.5, ge=0.0, le=1.0)
    humanism: float = Field(default=0.5, ge=0.0, le=1.0)
    faith_in_humanity: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    locus_of_control: float = Field(default=0.5, ge=0.0, le=1.0)
    need_for_cognition: float = Field(default=0.5, ge=0.0, le=1.0)
    trait_empathy: float = Field(default=0.5, ge=0.0, le=1.0)
    care_harm: float = Field(default=0.5, ge=0.0, le=1.0)
    fairness: float = Field(default=0.5, ge=0.0, le=1.0)
    binding_morals: float = Field(default=0.5, ge=0.0, le=1.0)
    self_direction: float = Field(default=0.5, ge=0.0, le=1.0)
    stimulation: float = Field(default=0.5, ge=0.0, le=1.0)
    hedonism: float = Field(default=0.5, ge=0.0, le=1.0)
    achievement: float = Field(default=0.5, ge=0.0, le=1.0)
    power: float = Field(default=0.5, ge=0.0, le=1.0)
    security: float = Field(default=0.5, ge=0.0, le=1.0)
    conformity: float = Field(default=0.5, ge=0.0, le=1.0)
    tradition: float = Field(default=0.5, ge=0.0, le=1.0)
    benevolence: float = Field(default=0.5, ge=0.0, le=1.0)
    universalism: float = Field(default=0.5, ge=0.0, le=1.0)

    def to_domain(self) -> Personality:
        return Personality(**self.model_dump())


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
    routine: list[CliRoutineEntryConfig] = Field(default_factory=list)

    def to_domain(self) -> Persona:
        return Persona(
            agent_id=self.agent_id,
            name=self.name,
            age=self.age,
            background=self.background,
            personality=self.personality.to_domain(),
            values=list(self.values),
            goals=list(self.goals),
            routine=[entry.to_domain() for entry in self.routine] or None,
        )


class CliRoutineEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_hour: int = Field(ge=0, le=24)
    end_hour: int = Field(ge=0, le=24)
    location_path: tuple[str, ...] = Field(min_length=1)
    default_action: str = Field(min_length=1)
    default_target: str | None = None

    def to_domain(self) -> RoutineEntry:
        return RoutineEntry(
            start_hour=self.start_hour,
            end_hour=self.end_hour,
            location_path=self.location_path,
            default_action=self.default_action,
            default_target=self.default_target,
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
    output_path: Path = Path("runs/luvoire_cli.jsonl")
    prompt_language: str = "en"


CliAgentConfig.model_rebuild()


class SimulationRunConfig(BaseModel):
    """YAML schema for `luvoire run config.yaml`."""

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
    parser = argparse.ArgumentParser(prog="luvoire", description="Luvoire CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a simulation from a YAML config.")
    run_parser.add_argument("config", type=Path, help="Path to a Luvoire run YAML config.")
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

    export_parser = subparsers.add_parser("export", help="Export scenario-derived artifacts.")
    export_subparsers = export_parser.add_subparsers(dest="export_command", required=True)
    odd_parser = export_subparsers.add_parser("odd", help="Export a Grimm 2020 ODD markdown report.")
    odd_parser.add_argument("scenario", type=Path, help="Scenario DSL YAML file.")
    odd_parser.add_argument("--out", type=Path, required=True, help="Output markdown path.")
    parquet_parser = export_subparsers.add_parser(
        "parquet",
        help="Export a Luvoire JSONL run log as analytics Parquet.",
    )
    parquet_parser.add_argument("logfile", type=Path, help="Input Luvoire JSONL run log.")
    parquet_parser.add_argument("--out", type=Path, required=True, help="Output Parquet path.")

    list_parser = subparsers.add_parser("list-scenarios", help="List packaged Playground scenarios.")
    list_parser.add_argument("--json", action="store_true", help="Print scenarios as JSON.")

    query_parser = subparsers.add_parser("query", help="Query analytics artifacts.")
    query_subparsers = query_parser.add_subparsers(dest="query_command", required=True)
    query_runs_parser = query_subparsers.add_parser(
        "runs",
        help="Run a DuckDB SQL query against Parquet exports as `runs`.",
    )
    query_runs_parser.add_argument("paths", nargs="+", type=Path, help="One or more Parquet paths.")
    query_runs_parser.add_argument("--sql", required=True, help="DuckDB SQL using the `runs` view.")
    query_runs_parser.add_argument("--json", action="store_true", help="Print rows as JSON.")

    verify_parser = subparsers.add_parser("verify", help="Verify a reproducibility certificate.")
    verify_parser.add_argument("certificate", type=Path, help="Path to run_fingerprint.json.")
    verify_parser.add_argument("--run-config", type=Path, default=None, help="Optional JSON config to hash.")
    verify_parser.add_argument("--result-jsonl", type=Path, default=None, help="Optional result JSONL to verify.")
    verify_parser.add_argument("--json", action="store_true", help="Print verification JSON.")

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate trace and study artifacts.")
    evaluate_subparsers = evaluate_parser.add_subparsers(dest="evaluate_command", required=True)
    evaluate_trace_parser = evaluate_subparsers.add_parser(
        "trace",
        help="Grade a Luvoire JSONL trace with a deterministic rubric.",
    )
    evaluate_trace_parser.add_argument("logfile", type=Path, help="Path to a Luvoire JSONL simulation log.")
    evaluate_trace_parser.add_argument("--trace-id", default=None, help="Optional explicit trace identifier.")
    evaluate_trace_parser.add_argument("--json", action="store_true", help="Print evaluation JSON.")

    playground_parser = subparsers.add_parser("playground", help="Start the local Gradio Playground.")
    playground_parser.add_argument("--host", default="127.0.0.1", help="Host interface.")
    playground_parser.add_argument("--port", type=int, default=7860, help="Port to bind.")
    playground_parser.add_argument("--dry-run", action="store_true", help="Print launch plan without starting Gradio.")
    playground_parser.add_argument("--json", action="store_true", help="Print launch plan as JSON.")

    replay_parser = subparsers.add_parser("replay-cache", help="Inspect replay-cache artifacts.")
    replay_subparsers = replay_parser.add_subparsers(dest="replay_cache_command", required=True)
    inspect_parser = replay_subparsers.add_parser("inspect", help="Summarize an NDMP replay cache.")
    inspect_parser.add_argument("path", type=Path, help="Path to a replay-cache NDMP file.")

    personas_parser = subparsers.add_parser("personas", help="Inspect Luvoire Persona Interface sources.")
    personas_subparsers = personas_parser.add_subparsers(dest="personas_command", required=True)
    personas_subparsers.add_parser("list", help="List supported Nemotron-Personas countries.")
    sample_parser = personas_subparsers.add_parser("sample", help="Sample LPI personas as NDJSON.")
    sample_parser.add_argument("--country", required=True, help="Country ISO: USA, JPN, IND, BRA, SGP, FRA, KOR.")
    sample_parser.add_argument("--n", type=int, required=True, help="Number of personas to emit.")
    sample_parser.add_argument("--seed", type=int, default=None, help="Optional deterministic sampling seed.")
    schema_parser = personas_subparsers.add_parser("schema", help="Write the LPI JSON schema.")
    schema_parser.add_argument("--out", type=Path, required=True, help="Output JSON schema path.")

    add_customer_subparser(subparsers)
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
    if args.command == "export":
        if args.export_command == "odd":
            output_path = export_odd_markdown(args.scenario, args.out)
            print(f"Wrote ODD report to {output_path}")
            return 0
        if args.export_command == "parquet":
            output_path = export_run_log_parquet(args.logfile, args.out)
            print(f"Wrote analytics parquet to {output_path}")
            return 0
        parser.error(f"Unknown export command: {args.export_command}")
        return 2
    if args.command == "list-scenarios":
        payload = list_scenarios_payload()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            for scenario in payload["scenarios"]:
                print(f"{scenario['name']} ({scenario['filename']})")
        return 0
    if args.command == "query":
        if args.query_command == "runs":
            rows = query_run_parquet(args.paths, args.sql)
            if args.json:
                print(json.dumps(rows, ensure_ascii=False, sort_keys=True))
            else:
                _print_query_rows(rows)
            return 0
        parser.error(f"Unknown query command: {args.query_command}")
        return 2
    if args.command == "verify":
        report = verify_certificate_path(
            args.certificate,
            run_config_path=args.run_config,
            result_jsonl_path=args.result_jsonl,
        )
        if args.json:
            print(json.dumps(report.to_json_dict(), ensure_ascii=False, sort_keys=True))
        elif report.verified:
            print("Luvoire reproducibility certificate verified.")
        else:
            print("Luvoire reproducibility certificate verification failed:")
            for mismatch in report.mismatches:
                print(f"- {mismatch}")
        return 0 if report.verified else 1
    if args.command == "evaluate":
        if args.evaluate_command == "trace":
            trace_report = grade_trace_report(args.logfile, trace_id=args.trace_id)
            if args.json:
                print(json.dumps(trace_report.to_json_dict(), ensure_ascii=False, sort_keys=True))
            else:
                print(
                    f"Trace {trace_report.trace_id}: score={trace_report.weighted_score:.3f} "
                    f"gate={'pass' if trace_report.passes_default_gate else 'fail'}"
                )
            return 0 if trace_report.passes_default_gate else 1
        parser.error(f"Unknown evaluate command: {args.evaluate_command}")
        return 2
    if args.command == "playground":
        payload = playground_launch_payload(args.host, args.port)
        if args.dry_run:
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            else:
                print(f"Playground would launch at {payload['url']} from {payload['app_file']}")
            return 0
        launch_playground(args.host, args.port)
        return 0
    if args.command == "replay-cache":
        if args.replay_cache_command == "inspect":
            cache_summary = inspect_replay_cache(args.path)
            print(f"records: {cache_summary.record_count}")
            print(f"unique_models: {', '.join(cache_summary.unique_models) or 'none'}")
            print(f"first_capture: {cache_summary.first_capture or 'none'}")
            print(f"last_capture: {cache_summary.last_capture or 'none'}")
            print(f"total_bytes: {cache_summary.total_bytes}")
            return 0
        parser.error(f"Unknown replay-cache command: {args.replay_cache_command}")
        return 2
    if args.command == "personas":
        from luvoire.personas import load_country, write_lpi_schema
        from luvoire.personas.loaders import list_country_metadata

        if args.personas_command == "list":
            for row in list_country_metadata():
                print(
                    "\t".join(
                        [
                            row["iso"],
                            row["population_source"],
                            row["record_count"],
                            row["license"],
                            row["grounding_version"],
                        ]
                    )
                )
            return 0
        if args.personas_command == "sample":
            for persona in load_country(args.country, limit=args.n, seed=args.seed):
                print(json.dumps(persona.to_dict(), ensure_ascii=False, sort_keys=True))
            return 0
        if args.personas_command == "schema":
            output_path = write_lpi_schema(args.out)
            print(f"Wrote LPI schema to {output_path}")
            return 0
        parser.error(f"Unknown personas command: {args.personas_command}")
        return 2
    if args.command == "customer":
        return handle_customer_command(args)
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


def list_scenarios_payload() -> dict[str, Any]:
    return {
        "count": len(PLAYGROUND_SCENARIOS),
        "scenarios": [dict(scenario) for scenario in PLAYGROUND_SCENARIOS],
    }


def _print_query_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("0 rows")
        return
    columns = list(rows[0].keys())
    print("\t".join(columns))
    for row in rows:
        print("\t".join("" if row.get(column) is None else str(row[column]) for column in columns))


def verify_certificate_path(
    certificate_path: str | Path,
    *,
    run_config_path: str | Path | None = None,
    result_jsonl_path: str | Path | None = None,
) -> VerificationReport:
    certificate = json.loads(Path(certificate_path).read_text(encoding="utf-8"))
    run_config = _load_optional_json_or_text(Path(run_config_path) if run_config_path else None)
    result = Path(result_jsonl_path).read_text(encoding="utf-8") if result_jsonl_path else None
    return verify_run_fingerprint(certificate, run_config=run_config, result=result)


def playground_launch_payload(host: str = "127.0.0.1", port: int = 7860) -> dict[str, Any]:
    app_file = _playground_app_file()
    return {
        "app_file": str(app_file),
        "host": host,
        "port": int(port),
        "url": f"http://{host}:{int(port)}",
    }


def launch_playground(host: str = "127.0.0.1", port: int = 7860) -> None:
    app_file = _playground_app_file()
    module = _load_module_from_path(app_file)
    build_app = getattr(module, "build_app", None)
    if not callable(build_app):
        raise RuntimeError(f"Playground app does not expose build_app(): {app_file}")
    app = cast(Any, build_app())
    app.launch(server_name=host, server_port=int(port), share=False)


def _discover_scenario_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(f"scenario path does not exist: {path}")
    files = sorted({*path.rglob("*.yaml"), *path.rglob("*.yml")})
    if not files:
        raise ValueError(f"no scenario YAML files found under: {path}")
    return files


def _load_optional_json_or_text(path: Path | None) -> Any | None:
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _playground_app_file() -> Path:
    candidates = [
        Path.cwd() / "playground" / "app.py",
        Path(__file__).resolve().parents[2] / "playground" / "app.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Could not find playground/app.py; searched {searched}")


def _load_module_from_path(path: Path) -> ModuleType:
    sys.path.insert(0, str(path.parent.parent))
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("luvoire_playground_app", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    "launch_playground",
    "list_scenarios_payload",
    "load_run_config",
    "main",
    "playground_launch_payload",
    "run_config",
    "validate_scenario_path",
    "verify_certificate_path",
]
