"""Natural-language scenario synthesis for Knoema run configs."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from knoema.cli import CliPersonalityConfig, SimulationRunConfig
from knoema.types import PERSONALITY_NEUTRAL_DEFAULTS

MAX_SYNTHETIC_AGENTS = 8
DEFAULT_SYNTHETIC_AGENTS = 3
TRAIT_NAMES = tuple(PERSONALITY_NEUTRAL_DEFAULTS)


class ScenarioSynthesisError(ValueError):
    """Raised when generated scenario JSON cannot be validated."""


class SynthesizedAgent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=1, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1)
    age: int = Field(ge=13, le=99)
    background: str = Field(min_length=1)
    personality: CliPersonalityConfig
    values: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)


class SynthesizedEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1)
    location: str = Field(min_length=1)
    description: str = Field(min_length=1)
    participants: list[str] = Field(min_length=1)


class SynthesizedScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    description: str = Field(min_length=12)
    language: Literal["ko", "en"] = "en"
    location_path: list[str] = Field(min_length=1)
    agents: list[SynthesizedAgent] = Field(min_length=1, max_length=MAX_SYNTHETIC_AGENTS)
    events: list[SynthesizedEvent] = Field(min_length=1)
    tick_duration_minutes: int = Field(default=30, ge=1, le=240)
    suggested_ticks: int = Field(default=4, ge=1, le=24)


def synthesize_scenario(
    description: str,
    language: str = "ko",
    *,
    llm_response: str | None = None,
) -> dict[str, Any]:
    """Synthesize a validated Knoema run config from natural language.

    `llm_response` accepts a JSON structured-output payload with the
    `SynthesizedScenario` shape. When it is omitted, a deterministic local
    heuristic creates a safe draft so the Playground and tests work without API
    keys.
    """

    cleaned = description.strip()
    if len(cleaned) < 8:
        raise ScenarioSynthesisError("Describe the social situation in at least 8 characters.")
    try:
        if llm_response is not None:
            payload = _parse_llm_response(llm_response)
        else:
            payload = _heuristic_payload(cleaned, _language_key(language))
        scenario = SynthesizedScenario.model_validate(payload)
        run_config = _to_run_config(scenario)
        SimulationRunConfig.model_validate(run_config)
        return run_config
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise ScenarioSynthesisError(str(exc)) from exc


def scenario_to_yaml(config: dict[str, Any]) -> str:
    """Serialize a synthesized run config as stable YAML."""

    return yaml.safe_dump(config, sort_keys=False, allow_unicode=True)


def _parse_llm_response(response: str) -> dict[str, Any]:
    payload = json.loads(response)
    if not isinstance(payload, dict):
        raise ScenarioSynthesisError("LLM response must be a JSON object.")
    return payload


def _heuristic_payload(description: str, language: str) -> dict[str, Any]:
    agent_count = _infer_agent_count(description)
    location_path = _infer_location_path(description)
    roles = _infer_roles(description, agent_count)
    agents = [
        _agent_payload(index=index, role=roles[index], description=description)
        for index in range(agent_count)
    ]
    title = _title_from_description(description, language)
    event_location = location_path[-1]
    return {
        "title": title,
        "description": description,
        "language": language,
        "location_path": location_path,
        "agents": agents,
        "events": [
            {
                "event_type": "scenario.trigger",
                "location": event_location,
                "description": _trigger_description(description, language),
                "participants": [agent["agent_id"] for agent in agents],
            }
        ],
        "tick_duration_minutes": 30,
        "suggested_ticks": min(max(4, agent_count), 8),
    }


def _to_run_config(scenario: SynthesizedScenario) -> dict[str, Any]:
    start_time = datetime(2026, 4, 20, 9, 0, 0)
    agents = [
        {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "age": agent.age,
            "background": agent.background,
            "personality": agent.personality.model_dump(),
            "values": list(agent.values),
            "goals": list(agent.goals),
            "location_path": list(scenario.location_path),
        }
        for agent in scenario.agents
    ]
    events = [
        {
            "timestamp": start_time.isoformat(),
            "event_type": event.event_type,
            "participants": list(event.participants),
            "location": event.location,
            "description": event.description,
        }
        for event in scenario.events
    ]
    config: dict[str, Any] = {
        "runtime": {
            "duration_days": 1,
            "tick_duration_minutes": scenario.tick_duration_minutes,
            "output_path": "runs/synthesized_scenario.jsonl",
            "prompt_language": scenario.language,
        },
        "environment": {
            "start_time": start_time.isoformat(),
            "location_path": list(scenario.location_path),
            "conditions": {
                "scenario_title": scenario.title,
                "source": "natural_language_synthesis",
                "suggested_ticks": scenario.suggested_ticks,
            },
        },
        "agents": agents,
        "events": events,
        "local_response": (
            '{"action_type": "speak", "target": null, '
            '"content": "I respond to the synthesized situation with a concrete next step."}'
        ),
    }
    if scenario.language == "ko":
        config["description_ko"] = scenario.description
        config["description_en"] = _english_fallback_description(scenario.description)
    else:
        config["description_en"] = scenario.description
    return config


def _agent_payload(*, index: int, role: str, description: str) -> dict[str, Any]:
    agent_id = f"agent_{index + 1}"
    name = _name_for(index, role)
    return {
        "agent_id": agent_id,
        "name": name,
        "age": 24 + (index * 4) % 33,
        "background": f"{name} is a synthetic {role} in this generated scenario.",
        "personality": _personality_for(description, index),
        "values": _values_for(role),
        "goals": [
            f"understand the {role} role in the situation",
            "respond without escalating conflict",
            "coordinate a concrete next step",
        ],
    }


def _personality_for(description: str, index: int) -> dict[str, float]:
    traits: dict[str, float] = {}
    for trait_name in TRAIT_NAMES:
        base = float(PERSONALITY_NEUTRAL_DEFAULTS[trait_name])
        digest = hashlib.sha256(f"{description}|{index}|{trait_name}".encode()).digest()
        jitter = ((digest[0] / 255.0) - 0.5) * 0.36
        traits[trait_name] = round(min(1.0, max(0.0, base + jitter)), 2)
    return traits


def _infer_agent_count(description: str) -> int:
    numeric_counts = [
        int(match.group(1))
        for match in re.finditer(
            r"(\d+)\s*(?:agents?|people|participants?|customers?|merchants?|students?|명)",
            description,
            flags=re.IGNORECASE,
        )
    ]
    if numeric_counts:
        return max(1, min(sum(numeric_counts), MAX_SYNTHETIC_AGENTS))
    lowered = description.lower()
    if "two" in lowered or "둘" in description:
        return 2
    if "five" in lowered or "다섯" in description:
        return 5
    return DEFAULT_SYNTHETIC_AGENTS


def _infer_location_path(description: str) -> list[str]:
    lowered = description.lower()
    if any(token in lowered for token in ("market", "merchant", "customer")) or "시장" in description:
        return ["Generated World", "Market", "Stall Row"]
    if any(token in lowered for token in ("office", "startup", "meeting")) or "회의" in description:
        return ["Generated World", "Office", "Meeting Room"]
    if any(token in lowered for token in ("class", "student", "school")) or "교실" in description:
        return ["Generated World", "School", "Classroom"]
    if any(token in lowered for token in ("hospital", "triage", "clinic")) or "병원" in description:
        return ["Generated World", "Hospital", "Waiting Area"]
    if any(token in lowered for token in ("dorm", "roommate")) or "기숙사" in description:
        return ["Generated World", "Dorm", "Shared Room"]
    return ["Generated World", "Community", "Common Area"]


def _infer_roles(description: str, count: int) -> list[str]:
    lowered = description.lower()
    if "merchant" in lowered or "customer" in lowered or "시장" in description:
        pool = ["merchant", "merchant", "customer", "customer", "mediator"]
    elif "student" in lowered or "교실" in description:
        pool = ["student", "student", "teacher", "observer", "group lead"]
    elif "office" in lowered or "회의" in description:
        pool = ["manager", "engineer", "designer", "operator", "stakeholder"]
    else:
        pool = ["participant", "participant", "facilitator", "observer", "stakeholder"]
    while len(pool) < count:
        pool.append(f"participant {len(pool) + 1}")
    return pool[:count]


def _name_for(index: int, role: str) -> str:
    stem = role.title().replace(" ", "")
    return f"{stem}{index + 1}"


def _values_for(role: str) -> list[str]:
    if role in {"merchant", "customer"}:
        return ["fair exchange", "reputation", "clear negotiation"]
    if role in {"student", "teacher"}:
        return ["learning", "fair participation", "patience"]
    if role in {"manager", "engineer", "designer"}:
        return ["delivery", "clarity", "team trust"]
    return ["respect", "coordination", "shared context"]


def _title_from_description(description: str, language: str) -> str:
    compact = " ".join(description.split())
    if language == "ko":
        return f"생성 시나리오: {compact[:48]}"
    return f"Generated scenario: {compact[:56]}"


def _trigger_description(description: str, language: str) -> str:
    if language == "ko":
        return f"참여자들이 다음 상황을 마주한다: {description}"
    return f"Participants respond to this situation: {description}"


def _english_fallback_description(description: str) -> str:
    return f"Natural-language generated scenario from this source description: {description}"


def _language_key(language: str) -> Literal["ko", "en"]:
    return "ko" if str(language).lower().startswith("ko") or str(language) == "한국어" else "en"


__all__ = [
    "ScenarioSynthesisError",
    "scenario_to_yaml",
    "synthesize_scenario",
]
