"""Seeded live Ollama demo helpers for recorded multi-agent runs."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import perf_counter
from urllib import error, request

from luvoire.decision import parse_action_response
from luvoire.environment import Environment
from luvoire.llm import LocalLLMError, OllamaClient
from luvoire.persona import Persona
from luvoire.protocols import Message
from luvoire.simulator import SimulationLogEntry, Simulator
from luvoire.types import Action, Personality, WorldEvent

DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_SEED = 20260419
DEFAULT_AGENT_COUNT = 5
DEFAULT_TICKS = 1
DEFAULT_BASE_URL = "http://localhost:11434"


@dataclass(frozen=True, slots=True)
class OllamaLiveDemoResult:
    model: str
    seed: int
    tick_count: int
    action_count: int
    relationship_edges: int
    elapsed_seconds: float
    completed_within_target: bool
    action_mix: dict[str, int]
    jsonl: str


def available_ollama_models(
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 2.0,
) -> list[str]:
    try:
        with request.urlopen(f"{base_url.rstrip('/')}/api/tags", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:  # pragma: no cover - depends on local server state
        raise LocalLLMError(f"could not reach Ollama at {base_url}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LocalLLMError("Ollama /api/tags response was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise LocalLLMError("Ollama /api/tags response must be a JSON object")
    models = payload.get("models")
    if not isinstance(models, list):
        raise LocalLLMError("Ollama /api/tags response did not include a model list")
    names = [str(model.get("name")) for model in models if isinstance(model, dict) and model.get("name")]
    return sorted(names)


def ensure_ollama_model_available(
    model: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 2.0,
) -> None:
    names = available_ollama_models(base_url=base_url, timeout=timeout)
    if model not in names:
        raise LocalLLMError(
            f"Ollama model {model!r} is not available locally. Installed models: {', '.join(names) or 'none'}."
        )


def warm_live_ollama_demo_model(
    *,
    model: str = DEFAULT_OLLAMA_MODEL,
    seed: int = DEFAULT_OLLAMA_SEED,
    base_url: str = DEFAULT_BASE_URL,
    request_timeout: float = 60.0,
) -> float:
    ensure_ollama_model_available(model, base_url=base_url)
    client = OllamaClient(model=model, base_url=base_url, timeout=request_timeout)
    started = perf_counter()
    client.complete(
        [
            _live_system_message(),
            {
                "role": "user",
                "content": (
                    'Warm the model. Reply with {"action_type":"observe","target":null,"content":"ready"}'
                ),
            },
        ],
        temperature=0.0,
        max_tokens=32,
        seed=seed,
    )
    return round(perf_counter() - started, 3)


def run_live_ollama_demo(
    *,
    model: str = DEFAULT_OLLAMA_MODEL,
    seed: int = DEFAULT_OLLAMA_SEED,
    ticks: int = DEFAULT_TICKS,
    base_url: str = DEFAULT_BASE_URL,
    request_timeout: float = 30.0,
    deadline_seconds: float = 30.0,
) -> OllamaLiveDemoResult:
    if ticks < 1:
        raise ValueError("ticks must be positive")
    ensure_ollama_model_available(model, base_url=base_url)
    client = OllamaClient(model=model, base_url=base_url, timeout=request_timeout)

    environment = Environment(
        start_time=datetime(2026, 4, 19, 20, 0),
        location_path=("Luvoire Demo World", "Seoul", "Mapo", "Rooftop Studio"),
        conditions={"weather": "clear", "session": "live-demo"},
    )
    personas = _build_personas(seed)
    for persona in personas:
        environment.set_agent_location(
            persona.agent_id,
            ("Luvoire Demo World", "Seoul", "Mapo", "Rooftop Studio", "Table Read"),
        )
    simulator = Simulator(
        agents=personas,
        environment=environment,
        tick_duration_minutes=45,
    )
    _schedule_demo_event(simulator)

    started = perf_counter()
    agent_ids = [persona.agent_id for persona in personas]
    for tick in range(ticks):
        for index, persona in enumerate(personas):
            action = _generate_live_action(
                client=client,
                persona=persona,
                environment=simulator.environment,
                agent_ids=agent_ids,
                seed=seed + tick * len(personas) + index,
            )
            simulator._record_action(tick, persona, action)
        simulator.environment.advance_time(simulator.tick_duration)
    elapsed = perf_counter() - started

    logs = list(simulator.logs)
    action_mix = Counter(entry.action.action_type for entry in logs)
    return OllamaLiveDemoResult(
        model=model,
        seed=seed,
        tick_count=ticks,
        action_count=len(logs),
        relationship_edges=simulator.relationships.to_networkx().number_of_edges(),
        elapsed_seconds=round(elapsed, 3),
        completed_within_target=elapsed <= deadline_seconds,
        action_mix=dict(sorted(action_mix.items())),
        jsonl=_logs_to_jsonl(logs),
    )


def _build_personas(seed: int) -> list[Persona]:
    cast = [
        ("mina", "Mina", "producer", 28, 0.62),
        ("jiho", "Jiho", "designer", 31, 0.55),
        ("ara", "Ara", "researcher", 26, 0.68),
        ("taeho", "Taeho", "engineer", 33, 0.49),
        ("soyeon", "Soyeon", "community lead", 29, 0.73),
    ]
    personas: list[Persona] = []
    for index, (agent_id, name, role, age, openness) in enumerate(cast):
        offset = (seed + index * 11) % 17
        personas.append(
            Persona(
                agent_id=agent_id,
                name=name,
                age=age,
                background=(
                    f"{name} is the {role} for a live demo rehearsal. "
                    "They need to coordinate clearly and keep the session on schedule."
                ),
                personality=Personality(
                    openness=round(min(0.92, openness + (offset % 3) * 0.03), 2),
                    conscientiousness=round(0.58 + (offset % 4) * 0.06, 2),
                    extraversion=round(0.36 + ((offset + 1) % 5) * 0.09, 2),
                    agreeableness=round(0.52 + ((offset + 2) % 4) * 0.07, 2),
                    neuroticism=round(0.14 + ((offset + 3) % 3) * 0.05, 2),
                ),
                values=["clarity", "follow-through", "respect for others' time"],
                goals=[
                    "finish one clean rehearsal pass",
                    "surface the next blocker early",
                    "leave a structured handoff note",
                ],
            )
        )
    return personas


def _schedule_demo_event(simulator: Simulator) -> None:
    start = simulator.environment.current_time
    simulator.scheduler.schedule(
        WorldEvent(
            timestamp=start + timedelta(minutes=10),
            event_type="demo.table_read",
            participants=[agent.agent_id for agent in simulator.agents],
            location="Luvoire Demo World > Seoul > Mapo > Rooftop Studio > Table Read",
            description="The host asks the five-agent cast to align on one risky moment before recording.",
        )
    )


def _generate_live_action(
    *,
    client: OllamaClient,
    persona: Persona,
    environment: Environment,
    agent_ids: Sequence[str],
    seed: int,
) -> Action:
    messages = [
        _live_system_message(),
        _live_user_message(
            persona=persona,
            environment=environment,
            agent_ids=agent_ids,
            seed=seed,
        ),
    ]
    response = client.complete(
        messages,
        temperature=0.0,
        max_tokens=32,
        seed=seed,
    )
    default_target = next(candidate for candidate in agent_ids if candidate != persona.agent_id)
    action = parse_action_response(
        response,
        agent_id=persona.agent_id,
        timestamp=environment.current_time,
        location="Luvoire Demo World > Seoul > Mapo > Rooftop Studio > Table Read",
    )
    resolved_target = action.target
    if resolved_target not in set(agent_ids) - {persona.agent_id}:
        resolved_target = default_target if action.action_type != "observe" else None
    content = " ".join(action.content.split())
    if len(content) > 64:
        content = content[:61].rstrip() + "..."
    return Action(
        agent_id=action.agent_id,
        timestamp=action.timestamp,
        action_type=action.action_type,
        target=resolved_target,
        content=content,
        location=action.location,
    )


def _live_system_message() -> Message:
    return {
        "role": "system",
        "content": (
            'Output one JSON object only. '
            'Schema: {"action_type":"handoff|review|speak|observe","target":"agent id or null","content":"max four words"}. '
            "No markdown or explanation."
        ),
    }


def _live_user_message(
    *,
    persona: Persona,
    environment: Environment,
    agent_ids: Sequence[str],
    seed: int,
) -> Message:
    others = ", ".join(agent_id for agent_id in agent_ids if agent_id != persona.agent_id)
    return {
        "role": "user",
        "content": (
            f"Agent {persona.agent_id}. Role rehearsal cast. "
            f"Time {environment.current_time.isoformat()}. "
            f"Location Rooftop Studio. "
            f"Other agents: {others}. "
            f"Seed {seed}. "
            "Return one short handoff action."
        ),
    }


def _logs_to_jsonl(logs: Sequence[SimulationLogEntry]) -> str:
    return "\n".join(
        json.dumps(entry.to_json_dict(), ensure_ascii=False, sort_keys=True) for entry in logs
    )


__all__ = [
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_OLLAMA_SEED",
    "OllamaLiveDemoResult",
    "available_ollama_models",
    "run_live_ollama_demo",
    "warm_live_ollama_demo_model",
]
