"""Reusable simulation helpers for the Knoema Playground."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml

from knoema.cli import (
    CliAgentConfig,
    CliEventConfig,
    CliPersonalityConfig,
    SimulationRunConfig,
    load_run_config,
)
from knoema.llm import AnthropicClient, LocalClient, OpenAIClient
from knoema.persona import Persona
from knoema.protocols import LLMClient, Message
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.types import PERSONALITY_NEUTRAL_DEFAULTS, Personality

Provider = Literal["Replay only", "OpenAI", "Anthropic"]
AGENT_COUNT_MIN = 1
AGENT_COUNT_MAX = 30
AGENT_RESIZE_JITTER = 0.05
PERSONALITY_FIELDS = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)
JITTER_STEPS = (-0.05, -0.025, 0.0, 0.025, 0.05)

SCENARIO_DIR = Path(__file__).resolve().parent / "scenarios"
ENVIRONMENTS_PATH = Path(__file__).resolve().parent / "environments.yaml"
PERSONA_PRESETS_PATH = Path(__file__).resolve().parent / "persona_presets.yaml"
CULTURAL_PRIORS_PATH = Path(__file__).resolve().parent / "cultural_priors.yaml"
DEFAULT_SCENARIOS: tuple[dict[str, str], ...] = (
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
PERSONA_TRAIT_FIELDS = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
    "honesty_humility",
    "machiavellianism",
    "narcissism",
    "psychopathy",
    "sadism",
    "kantianism",
    "humanism",
    "faith_in_humanity",
    "risk_tolerance",
    "locus_of_control",
    "need_for_cognition",
    "trait_empathy",
    "care_harm",
    "fairness",
    "binding_morals",
    "self_direction",
    "stimulation",
    "hedonism",
    "achievement",
    "power",
    "security",
    "conformity",
    "tradition",
    "benevolence",
    "universalism",
)
PERSONA_TRAIT_DEFAULTS = {
    field_name: float(PERSONALITY_NEUTRAL_DEFAULTS[field_name]) for field_name in PERSONA_TRAIT_FIELDS
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
    return [scenario["name"] for scenario in DEFAULT_SCENARIOS]


def scenario_path(name: str) -> Path:
    for scenario in DEFAULT_SCENARIOS:
        if scenario["name"] == name:
            return SCENARIO_DIR / scenario["filename"]
    raise ValueError(f"Unknown scenario: {name}")


def scenario_default_agent_count(name: str) -> int:
    return len(load_run_config(scenario_path(name)).agents)


def scenario_description(name: str, language: str = "en") -> str:
    config = load_run_config(scenario_path(name))
    if language == "ko" and config.description_ko:
        return config.description_ko.strip()
    if language != "ko" and config.description_en:
        return config.description_en.strip()
    return _default_scenario_description(language)


def build_playground_hint(
    *,
    scenario_name: str | None,
    language: str = "en",
    environment_note: str | None = None,
) -> str:
    parts: list[str] = []
    if scenario_name:
        scenario_label = "시나리오" if language == "ko" else "Scenario"
        parts.append(f"**{scenario_label}:** {scenario_description(scenario_name, language)}")
    else:
        parts.append(_default_scenario_description(language))
    if environment_note:
        environment_label = "환경" if language == "ko" else "Environment"
        parts.append(f"**{environment_label}:** {environment_note.strip()}")
    return "\n\n".join(parts)


def _default_scenario_description(language: str) -> str:
    if language == "ko":
        return "기본 데모 시나리오를 선택해 짧은 에이전트 상호작용 흐름을 확인해 보세요."
    return "Select a demo scenario to preview a short persistent-agent interaction flow."


@lru_cache(maxsize=1)
def load_environment_presets() -> tuple[dict[str, Any], ...]:
    with ENVIRONMENTS_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    presets = data.get("presets", [])
    return tuple(dict(preset) for preset in presets)


def environment_choices(language: str = "en") -> list[tuple[str, str]]:
    label_key = "label_ko" if language == "ko" else "label_en"
    return [
        (str(preset[label_key]), str(preset["id"]))
        for preset in load_environment_presets()
    ]


def environment_note(preset_id: str | None, language: str = "en") -> str | None:
    preset = environment_preset(preset_id)
    if preset is None:
        return None
    key = "notes_ko" if language == "ko" else "notes_en"
    note = preset.get(key)
    return str(note).strip() if note else None


def environment_preset(preset_id: str | None) -> dict[str, Any] | None:
    if not preset_id:
        return None
    for preset in load_environment_presets():
        if preset.get("id") == preset_id:
            return dict(preset)
    return None


@lru_cache(maxsize=1)
def load_persona_presets() -> tuple[dict[str, Any], ...]:
    with PERSONA_PRESETS_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    presets = data.get("presets", [])
    normalized: list[dict[str, Any]] = []
    for preset in presets:
        personality = dict(preset.get("personality", {}))
        missing = sorted(set(PERSONA_TRAIT_FIELDS).difference(personality))
        if missing:
            preset_id = preset.get("id", "<unknown>")
            raise ValueError(
                f"persona preset {preset_id!r} is missing trait fields: {', '.join(missing)}"
            )
        normalized.append({**dict(preset), "personality": personality})
    return tuple(normalized)


def persona_choices(language: str = "en", *, include_blank: bool = True) -> list[tuple[str, str]]:
    choices: list[tuple[str, str]] = []
    if include_blank:
        blank_label = "수동 조정" if language == "ko" else "Manual tuning"
        choices.append((blank_label, ""))
    label_key = "label_ko" if language == "ko" else "label_en"
    choices.extend(
        (str(preset[label_key]), str(preset["id"])) for preset in load_persona_presets()
    )
    return choices


def persona_preset(preset_id: str | None) -> dict[str, Any] | None:
    if not preset_id:
        return None
    for preset in load_persona_presets():
        if preset.get("id") == preset_id:
            return dict(preset)
    return None


def persona_trait_values(
    preset_id: str | None,
    fields: tuple[str, ...] = PERSONALITY_FIELDS,
) -> tuple[float, ...] | None:
    preset = persona_preset(preset_id)
    if preset is None:
        return None
    personality = dict(preset["personality"])
    return tuple(float(personality[field]) for field in fields)


@lru_cache(maxsize=1)
def load_cultural_priors() -> tuple[dict[str, Any], ...]:
    with CULTURAL_PRIORS_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    priors = data.get("priors", [])
    normalized: list[dict[str, Any]] = []
    for prior in priors:
        shifts = {field_name: float(value) for field_name, value in dict(prior.get("shifts", {})).items()}
        unknown = sorted(set(shifts).difference(PERSONA_TRAIT_FIELDS))
        if unknown:
            prior_id = prior.get("id", "<unknown>")
            raise ValueError(
                f"cultural prior {prior_id!r} contains unknown trait shifts: {', '.join(unknown)}"
            )
        normalized.append({**dict(prior), "shifts": shifts})
    return tuple(normalized)


def cultural_prior(prior_id: str | None) -> dict[str, Any] | None:
    if not prior_id:
        return None
    for prior in load_cultural_priors():
        if prior.get("id") == prior_id:
            return dict(prior)
    return None


def cultural_prior_choices(language: str = "en", *, include_blank: bool = True) -> list[tuple[str, str]]:
    choices: list[tuple[str, str]] = []
    if include_blank:
        blank_label = "(없음)" if language == "ko" else "(none)"
        choices.append((blank_label, ""))
    label_key = "label_ko" if language == "ko" else "label_en"
    choices.extend((str(prior[label_key]), str(prior["id"])) for prior in load_cultural_priors())
    return choices


def cultural_prior_trait_values(
    prior_id: str | None,
    fields: tuple[str, ...] = PERSONA_TRAIT_FIELDS,
) -> tuple[float, ...]:
    resolved = dict(PERSONA_TRAIT_DEFAULTS)
    prior = cultural_prior(prior_id)
    if prior is not None:
        for field_name, shift in dict(prior["shifts"]).items():
            resolved[field_name] = _clamp_unit(PERSONALITY_NEUTRAL_DEFAULTS[field_name] + float(shift))
    return tuple(float(resolved[field_name]) for field_name in fields)


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
    personality_overrides: dict[str, float] | None = None,
    ticks: int,
    agent_count: int | None = None,
    environment_preset_id: str | None = None,
    cultural_prior_id: str | None = None,
    language: str = "en",
) -> PlaygroundResult:
    """Run a short scenario and return UI-ready artifacts.

    API keys are only passed into the selected client for this call and are not
    written to disk or stored in module state.
    """

    config = load_run_config(scenario_path(scenario_name))
    target_agent_count = len(config.agents) if agent_count is None else int(agent_count)
    agent_configs = _resize_agent_pool(config.agents, target_agent_count)
    agents = [agent.to_domain() for agent in agent_configs]
    if cultural_prior_id:
        agents = [
            _apply_cultural_prior_to_agent(agent, cultural_prior_id, language=language)
            for agent in agents
        ]
    resolved_personality = {
        "openness": openness,
        "conscientiousness": conscientiousness,
        "extraversion": extraversion,
        "agreeableness": agreeableness,
        "neuroticism": neuroticism,
        **(personality_overrides or {}),
    }
    agents[0] = _customize_agent(
        agents[0],
        name=primary_name,
        age=primary_age,
        personality_overrides=resolved_personality,
    )
    environment = config.environment.to_domain()
    preset = environment_preset(environment_preset_id)
    if preset is None:
        for agent_config in agent_configs:
            if agent_config.location_path is not None:
                environment.set_agent_location(agent_config.agent_id, agent_config.location_path)
    else:
        _apply_environment_preset(environment, preset)

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
    for event in _filter_events_for_agent_pool(config.events, agent_configs):
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


def _resize_agent_pool(
    agent_configs: list[CliAgentConfig], target_count: int
) -> list[CliAgentConfig]:
    clamped_target = max(AGENT_COUNT_MIN, min(int(target_count), AGENT_COUNT_MAX))
    resized = [agent.model_copy(deep=True) for agent in agent_configs[:clamped_target]]
    if clamped_target <= len(agent_configs):
        return resized

    base_agent = agent_configs[-1]
    while len(resized) < clamped_target:
        duplicate_index = len(resized) + 1
        resized.append(
            base_agent.model_copy(
                deep=True,
                update={
                    "agent_id": f"{base_agent.agent_id}-{duplicate_index}",
                    "name": f"{base_agent.name}-{duplicate_index}",
                    "personality": _jitter_personality(base_agent, duplicate_index),
                    "location_path": None,
                },
            )
        )
    return resized


def _filter_events_for_agent_pool(
    events: list[CliEventConfig], agent_configs: list[CliAgentConfig]
) -> list[CliEventConfig]:
    allowed_agent_ids = {agent.agent_id for agent in agent_configs}
    filtered_events: list[CliEventConfig] = []
    for event in events:
        participants = [
            participant for participant in event.participants if participant in allowed_agent_ids
        ]
        if event.participants and not participants:
            continue
        filtered_events.append(
            event.model_copy(deep=True, update={"participants": participants})
        )
    return filtered_events


def _jitter_personality(
    agent_config: CliAgentConfig, duplicate_index: int
) -> CliPersonalityConfig:
    base_values = agent_config.personality.model_dump()
    jittered_values: dict[str, float] = {}
    for offset, trait_name in enumerate(PERSONALITY_FIELDS):
        jitter = JITTER_STEPS[(duplicate_index + offset) % len(JITTER_STEPS)]
        jittered_values[trait_name] = round(
            _clamp_unit(float(base_values[trait_name]) + jitter),
            3,
        )
    return agent_config.personality.model_copy(update=jittered_values)


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def _apply_environment_preset(environment: object, preset: dict[str, Any]) -> None:
    environment.location_path = tuple(str(part) for part in preset["location_path"])
    environment.current_time = datetime.fromisoformat(str(preset["start_time"]))
    environment.conditions = dict(getattr(environment, "conditions", {}))
    environment.conditions["preset_id"] = str(preset["id"])
    environment.conditions["crowding"] = str(preset["crowding"])
    environment.conditions["preset_conditions"] = list(preset.get("conditions", []))


def _rebuild_persona(
    agent: Persona,
    *,
    name: str | None = None,
    age: int | None = None,
    background: str | None = None,
    personality_values: dict[str, float] | None = None,
) -> Persona:
    return Persona(
        agent_id=agent.agent_id,
        name=(name.strip() if name is not None else agent.name.strip()) or agent.name,
        age=max(1, age if age is not None else agent.age),
        background=background if background is not None else agent.background,
        personality=Personality.from_dict(personality_values or agent.personality.to_dict()),
        values=list(agent.values),
        goals=list(agent.goals),
        theory_of_mind=agent.theory_of_mind,
        planning=agent.planning,
        social_learning=agent.social_learning,
    )


def _apply_cultural_prior_to_agent(
    agent: Persona,
    prior_id: str,
    *,
    language: str = "en",
) -> Persona:
    prior = cultural_prior(prior_id)
    if prior is None:
        return agent
    personality_values = agent.personality.to_dict()
    for field_name, value in zip(
        PERSONA_TRAIT_FIELDS,
        cultural_prior_trait_values(prior_id, PERSONA_TRAIT_FIELDS),
        strict=True,
    ):
        if field_name in prior["shifts"]:
            personality_values[field_name] = value
    tone_key = "tone_ko" if language == "ko" else "tone_en"
    tone = str(prior.get(tone_key, "")).strip()
    background = agent.background
    if tone:
        background = f"{background} {tone}".strip()
    return _rebuild_persona(
        agent,
        background=background,
        personality_values=personality_values,
    )


def _customize_agent(
    agent: Persona,
    *,
    name: str,
    age: int,
    personality_overrides: dict[str, float] | None = None,
) -> Persona:
    personality_values = agent.personality.to_dict()
    for field_name, value in (personality_overrides or {}).items():
        if field_name in PERSONA_TRAIT_FIELDS:
            personality_values[field_name] = float(value)
    return _rebuild_persona(
        agent,
        name=name,
        age=age,
        personality_values=personality_values,
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
    return _customize_agent(
        agent,
        name=name,
        age=age,
        personality_overrides={
            "openness": openness,
            "conscientiousness": conscientiousness,
            "extraversion": extraversion,
            "agreeableness": agreeableness,
            "neuroticism": neuroticism,
        },
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
    user_key = api_key.strip()
    host_openai_key = os.environ.get("DEMO_OPENAI_API_KEY", "").strip()
    host_anthropic_key = os.environ.get("DEMO_ANTHROPIC_API_KEY", "").strip()

    if provider == "OpenAI":
        key = user_key or host_openai_key
        if key:
            return OpenAIClient(model=model.strip() or "gpt-4o-mini", api_key=key)
    if provider == "Anthropic":
        key = user_key or host_anthropic_key
        if key:
            return AnthropicClient(
                model=model.strip() or "claude-3-5-haiku-latest",
                api_key=key,
            )
    return LocalClient(
        _scripted_responder(agent_ids=agent_ids, fallback=config.local_response, language=language)
    )


def host_key_active(provider: Provider, api_key: str) -> str | None:
    """Return the source label if a host-side demo key would be used."""

    if api_key.strip():
        return None
    if provider == "OpenAI" and os.environ.get("DEMO_OPENAI_API_KEY", "").strip():
        return "OpenAI"
    if provider == "Anthropic" and os.environ.get("DEMO_ANTHROPIC_API_KEY", "").strip():
        return "Anthropic"
    return None


def _scripted_responder(*, agent_ids: list[str], fallback: str, language: str = "en"):
    def respond(messages: list[Message]) -> str:
        system_prompt = next(
            (message.get("content", "") for message in messages if message.get("role") == "system"),
            "",
        )
        user_prompt = next(
            (
                message.get("content", "")
                for message in reversed(messages)
                if message.get("role") == "user"
            ),
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
