"""Stdio Model Context Protocol server for Knoema.

The server implements the JSON-RPC MCP lifecycle used by desktop clients:
`initialize`, `tools/list`, and `tools/call`. It intentionally runs local
deterministic replay by default so Claude Desktop or Cursor can inspect Knoema
without sending secrets or live model calls through the tool layer.
"""

from __future__ import annotations

import json
import sys
import uuid
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, TextIO, TypeAlias

from knoema.cli import SimulationRunConfig, load_run_config
from knoema.llm import LocalClient
from knoema.protocols import Message
from knoema.simulator import SimulationLogEntry, Simulator

JsonObject: TypeAlias = dict[str, Any]
JsonRpcId: TypeAlias = str | int | None

PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = frozenset(
    {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}
)

DEFAULT_SCENARIOS: tuple[tuple[str, str], ...] = (
    ("Dorm: two agents", "dorm_two_agents.yaml"),
    ("Village: ten agents", "village_ten.yaml"),
    ("School corridor", "school_corridor.yaml"),
    ("Office team conflict", "office_team_conflict.yaml"),
    ("Family dinner table", "family_dinner_table.yaml"),
    ("Cafe first meeting", "cafe_first_meeting.yaml"),
    ("Subway rush crowd", "subway_rush_crowd.yaml"),
    ("School group project", "school_group_project.yaml"),
    ("Apartment neighbor dispute", "apartment_neighbor_dispute.yaml"),
    ("Volunteer cleanup team", "volunteer_cleanup_team.yaml"),
    ("Startup pivot meeting", "startup_pivot_meeting.yaml"),
    ("Late-night convenience store", "late_night_convenience_store.yaml"),
    ("Book club debate", "book_club_debate.yaml"),
    ("Hospital waiting room", "hospital_waiting_room.yaml"),
    ("Neighborhood festival", "neighborhood_festival.yaml"),
    ("Classroom pop quiz", "classroom_pop_quiz.yaml"),
    ("Religious service", "religious_service.yaml"),
    ("Military barracks morning", "military_barracks_morning.yaml"),
    ("ER triage", "er_triage.yaml"),
    ("Courtroom jury deliberation", "courtroom_jury_deliberation.yaml"),
    ("Election rally", "election_rally.yaml"),
    ("Refugee shelter arrival", "refugee_shelter_arrival.yaml"),
    ("Tech demo day", "tech_demo_day.yaml"),
    ("Wedding after-party", "wedding_after_party.yaml"),
    ("Funeral wake", "funeral_wake.yaml"),
    ("Prison yard (fictional)", "prison_yard_fictional.yaml"),
    ("Zoom team standup", "zoom_team_standup.yaml"),
    ("Kindergarten storytime", "kindergarten_storytime.yaml"),
    ("Senior center chess", "senior_center_chess.yaml"),
    ("Concert lobby intermission", "concert_lobby_intermission.yaml"),
)


@dataclass(frozen=True, slots=True)
class ScenarioRecord:
    name: str
    filename: str

    @property
    def scenario_id(self) -> str:
        return Path(self.filename).stem


@dataclass(frozen=True, slots=True)
class StoredRun:
    run_id: str
    scenario_name: str
    provider: str
    generated_at: str
    config: SimulationRunConfig
    logs: tuple[SimulationLogEntry, ...]


class McpProtocolError(Exception):
    """JSON-RPC protocol-level error."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class KnoemaMcpService:
    """Tool implementation behind the stdio MCP JSON-RPC surface."""

    def __init__(self, *, scenario_dir: Path | None = None) -> None:
        self.scenario_dir = scenario_dir
        self.runs: dict[str, StoredRun] = {}
        self.latest_run_id: str | None = None
        self.scenarios = tuple(ScenarioRecord(name, filename) for name, filename in DEFAULT_SCENARIOS)

    def initialize(self, params: JsonObject | None = None) -> JsonObject:
        requested_version = ""
        if params is not None:
            requested = params.get("protocolVersion")
            if isinstance(requested, str):
                requested_version = requested
        protocol_version = (
            requested_version
            if requested_version in SUPPORTED_PROTOCOL_VERSIONS
            else PROTOCOL_VERSION
        )
        return {
            "protocolVersion": protocol_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {
                "name": "knoema-engine",
                "version": _package_version(),
            },
        }

    def list_tools(self) -> JsonObject:
        return {"tools": list(_tool_descriptors())}

    def call_tool(self, name: str, arguments: JsonObject | None = None) -> JsonObject:
        args = arguments or {}
        try:
            if name == "list_scenarios":
                return _tool_result(self.list_scenarios())
            if name == "run_scenario":
                return _tool_result(
                    self.run_scenario(
                        name=_string_arg(args, "name"),
                        provider=_string_arg(args, "provider", default="replay"),
                        ticks=_int_arg(args, "ticks", default=4),
                    )
                )
            if name == "inspect_trait_vector":
                return _tool_result(
                    self.inspect_trait_vector(
                        agent_id=_string_arg(args, "agent_id"),
                        run_id=_optional_string_arg(args, "run_id"),
                    )
                )
            if name == "generate_report":
                return _tool_result(
                    self.generate_report(run_id=_string_arg(args, "run_id", default="latest"))
                )
            if name == "suggest_scenario":
                return _tool_result(
                    self.suggest_scenario(description=_string_arg(args, "description"))
                )
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": str(exc)}],
                "isError": True,
            }
        raise McpProtocolError(-32602, f"Unknown Knoema tool: {name}")

    def list_scenarios(self) -> JsonObject:
        summaries: list[JsonObject] = []
        for record in self.scenarios:
            summary: JsonObject = {
                "id": record.scenario_id,
                "name": record.name,
                "filename": record.filename,
            }
            try:
                config = self._load_config(record.name)
            except Exception:
                summary["available"] = False
            else:
                summary.update(
                    {
                        "available": True,
                        "agent_count": len(config.agents),
                        "tick_duration_minutes": config.runtime.tick_duration_minutes,
                        "description": config.description_en or config.description_ko or "",
                    }
                )
            summaries.append(summary)
        return {"count": len(summaries), "scenarios": summaries}

    def run_scenario(self, *, name: str, provider: str = "replay", ticks: int = 4) -> JsonObject:
        normalized_provider = _normalize_provider(provider)
        if normalized_provider != "replay":
            raise ValueError(
                "MCP runs default to deterministic replay. Use provider='replay' to avoid "
                "sending API keys through desktop tool calls."
            )
        clamped_ticks = max(1, min(int(ticks), 12))
        config = self._load_config(name)
        simulator = _simulator_from_config(config)
        try:
            logs = tuple(simulator.run_ticks(clamped_ticks))
        finally:
            simulator.close()
        run_id = f"knoema-{uuid.uuid4().hex[:12]}"
        stored = StoredRun(
            run_id=run_id,
            scenario_name=self._record_for(name).name,
            provider=normalized_provider,
            generated_at=datetime.now(UTC).isoformat(),
            config=config,
            logs=logs,
        )
        self.runs[run_id] = stored
        self.latest_run_id = run_id
        return self._run_payload(stored)

    def inspect_trait_vector(self, *, agent_id: str, run_id: str | None = None) -> JsonObject:
        selected_run = self._select_run(run_id)
        if selected_run is not None:
            for agent in selected_run.config.agents:
                if agent.agent_id == agent_id:
                    return {
                        "run_id": selected_run.run_id,
                        "scenario": selected_run.scenario_name,
                        "agent_id": agent.agent_id,
                        "name": agent.name,
                        "traits": agent.personality.model_dump(),
                    }
        for record in self.scenarios:
            try:
                config = self._load_config(record.name)
            except Exception:
                continue
            for agent in config.agents:
                if agent.agent_id == agent_id:
                    return {
                        "run_id": None,
                        "scenario": record.name,
                        "agent_id": agent.agent_id,
                        "name": agent.name,
                        "traits": agent.personality.model_dump(),
                    }
        raise ValueError(f"Unknown agent_id: {agent_id}")

    def generate_report(self, *, run_id: str = "latest") -> JsonObject:
        stored = self._require_run(run_id)
        action_counts = Counter(entry.action.action_type for entry in stored.logs)
        agent_counts = Counter(entry.agent_id for entry in stored.logs)
        lines = [
            f"# Knoema MCP Run Report: {stored.scenario_name}",
            "",
            f"- Run ID: `{stored.run_id}`",
            f"- Provider: `{stored.provider}`",
            f"- Generated at: `{stored.generated_at}`",
            f"- Agents: {len(stored.config.agents)}",
            f"- Actions: {len(stored.logs)}",
            "",
            "## Action Counts",
            *[f"- {action_type}: {count}" for action_type, count in action_counts.most_common()],
            "",
            "## Agent Activity",
            *[f"- {agent_id}: {count} actions" for agent_id, count in agent_counts.most_common()],
            "",
            "## First Actions",
            *[
                f"- tick {entry.tick}, {entry.agent_id}: {entry.action.action_type} -> {entry.action.content}"
                for entry in stored.logs[:5]
            ],
        ]
        return {
            "run_id": stored.run_id,
            "scenario": stored.scenario_name,
            "markdown": "\n".join(lines).strip() + "\n",
        }

    def suggest_scenario(self, *, description: str) -> JsonObject:
        query_tokens = _tokens(description)
        scored: list[tuple[int, ScenarioRecord, str]] = []
        for record in self.scenarios:
            haystack_parts = [record.name, record.scenario_id.replace("_", " ")]
            try:
                config = self._load_config(record.name)
            except Exception:
                config = None
            if config is not None:
                haystack_parts.extend(
                    [
                        config.description_en or "",
                        config.description_ko or "",
                        " ".join(agent.background for agent in config.agents),
                    ]
                )
            haystack = " ".join(haystack_parts).lower()
            score = sum(1 for token in query_tokens if token in haystack)
            if score == 0 and record.name.lower().split()[0] in description.lower():
                score = 1
            reason = "matched keywords" if score else "fallback curated scenario"
            scored.append((score, record, reason))
        scored.sort(key=lambda item: (-item[0], item[1].name))
        suggestions = [
            {
                "id": record.scenario_id,
                "name": record.name,
                "score": score,
                "reason": reason,
            }
            for score, record, reason in scored[:3]
        ]
        return {"description": description, "suggestions": suggestions}

    def _run_payload(self, stored: StoredRun) -> JsonObject:
        action_counts = Counter(entry.action.action_type for entry in stored.logs)
        return {
            "run_id": stored.run_id,
            "scenario": stored.scenario_name,
            "provider": stored.provider,
            "ticks": len({entry.tick for entry in stored.logs}),
            "agent_count": len(stored.config.agents),
            "log_count": len(stored.logs),
            "action_type_counts": dict(sorted(action_counts.items())),
            "logs": [entry.to_json_dict() for entry in stored.logs],
        }

    def _record_for(self, name: str) -> ScenarioRecord:
        normalized = _normalize_name(name)
        for record in self.scenarios:
            if normalized in {_normalize_name(record.name), _normalize_name(record.scenario_id)}:
                return record
        raise ValueError(f"Unknown scenario: {name}")

    def _load_config(self, name: str) -> SimulationRunConfig:
        record = self._record_for(name)
        path = self._scenario_path(record)
        return load_run_config(path)

    def _scenario_path(self, record: ScenarioRecord) -> Path:
        for directory in self._scenario_dirs():
            candidate = directory / record.filename
            if candidate.exists():
                return candidate
        searched = ", ".join(str(path) for path in self._scenario_dirs())
        raise FileNotFoundError(f"Scenario file {record.filename} not found; searched {searched}")

    def _scenario_dirs(self) -> tuple[Path, ...]:
        candidates: list[Path] = []
        if self.scenario_dir is not None:
            candidates.append(self.scenario_dir)
        env_value = _env_scenario_dir()
        if env_value is not None:
            candidates.append(env_value)
        module_path = Path(__file__).resolve()
        candidates.extend(
            [
                Path.cwd() / "playground" / "scenarios",
                module_path.parents[2] / "playground" / "scenarios",
            ]
        )
        deduped: list[Path] = []
        for candidate in candidates:
            if candidate not in deduped:
                deduped.append(candidate)
        return tuple(deduped)

    def _select_run(self, run_id: str | None) -> StoredRun | None:
        if run_id is None:
            if self.latest_run_id is None:
                return None
            return self.runs.get(self.latest_run_id)
        return self.runs.get(run_id)

    def _require_run(self, run_id: str) -> StoredRun:
        selected_id = self.latest_run_id if run_id == "latest" else run_id
        if selected_id is None or selected_id not in self.runs:
            raise ValueError("No MCP run is available. Call run_scenario first.")
        return self.runs[selected_id]


def serve_stdio(
    *,
    service: KnoemaMcpService | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    resolved_service = service or KnoemaMcpService()
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    for line in input_stream:
        stripped = line.strip()
        if not stripped:
            continue
        response = handle_jsonrpc_line(resolved_service, stripped)
        if response is None:
            continue
        output_stream.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
        output_stream.flush()
    return 0


def handle_jsonrpc_line(service: KnoemaMcpService, line: str) -> JsonObject | None:
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            raise McpProtocolError(-32600, "Invalid JSON-RPC request")
        response = _dispatch_request(service, request)
    except json.JSONDecodeError as exc:
        return _error_response(None, -32700, f"Parse error: {exc.msg}")
    except McpProtocolError as exc:
        request_id = _request_id_from_raw(locals().get("request"))
        return _error_response(request_id, exc.code, exc.message)
    return response


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args != ["--stdio"]:
        print("usage: knoema-mcp [--stdio]", file=sys.stderr)
        return 2
    return serve_stdio()


def _dispatch_request(service: KnoemaMcpService, request: JsonObject) -> JsonObject | None:
    if request.get("jsonrpc") != "2.0":
        raise McpProtocolError(-32600, "JSON-RPC version must be 2.0")
    request_id = _request_id(request)
    method = request.get("method")
    if not isinstance(method, str):
        raise McpProtocolError(-32600, "JSON-RPC method must be a string")
    params = request.get("params")
    if params is not None and not isinstance(params, dict):
        raise McpProtocolError(-32602, "JSON-RPC params must be an object")
    if request_id is None and "id" not in request:
        return None
    if method == "initialize":
        return _success_response(request_id, service.initialize(params))
    if method == "ping":
        return _success_response(request_id, {})
    if method == "tools/list":
        return _success_response(request_id, service.list_tools())
    if method == "tools/call":
        if params is None:
            raise McpProtocolError(-32602, "tools/call requires params")
        tool_name = params.get("name")
        if not isinstance(tool_name, str):
            raise McpProtocolError(-32602, "tools/call params.name must be a string")
        arguments = params.get("arguments")
        if arguments is not None and not isinstance(arguments, dict):
            raise McpProtocolError(-32602, "tools/call params.arguments must be an object")
        return _success_response(request_id, service.call_tool(tool_name, arguments))
    raise McpProtocolError(-32601, f"Method not found: {method}")


def _tool_descriptors() -> Iterable[JsonObject]:
    return (
        {
            "name": "list_scenarios",
            "description": "List the 30 built-in Knoema Playground scenarios.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "run_scenario",
            "description": "Run a deterministic replay scenario and return JSON logs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Scenario name or id."},
                    "provider": {
                        "type": "string",
                        "description": "Use 'replay' for deterministic local MCP runs.",
                        "default": "replay",
                    },
                    "ticks": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 12,
                        "default": 4,
                    },
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "inspect_trait_vector",
            "description": "Return a 30-trait vector for an agent from a run or built-in scenario.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string"},
                    "run_id": {"type": "string", "description": "Optional run id; defaults to latest."},
                },
                "required": ["agent_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "generate_report",
            "description": "Generate a Markdown report for a prior MCP run.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string", "default": "latest"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "suggest_scenario",
            "description": "Suggest built-in Knoema scenarios from a natural-language description.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                },
                "required": ["description"],
                "additionalProperties": False,
            },
        },
    )


def _tool_result(payload: JsonObject) -> JsonObject:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            }
        ],
        "structuredContent": payload,
    }


def _success_response(request_id: JsonRpcId, result: JsonObject) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error_response(request_id: JsonRpcId, code: int, message: str) -> JsonObject:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _request_id(request: JsonObject) -> JsonRpcId:
    raw_id = request.get("id")
    if raw_id is None or isinstance(raw_id, str | int):
        return raw_id
    raise McpProtocolError(-32600, "JSON-RPC id must be a string, integer, or null")


def _request_id_from_raw(raw_request: object) -> JsonRpcId:
    if not isinstance(raw_request, dict):
        return None
    raw_id = raw_request.get("id")
    if raw_id is None or isinstance(raw_id, str | int):
        return raw_id
    return None


def _string_arg(args: JsonObject, key: str, *, default: str | None = None) -> str:
    value = args.get(key, default)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"Tool argument '{key}' must be a non-empty string")


def _optional_string_arg(args: JsonObject, key: str) -> str | None:
    value = args.get(key)
    if value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"Tool argument '{key}' must be a non-empty string when provided")


def _int_arg(args: JsonObject, key: str, *, default: int) -> int:
    value = args.get(key, default)
    if isinstance(value, int):
        return value
    raise ValueError(f"Tool argument '{key}' must be an integer")


def _normalize_name(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_").replace(":", "")


def _normalize_provider(value: str) -> str:
    normalized = value.strip().lower().replace("_", " ")
    if normalized in {"replay", "replay only", "local"}:
        return "replay"
    if normalized in {"openai", "gpt"}:
        return "openai"
    if normalized in {"anthropic", "claude"}:
        return "anthropic"
    raise ValueError("provider must be one of: replay, openai, anthropic")


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in (
            raw.strip(".,:;!?()[]{}\"'").lower()
            for raw in text.replace("-", " ").replace("_", " ").split()
        )
        if len(token) >= 3
    )


def _env_scenario_dir() -> Path | None:
    # `os.environ` is avoided at import time to keep tests free to monkeypatch.
    import os

    value = os.environ.get("KNOEMA_SCENARIO_DIR")
    if not value:
        return None
    return Path(value)


def _package_version() -> str:
    try:
        return importlib_metadata.version("knoema-engine")
    except importlib_metadata.PackageNotFoundError:
        return "0.2.0"


def _simulator_from_config(config: SimulationRunConfig) -> Simulator:
    environment = config.environment.to_domain()
    agents = [agent.to_domain() for agent in config.agents]
    for agent in config.agents:
        if agent.location_path is not None:
            environment.set_agent_location(agent.agent_id, agent.location_path)

    def local_response(_messages: Sequence[Message]) -> str:
        return config.local_response

    simulator = Simulator(
        agents=agents,
        environment=environment,
        tick_duration_minutes=config.runtime.tick_duration_minutes,
        llm=LocalClient(local_response),
        language=config.prompt_language,
    )
    for event in config.events:
        simulator.scheduler.schedule(event.to_domain())
    return simulator


__all__ = [
    "KnoemaMcpService",
    "handle_jsonrpc_line",
    "main",
    "serve_stdio",
]
