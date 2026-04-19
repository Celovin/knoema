"""Reusable simulation helpers for the Knoema Playground."""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from knoema.cli import SimulationRunConfig, load_run_config
from knoema.llm import AnthropicClient, LocalClient, OpenAIClient
from knoema.persona import Persona
from knoema.protocols import LLMClient, Message
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.types import Personality

Provider = Literal["Replay only", "OpenAI", "Anthropic"]

SCENARIO_DIR = Path(__file__).resolve().parent / "scenarios"
DEFAULT_SCENARIOS: dict[str, str] = {
    "Dorm: two agents": "dorm_two_agents.yaml",
    "Village: ten agents": "village_ten.yaml",
    "School corridor": "school_corridor.yaml",
}


@dataclass(frozen=True, slots=True)
class PlaygroundResult:
    scenario_name: str
    mode: Provider
    timeline_markdown: str
    relationship_rows: list[dict[str, object]]
    jsonl: str
    download_path: str
    log_count: int
    agent_count: int
    tick_count: int


def scenario_choices() -> list[str]:
    return list(DEFAULT_SCENARIOS)


def scenario_path(name: str) -> Path:
    try:
        filename = DEFAULT_SCENARIOS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown scenario: {name}") from exc
    return SCENARIO_DIR / filename


def run_playground_scenario(
    *,
    scenario_name: str,
    provider: Provider,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    openness: float,
    conscientiousness: float,
    extraversion: float,
    agreeableness: float,
    neuroticism: float,
    ticks: int,
    language: str = "en",
) -> PlaygroundResult:
    """Run a short scenario and return UI-ready artifacts.

    API keys are only passed into the selected client for this call and are not
    written to disk or stored in module state.
    """

    config = load_run_config(scenario_path(scenario_name))
    agents = [agent.to_domain() for agent in config.agents]
    agents[0] = _customize_primary_agent(
        agents[0],
        name=primary_name,
        age=primary_age,
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism,
    )
    environment = config.environment.to_domain()
    for agent_config in config.agents:
        if agent_config.location_path is not None:
            environment.set_agent_location(agent_config.agent_id, agent_config.location_path)

    simulator = Simulator(
        agents=agents,
        environment=environment,
        tick_duration_minutes=config.runtime.tick_duration_minutes,
        llm=_build_client(
            provider=provider,
            api_key=api_key,
            model=model,
            config=config,
            agent_ids=[agent.agent_id for agent in agents],
            language=language,
        ),
        language=language if language in {"ko", "ja", "zh"} else config.prompt_language,
    )
    for event in config.events:
        simulator.scheduler.schedule(event.to_domain())

    _run_ticks(simulator, ticks=max(1, min(ticks, 24)))
    jsonl = _logs_to_jsonl(simulator.logs)
    download_path = _write_download_file(jsonl)
    return PlaygroundResult(
        scenario_name=scenario_name,
        mode=provider,
        timeline_markdown=_timeline_markdown(simulator.logs, language=language),
        relationship_rows=_relationship_rows(simulator),
        jsonl=jsonl,
        download_path=download_path,
        log_count=len(simulator.logs),
        agent_count=len(agents),
        tick_count=len({entry.tick for entry in simulator.logs}),
    )


def _customize_primary_agent(
    agent: Persona,
    *,
    name: str,
    age: int,
    openness: float,
    conscientiousness: float,
    extraversion: float,
    agreeableness: float,
    neuroticism: float,
) -> Persona:
    resolved_name = name.strip() or agent.name
    return Persona(
        agent_id=agent.agent_id,
        name=resolved_name,
        age=max(1, age),
        background=agent.background,
        personality=Personality(
            openness=openness,
            conscientiousness=conscientiousness,
            extraversion=extraversion,
            agreeableness=agreeableness,
            neuroticism=neuroticism,
        ),
        values=list(agent.values),
        goals=list(agent.goals),
    )


def _build_client(
    *,
    provider: Provider,
    api_key: str,
    model: str,
    config: SimulationRunConfig,
    agent_ids: list[str],
    language: str = "en",
) -> LLMClient:
    if provider == "OpenAI" and api_key.strip():
        return OpenAIClient(model=model.strip() or "gpt-4o-mini", api_key=api_key.strip())
    if provider == "Anthropic" and api_key.strip():
        return AnthropicClient(
            model=model.strip() or "claude-3-5-haiku-latest",
            api_key=api_key.strip(),
        )
    return LocalClient(
        _scripted_responder(agent_ids=agent_ids, fallback=config.local_response, language=language)
    )


def _scripted_responder(*, agent_ids: list[str], fallback: str, language: str = "en"):
    def respond(messages: list[Message]) -> str:
        system_prompt = next(
            (message.get("content", "") for message in messages if message.get("role") == "system"),
            "",
        )
        user_prompt = next(
            (message.get("content", "") for message in reversed(messages) if message.get("role") == "user"),
            "",
        )
        agent_id = _extract_agent_id(system_prompt) or (agent_ids[0] if agent_ids else "agent")
        target = next((candidate for candidate in agent_ids if candidate != agent_id), None)
        location = _extract_line_value(user_prompt, "Location: ") or "shared space"
        content = _scripted_content(
            agent_id=agent_id, location=location, user_prompt=user_prompt, language=language
        )
        if not content:
            return fallback
        return json.dumps(
            {
                "action_type": "speak" if target else "observe",
                "target": target,
                "content": content,
            },
            ensure_ascii=False,
        )

    return respond


def _extract_agent_id(system_prompt: str) -> str | None:
    match = re.search(r"Persona ID:\s*([A-Za-z0-9_-]+)", system_prompt)
    return match.group(1) if match else None


def _extract_line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def _scripted_content(
    *, agent_id: str, location: str, user_prompt: str, language: str = "en"
) -> str:
    has_trigger = "Trigger:" in user_prompt and "No immediate trigger" not in user_prompt
    if language == "ko":
        if has_trigger:
            return f"[{agent_id}] {location}에서 발생한 최근 사건에 반응하며 다른 사람들의 반응을 살핀다."
        return f"[{agent_id}] {location}에 대한 짧은 관찰을 공유하고 자신의 계획을 갱신한다."
    if has_trigger:
        return f"{agent_id} reacts to the latest event at {location} and checks how others feel."
    return f"{agent_id} shares a small observation about {location} and updates their plan."


def _run_ticks(simulator: Simulator, *, ticks: int) -> None:
    for tick in range(ticks):
        simulator._run_tick(tick)
        simulator.environment.advance_time(simulator.tick_duration)


def _logs_to_jsonl(logs: list[SimulationLogEntry]) -> str:
    return "\n".join(
        json.dumps(entry.to_json_dict(), ensure_ascii=False, sort_keys=True) for entry in logs
    )


def _write_download_file(jsonl: str) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".jsonl",
        prefix="knoema_playground_",
        delete=False,
    ) as handle:
        handle.write(jsonl)
        if jsonl:
            handle.write("\n")
        return handle.name


def _timeline_markdown(logs: list[SimulationLogEntry], *, language: str = "en") -> str:
    if not logs:
        return "아직 이벤트가 없습니다." if language == "ko" else "No events yet."
    header = "### 타임라인" if language == "ko" else "### Timeline"
    lines = [header]
    tick_label = "틱" if language == "ko" else "Tick"
    for entry in logs[:80]:
        action = entry.action
        target = f" -> {action.target}" if action.target else ""
        lines.append(
            f"- **{tick_label} {entry.tick:02d}** `{entry.timestamp.isoformat()}` "
            f"**{entry.agent_id}{target}**: {action.content}"
        )
    return "\n".join(lines)


def _relationship_rows(simulator: Simulator) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    graph = simulator.relationships.to_networkx()
    for source, target, data in graph.edges(data=True):
        rows.append(
            {
                "source": source,
                "target": target,
                "relationship_type": data.get("relationship_type", "stranger"),
                "weight": round(float(data.get("weight", 0.0)), 3),
                "trust": round(float(data.get("trust", 0.5)), 3),
                "familiarity": round(float(data.get("familiarity", 0.0)), 3),
            }
        )
    return rows
