"""Reusable simulation helpers for the Knoema Playground."""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from html import escape
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
from knoema.cognition import Monologue
from knoema.game.inventory import Inventory
from knoema.llm import AnthropicClient, LocalClient, OpenAIClient
from knoema.persona import Persona
from knoema.planning import HierarchicalPlanner, Task
from knoema.protocols import LLMClient, Message
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.types import (
    ACTION_TYPES,
    GAME_ACTION_TYPES,
    PERSONALITY_NEUTRAL_DEFAULTS,
    SOCIAL_ACTION_TYPES,
    Personality,
)

Provider = Literal["Replay only", "OpenAI", "Anthropic"]
AGENT_COUNT_MIN = 1
AGENT_COUNT_MAX = 30
AGENT_RESIZE_JITTER = 0.05
AGENT_EDITOR_SLOT_COUNT = 3
TRAIT_CORRELATION_RUN_COUNT = 100
TRAIT_REDUNDANCY_THRESHOLD = 0.7
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
ACTION_TEMPLATES_PATH = Path(__file__).resolve().parent / "action_templates.yaml"
UNTARGETED_ACTION_TYPES = frozenset(
    {
        "observe",
        "move",
        "query_memory",
        "propose_plan",
        "exit",
        "enter",
        "gossip",
        "alone",
        "flee",
        "use_skill",
        "use_item",
        "pickup_item",
        "drop_item",
        "quest_accept",
        "quest_complete",
        "faction_join",
        "faction_betray",
        "craft_item",
        "level_up",
    }
)
PROMPT_LINE_PREFIXES: dict[str, dict[str, str]] = {
    "en": {"location": "Location: ", "trigger": "Trigger: "},
    "ko": {"location": "위치: ", "trigger": "트리거: "},
    "ja": {"location": "場所: ", "trigger": "トリガー: "},
    "zh": {"location": "位置: ", "trigger": "触发事件: "},
}
NO_TRIGGER_LINES = {
    "en": "No immediate trigger.",
    "ko": "즉시 반응할 트리거가 없습니다.",
    "ja": "直近のトリガーはありません。",
    "zh": "没有需要立即回应的触发事件。",
}
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
    monologue_markdown: str
    plan_markdown: str
    relationship_rows: list[dict[str, object]]
    jsonl: str
    download_path: str
    log_count: int
    agent_count: int
    tick_count: int
    batch_result: BatchResult | None = None


@dataclass(frozen=True, slots=True)
class BatchTickStat:
    tick: int
    mean_actions: float
    action_type_counts: dict[str, int]
    top_action_type: str


@dataclass(frozen=True, slots=True)
class BatchAgentStat:
    agent_id: str
    mean_actions: float
    action_type_counts: dict[str, int]
    top_action_type: str


@dataclass(frozen=True, slots=True)
class BatchResult:
    batch_size: int
    master_seed: int
    seeds: tuple[int, ...]
    reproducibility_coefficient: float
    per_tick_stats: tuple[BatchTickStat, ...]
    per_agent_stats: tuple[BatchAgentStat, ...]


@dataclass(frozen=True, slots=True)
class PlaygroundRunArtifacts:
    agents: list[Persona]
    simulator: Simulator


@dataclass(frozen=True, slots=True)
class TraitMergeCandidate:
    keep_trait: str
    drop_trait: str
    correlation: float
    keep_stddev: float
    drop_stddev: float


@dataclass(frozen=True, slots=True)
class TraitCorrelationStudy:
    sample_count: int
    trait_names: tuple[str, ...]
    correlation_matrix: tuple[tuple[float, ...], ...]
    max_pair: tuple[str, str, float]
    merge_candidates: tuple[TraitMergeCandidate, ...]


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


@lru_cache(maxsize=8)
def compute_trait_correlation_study(
    run_count: int = TRAIT_CORRELATION_RUN_COUNT,
    threshold: float = TRAIT_REDUNDANCY_THRESHOLD,
) -> TraitCorrelationStudy:
    sample_count = max(1, int(run_count))
    samples = _trait_sample_vectors(sample_count)
    columns = {
        field_name: [sample[field_name] for sample in samples]
        for field_name in PERSONA_TRAIT_FIELDS
    }
    stddevs = {
        field_name: _population_stddev(values)
        for field_name, values in columns.items()
    }

    matrix_rows: list[tuple[float, ...]] = []
    max_pair = ("", "", 0.0)
    merge_candidates: list[TraitMergeCandidate] = []
    for row_index, row_trait in enumerate(PERSONA_TRAIT_FIELDS):
        row_values: list[float] = []
        for column_index, column_trait in enumerate(PERSONA_TRAIT_FIELDS):
            if row_index == column_index:
                correlation = 1.0
            else:
                correlation = round(
                    _pearson_correlation(columns[row_trait], columns[column_trait]),
                    4,
                )
                if column_index > row_index and abs(correlation) > abs(max_pair[2]):
                    max_pair = (row_trait, column_trait, correlation)
                if column_index > row_index and abs(correlation) > float(threshold):
                    keep_trait, drop_trait = _merge_direction(
                        row_trait,
                        column_trait,
                        stddevs,
                    )
                    merge_candidates.append(
                        TraitMergeCandidate(
                            keep_trait=keep_trait,
                            drop_trait=drop_trait,
                            correlation=correlation,
                            keep_stddev=round(stddevs[keep_trait], 4),
                            drop_stddev=round(stddevs[drop_trait], 4),
                        )
                    )
            row_values.append(correlation)
        matrix_rows.append(tuple(row_values))

    merge_candidates.sort(key=lambda candidate: abs(candidate.correlation), reverse=True)
    return TraitCorrelationStudy(
        sample_count=sample_count,
        trait_names=PERSONA_TRAIT_FIELDS,
        correlation_matrix=tuple(matrix_rows),
        max_pair=max_pair,
        merge_candidates=tuple(merge_candidates),
    )


def trait_correlation_summary(
    *,
    run_count: int = TRAIT_CORRELATION_RUN_COUNT,
    threshold: float = TRAIT_REDUNDANCY_THRESHOLD,
    language: str = "en",
) -> str:
    study = compute_trait_correlation_study(run_count=run_count, threshold=threshold)
    title = "### 특성 상관 진단" if language == "ko" else "### Trait correlation study"
    max_label = "최대 |r| 쌍" if language == "ko" else "Max |r| pair"
    sample_label = "배치 실행 수" if language == "ko" else "Batch runs"
    threshold_label = "병합 기준" if language == "ko" else "Merge threshold"
    lines = [
        title,
        f"- **{sample_label}:** {study.sample_count}",
        f"- **{threshold_label}:** |r| > {threshold:.2f}",
        (
            f"- **{max_label}:** `{study.max_pair[0]}` <-> `{study.max_pair[1]}` (r={study.max_pair[2]:.2f})"
            if study.max_pair[0]
            else f"- **{max_label}:** none"
        ),
    ]
    if study.merge_candidates:
        candidate_label = "분석상 병합 후보" if language == "ko" else "Analysis-only merge candidates"
        retention_note = (
            "하위호환을 위해 스키마는 유지하고 후보만 보고합니다."
            if language == "ko"
            else "Schema is preserved for backward compatibility; only candidates are reported."
        )
        lines.append(
            f"- **{candidate_label}:** {len(study.merge_candidates)} pairs. {retention_note}"
        )
        for candidate in study.merge_candidates[:5]:
            lines.append(
                "  - "
                f"`{candidate.drop_trait}` -> `{candidate.keep_trait}` "
                f"(r={candidate.correlation:.2f}, sigma={candidate.drop_stddev:.3f}->{candidate.keep_stddev:.3f})"
            )
    else:
        lines.append(
            "- 모든 30개 trait를 유지합니다. |r| > 0.70인 쌍이 없습니다."
            if language == "ko"
            else "- Keep all 30 traits. No pair exceeds |r| > 0.70."
        )
    return "\n".join(lines)


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


@lru_cache(maxsize=1)
def load_action_templates() -> dict[str, dict[str, str]]:
    with ACTION_TEMPLATES_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    templates = {str(language): dict(values) for language, values in dict(data).items()}
    for language in ("en", "ko"):
        missing = [action_type for action_type in ACTION_TYPES if action_type not in templates.get(language, {})]
        if missing:
            raise ValueError(
                f"action templates for {language!r} are missing verbs: {', '.join(missing)}"
            )
    return templates


def agent_editor_defaults(
    scenario_name: str,
    *,
    agent_count: int | None = None,
    slot_count: int = AGENT_EDITOR_SLOT_COUNT,
    cultural_prior_id: str | None = None,
    language: str = "en",
) -> tuple[dict[str, Any], ...]:
    config = load_run_config(scenario_path(scenario_name))
    target_agent_count = len(config.agents) if agent_count is None else int(agent_count)
    agent_configs = _resize_agent_pool(config.agents, target_agent_count)
    agents = [agent.to_domain() for agent in agent_configs[:slot_count]]
    if cultural_prior_id:
        agents = [
            _apply_cultural_prior_to_agent(agent, cultural_prior_id, language=language)
            for agent in agents
        ]

    defaults: list[dict[str, Any]] = []
    for slot_index in range(slot_count):
        if slot_index < len(agents):
            agent = agents[slot_index]
            defaults.append(
                {
                    "enabled": True,
                    "name": agent.name,
                    "age": agent.age,
                    "personality": agent.personality.to_dict(),
                }
            )
        else:
            defaults.append(
                {
                    "enabled": False,
                    "name": f"Agent {slot_index + 1}",
                    "age": 21,
                    "personality": dict(PERSONA_TRAIT_DEFAULTS),
                }
            )
    return tuple(defaults)


def _trait_sample_vectors(run_count: int) -> tuple[dict[str, float], ...]:
    presets = load_persona_presets()
    priors = (None, *load_cultural_priors())
    samples: list[dict[str, float]] = []
    for sample_index in range(run_count):
        preset = presets[sample_index % len(presets)]
        prior = priors[sample_index % len(priors)]
        values = {
            field_name: float(preset["personality"][field_name])
            for field_name in PERSONA_TRAIT_FIELDS
        }
        if prior is not None:
            for field_name, shifted_value in zip(
                PERSONA_TRAIT_FIELDS,
                cultural_prior_trait_values(str(prior["id"]), PERSONA_TRAIT_FIELDS),
                strict=True,
            ):
                if field_name in prior["shifts"]:
                    values[field_name] = float(shifted_value)
        samples.append(_apply_analysis_jitter(values, sample_index))
    return tuple(samples)


def _apply_analysis_jitter(values: dict[str, float], sample_index: int) -> dict[str, float]:
    jittered: dict[str, float] = {}
    for offset, field_name in enumerate(PERSONA_TRAIT_FIELDS):
        jitter_bucket = ((sample_index * 7) + (offset * 3)) % 7 - 3
        jitter = jitter_bucket * 0.01
        jittered[field_name] = round(_clamp_unit(values[field_name] + jitter), 4)
    return jittered


def _population_stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return variance ** 0.5


def _pearson_correlation(values_a: list[float], values_b: list[float]) -> float:
    if len(values_a) != len(values_b):
        raise ValueError("correlation inputs must have matching lengths")
    if not values_a:
        return 0.0
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    centered_a = [value - mean_a for value in values_a]
    centered_b = [value - mean_b for value in values_b]
    numerator = sum(value_a * value_b for value_a, value_b in zip(centered_a, centered_b, strict=True))
    denominator = (
        sum(value * value for value in centered_a) * sum(value * value for value in centered_b)
    ) ** 0.5
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _merge_direction(
    trait_a: str,
    trait_b: str,
    stddevs: dict[str, float],
) -> tuple[str, str]:
    if stddevs[trait_a] >= stddevs[trait_b]:
        return trait_a, trait_b
    return trait_b, trait_a


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
    agent_overrides: list[dict[str, Any]] | None = None,
    primary_planning_enabled: bool = False,
    planning_depth: int = 3,
    batch_mode: bool = False,
    batch_runs: int = 10,
    master_seed: int = 20260419,
    language: str = "en",
) -> PlaygroundResult:
    """Run a short scenario and return UI-ready artifacts.

    API keys are only passed into the selected client for this call and are not
    written to disk or stored in module state.
    """

    resolved_batch_runs = max(1, min(int(batch_runs), 100)) if batch_mode else 1
    resolved_ticks = max(1, min(int(ticks), 24))

    if resolved_batch_runs == 1:
        artifacts = _execute_playground_run(
            scenario_name=scenario_name,
            provider=provider,
            api_key=api_key,
            model=model,
            primary_name=primary_name,
            primary_age=primary_age,
            openness=openness,
            conscientiousness=conscientiousness,
            extraversion=extraversion,
            agreeableness=agreeableness,
            neuroticism=neuroticism,
            personality_overrides=personality_overrides,
            ticks=resolved_ticks,
            agent_count=agent_count,
            environment_preset_id=environment_preset_id,
            cultural_prior_id=cultural_prior_id,
            agent_overrides=agent_overrides,
            primary_planning_enabled=primary_planning_enabled,
            planning_depth=planning_depth,
            language=language,
            seed=master_seed if batch_mode else None,
        )
        jsonl = _logs_to_jsonl(artifacts.simulator.logs)
        download_path = _write_download_file(jsonl)
        return PlaygroundResult(
            scenario_name=scenario_name,
            mode=provider,
            timeline_markdown=_timeline_markdown(artifacts.simulator.logs, language=language),
            monologue_markdown=_monologue_markdown(
                artifacts.simulator.monologues,
                artifacts.simulator.monologue_valence,
                language=language,
            ),
            plan_markdown=_plan_markdown(
                artifacts.simulator.planner,
                artifacts.agents,
                language=language,
            ),
            relationship_rows=_relationship_rows(artifacts.simulator),
            jsonl=jsonl,
            download_path=download_path,
            log_count=len(artifacts.simulator.logs),
            agent_count=len(artifacts.agents),
            tick_count=len({entry.tick for entry in artifacts.simulator.logs}),
        )

    seeds = tuple(int(master_seed) + index for index in range(resolved_batch_runs))
    worker_count = min(len(seeds), 8)
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        artifacts_by_seed = list(
            executor.map(
                lambda seed: _execute_playground_run(
                    scenario_name=scenario_name,
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    primary_name=primary_name,
                    primary_age=primary_age,
                    openness=openness,
                    conscientiousness=conscientiousness,
                    extraversion=extraversion,
                    agreeableness=agreeableness,
                    neuroticism=neuroticism,
                    personality_overrides=personality_overrides,
                    ticks=resolved_ticks,
                    agent_count=agent_count,
                    environment_preset_id=environment_preset_id,
                    cultural_prior_id=cultural_prior_id,
                    agent_overrides=agent_overrides,
                    primary_planning_enabled=primary_planning_enabled,
                    planning_depth=planning_depth,
                    language=language,
                    seed=seed,
                ),
                seeds,
            )
        )

    batch_result = _build_batch_result(
        artifacts_by_seed,
        seeds=seeds,
        master_seed=int(master_seed),
    )
    jsonl = _batch_jsonl(batch_result)
    download_path = _write_download_file(jsonl)
    sample_artifacts = artifacts_by_seed[0]
    return PlaygroundResult(
        scenario_name=scenario_name,
        mode=provider,
        timeline_markdown=_batch_timeline_markdown(batch_result, language=language),
        monologue_markdown=_batch_monologue_markdown(language=language),
        plan_markdown=_batch_plan_markdown(language=language),
        relationship_rows=_aggregate_relationship_rows(artifacts_by_seed),
        jsonl=jsonl,
        download_path=download_path,
        log_count=sum(len(artifacts.simulator.logs) for artifacts in artifacts_by_seed),
        agent_count=len(sample_artifacts.agents),
        tick_count=len({entry.tick for entry in sample_artifacts.simulator.logs}),
        batch_result=batch_result,
    )


def _execute_playground_run(
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
    personality_overrides: dict[str, float] | None,
    ticks: int,
    agent_count: int | None,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    agent_overrides: list[dict[str, Any]] | None,
    primary_planning_enabled: bool,
    planning_depth: int,
    language: str,
    seed: int | None,
) -> PlaygroundRunArtifacts:
    config = load_run_config(scenario_path(scenario_name))
    target_agent_count = len(config.agents) if agent_count is None else int(agent_count)
    agent_configs = _resize_agent_pool(config.agents, target_agent_count)
    agents = [agent.to_domain() for agent in agent_configs]
    if cultural_prior_id:
        agents = [
            _apply_cultural_prior_to_agent(agent, cultural_prior_id, language=language)
            for agent in agents
        ]
    resolved_overrides = list(agent_overrides or [])
    if not resolved_overrides:
        resolved_overrides.append(
            {
                "name": primary_name,
                "age": primary_age,
                "personality_overrides": {
                    "openness": openness,
                    "conscientiousness": conscientiousness,
                    "extraversion": extraversion,
                    "agreeableness": agreeableness,
                    "neuroticism": neuroticism,
                    **(personality_overrides or {}),
                },
                "planning": primary_planning_enabled,
            }
        )

    for index, override in enumerate(resolved_overrides):
        if index >= len(agents):
            break
        applied_override = dict(override)
        if index == 0:
            applied_override.setdefault("planning", primary_planning_enabled)
        agents[index] = _customize_agent(
            agents[index],
            name=str(applied_override.get("name", agents[index].name)),
            age=int(applied_override.get("age", agents[index].age)),
            personality_overrides=dict(applied_override.get("personality_overrides", {})),
            inventory=(
                _coerce_inventory(applied_override.get("inventory"))
                if "inventory" in applied_override
                else None
            ),
            factions=(
                _coerce_factions(applied_override.get("factions"))
                if "factions" in applied_override
                else None
            ),
            planning=(
                bool(applied_override["planning"])
                if "planning" in applied_override
                else None
            ),
        )

    environment = config.environment.to_domain()
    if seed is not None:
        environment.conditions = dict(environment.conditions)
        environment.conditions["seed"] = int(seed)
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
            agents=agents,
            language=language,
        ),
        language=language if language in {"ko", "ja", "zh"} else config.prompt_language,
        planning_depth=max(2, min(int(planning_depth), 4)),
    )
    for event in _filter_events_for_agent_pool(config.events, agent_configs):
        simulator.scheduler.schedule(event.to_domain())

    _run_ticks(simulator, ticks=max(1, min(int(ticks), 24)))
    return PlaygroundRunArtifacts(agents=agents, simulator=simulator)


def _build_batch_result(
    artifacts_by_seed: list[PlaygroundRunArtifacts],
    *,
    seeds: tuple[int, ...],
    master_seed: int,
) -> BatchResult:
    tick_totals: dict[int, list[int]] = defaultdict(list)
    tick_action_counts: dict[int, Counter[str]] = defaultdict(Counter)
    agent_totals: dict[str, list[int]] = defaultdict(list)
    agent_action_counts: dict[str, Counter[str]] = defaultdict(Counter)
    total_actions_per_run: list[int] = []

    for artifacts in artifacts_by_seed:
        total_actions_per_run.append(len(artifacts.simulator.logs))
        logs_by_tick: dict[int, list[SimulationLogEntry]] = defaultdict(list)
        logs_by_agent: dict[str, list[SimulationLogEntry]] = defaultdict(list)
        for entry in artifacts.simulator.logs:
            logs_by_tick[entry.tick].append(entry)
            logs_by_agent[entry.agent_id].append(entry)
        for tick, tick_logs in logs_by_tick.items():
            tick_totals[tick].append(len(tick_logs))
            tick_action_counts[tick].update(entry.action.action_type for entry in tick_logs)
        for agent_id, agent_logs in logs_by_agent.items():
            agent_totals[agent_id].append(len(agent_logs))
            agent_action_counts[agent_id].update(
                entry.action.action_type for entry in agent_logs
            )

    per_tick_stats = tuple(
        BatchTickStat(
            tick=tick,
            mean_actions=_mean(tick_totals[tick]),
            action_type_counts=dict(sorted(tick_action_counts[tick].items())),
            top_action_type=_top_action_type(tick_action_counts[tick]),
        )
        for tick in sorted(tick_totals)
    )
    per_agent_stats = tuple(
        BatchAgentStat(
            agent_id=agent_id,
            mean_actions=_mean(agent_totals[agent_id]),
            action_type_counts=dict(sorted(agent_action_counts[agent_id].items())),
            top_action_type=_top_action_type(agent_action_counts[agent_id]),
        )
        for agent_id in sorted(agent_totals)
    )

    return BatchResult(
        batch_size=len(artifacts_by_seed),
        master_seed=master_seed,
        seeds=seeds,
        reproducibility_coefficient=_reproducibility_coefficient(total_actions_per_run),
        per_tick_stats=per_tick_stats,
        per_agent_stats=per_agent_stats,
    )


def _batch_jsonl(batch_result: BatchResult) -> str:
    rows: list[dict[str, object]] = [
        {
            "record_type": "batch_summary",
            "batch_size": batch_result.batch_size,
            "master_seed": batch_result.master_seed,
            "seeds": list(batch_result.seeds),
            "reproducibility_coefficient": batch_result.reproducibility_coefficient,
        }
    ]
    rows.extend(
        {
            "record_type": "tick_stat",
            "tick": stat.tick,
            "mean_actions": stat.mean_actions,
            "top_action_type": stat.top_action_type,
            "action_type_counts": stat.action_type_counts,
        }
        for stat in batch_result.per_tick_stats
    )
    rows.extend(
        {
            "record_type": "agent_stat",
            "agent_id": stat.agent_id,
            "mean_actions": stat.mean_actions,
            "top_action_type": stat.top_action_type,
            "action_type_counts": stat.action_type_counts,
        }
        for stat in batch_result.per_agent_stats
    )
    return "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)


def _batch_timeline_markdown(batch_result: BatchResult, *, language: str = "en") -> str:
    if language == "ko":
        lines = [
            "### 배치 타임라인",
            (
                f"- 반복 {batch_result.batch_size}회 | 마스터 시드 {batch_result.master_seed} "
                f"| 재현성 계수 {batch_result.reproducibility_coefficient:.3f}"
            ),
        ]
        for stat in batch_result.per_tick_stats:
            top_counts = _top_count_text(stat.action_type_counts)
            lines.append(
                f"- **틱 {stat.tick:02d}** 평균 행동 {stat.mean_actions:.1f} | 상위 액션: {top_counts}"
            )
        return "\n".join(lines)

    lines = [
        "### Batch timeline",
        (
            f"- Batch runs: {batch_result.batch_size} | Master seed: {batch_result.master_seed} "
            f"| Reproducibility coefficient: {batch_result.reproducibility_coefficient:.3f}"
        ),
    ]
    for stat in batch_result.per_tick_stats:
        top_counts = _top_count_text(stat.action_type_counts)
        lines.append(
            f"- **Tick {stat.tick:02d}** mean actions={stat.mean_actions:.1f} | top actions: {top_counts}"
        )
    return "\n".join(lines)


def _batch_monologue_markdown(*, language: str = "en") -> str:
    if language == "ko":
        return "배치 모드는 여러 시드를 집계합니다. 개별 내적 독백은 단일 실행 모드에서 확인하세요."
    return "Batch mode aggregates multiple seeds. Use single-run mode to inspect per-agent monologues."


def _batch_plan_markdown(*, language: str = "en") -> str:
    if language == "ko":
        return "배치 모드는 여러 시드를 집계합니다. 개별 HTN 계획은 단일 실행 모드에서 확인하세요."
    return "Batch mode aggregates multiple seeds. Use single-run mode to inspect per-run HTN plans."


def _aggregate_relationship_rows(
    artifacts_by_seed: list[PlaygroundRunArtifacts],
) -> list[dict[str, object]]:
    aggregated: dict[tuple[str, str], dict[str, object]] = {}
    for artifacts in artifacts_by_seed:
        for row in _relationship_rows(artifacts.simulator):
            key = (str(row["source"]), str(row["target"]))
            bucket = aggregated.setdefault(
                key,
                {
                    "source": row["source"],
                    "target": row["target"],
                    "relationship_type": row["relationship_type"],
                    "weight_total": 0.0,
                    "trust_total": 0.0,
                    "familiarity_total": 0.0,
                    "count": 0,
                },
            )
            bucket["weight_total"] = float(bucket["weight_total"]) + float(row["weight"])
            bucket["trust_total"] = float(bucket["trust_total"]) + float(row["trust"])
            bucket["familiarity_total"] = float(bucket["familiarity_total"]) + float(
                row["familiarity"]
            )
            bucket["count"] = int(bucket["count"]) + 1

    rows: list[dict[str, object]] = []
    for key in sorted(aggregated):
        bucket = aggregated[key]
        count = max(1, int(bucket["count"]))
        rows.append(
            {
                "source": bucket["source"],
                "target": bucket["target"],
                "relationship_type": bucket["relationship_type"],
                "weight": round(float(bucket["weight_total"]) / count, 3),
                "trust": round(float(bucket["trust_total"]) / count, 3),
                "familiarity": round(float(bucket["familiarity_total"]) / count, 3),
            }
        )
    return rows


def _mean(values: list[int]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _reproducibility_coefficient(action_counts: list[int]) -> float:
    if not action_counts:
        return 1.0
    mean_count = sum(action_counts) / len(action_counts)
    if mean_count <= 0:
        return 1.0
    variance = sum((count - mean_count) ** 2 for count in action_counts) / len(action_counts)
    normalized_variance = variance / max(mean_count**2, 1.0)
    return round(max(0.0, 1.0 - normalized_variance), 3)


def _top_action_type(counts: Counter[str]) -> str:
    if not counts:
        return "observe"
    return min(
        counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[0]


def _top_count_text(action_type_counts: dict[str, int]) -> str:
    ranked = sorted(action_type_counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{action_type}x{count}" for action_type, count in ranked[:3])


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
    inventory: Inventory | None = None,
    factions: dict[str, float] | None = None,
    planning: bool | None = None,
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
        inventory=agent.inventory if inventory is None else inventory,
        factions=dict(agent.factions or {}) if factions is None else dict(factions),
        planning=agent.planning if planning is None else planning,
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
    inventory: Inventory | None = None,
    factions: dict[str, float] | None = None,
    planning: bool | None = None,
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
        inventory=inventory,
        factions=factions,
        planning=planning,
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


def _coerce_inventory(value: object) -> Inventory | None:
    if value is None:
        return None
    if isinstance(value, Inventory):
        return Inventory(item_ids=list(value.item_ids))
    if isinstance(value, (list, tuple)):
        inventory = Inventory()
        for item in value:
            if isinstance(item, str) and item.strip():
                inventory.add(item)
        return inventory
    raise TypeError(f"unsupported inventory override: {type(value)!r}")


def _coerce_factions(value: object) -> dict[str, float] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f"unsupported factions override: {type(value)!r}")
    return {str(faction_id): float(score) for faction_id, score in value.items()}


def _build_client(
    *,
    provider: Provider,
    api_key: str,
    model: str,
    config: SimulationRunConfig,
    agents: list[Persona],
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
        _scripted_responder(agents=agents, fallback=config.local_response, language=language)
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


def _scripted_responder(*, agents: list[Persona], fallback: str, language: str = "en"):
    agent_ids = [agent.agent_id for agent in agents]
    persona_by_id = {agent.agent_id: agent for agent in agents}
    call_counts = {agent.agent_id: 0 for agent in agents}

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
        persona = persona_by_id.get(agent_id)
        tick = call_counts.get(agent_id, 0)
        target = _default_scripted_target(agent_ids, agent_id, tick=tick)
        location = _extract_prompt_line(user_prompt, key="location", language=language) or (
            "공용 공간" if _template_language(language) == "ko" else "shared space"
        )
        call_counts[agent_id] = tick + 1
        payload = _scripted_action_payload(
            persona=persona,
            agent_id=agent_id,
            location=location,
            user_prompt=user_prompt,
            default_target=target,
            trigger_target=_extract_trigger_target(user_prompt, agent_ids, agent_id, language),
            tick=tick,
            language=language,
        )
        if payload is None:
            return fallback
        return json.dumps(payload, ensure_ascii=False)

    return respond


def _extract_agent_id(system_prompt: str) -> str | None:
    match = re.search(r"Persona ID:\s*([A-Za-z0-9_-]+)", system_prompt)
    return match.group(1) if match else None


def _extract_line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def _scripted_action_payload(
    *,
    persona: Persona | None,
    agent_id: str,
    location: str,
    user_prompt: str,
    default_target: str | None,
    trigger_target: str | None,
    tick: int,
    language: str = "en",
) -> dict[str, Any]:
    trigger_text = _extract_trigger_text(user_prompt, language)
    action_type = _scripted_action_type(
        persona=persona,
        agent_id=agent_id,
        location=location,
        tick=tick,
        user_prompt=user_prompt,
        trigger_text=trigger_text,
        default_target=default_target,
        trigger_target=trigger_target,
    )
    target = _resolved_scripted_target(
        action_type,
        default_target=default_target,
        trigger_target=trigger_target,
    )
    metadata, topic = _scripted_metadata_and_topic(
        action_type=action_type,
        agent_id=agent_id,
        persona=persona,
        target=target,
        tick=tick,
        trigger_text=trigger_text,
        location=location,
        language=language,
    )
    metadata.update(
        {
            "rule": "replay-action-vocabulary",
            "scripted": True,
            "template_language": _template_language(language),
            "tick": tick,
            "topic": topic,
        }
    )
    return {
        "action_type": action_type,
        "target": target,
        "content": _render_scripted_action_content(
            action_type=action_type,
            agent_id=agent_id,
            target=target,
            location=location,
            topic=topic,
            language=language,
        ),
        "metadata": metadata,
    }


def _scripted_action_type(
    *,
    persona: Persona | None,
    agent_id: str,
    location: str,
    tick: int,
    user_prompt: str,
    trigger_text: str,
    default_target: str | None,
    trigger_target: str | None,
) -> str:
    has_trigger = _has_trigger(trigger_text)
    personality = (
        persona.personality
        if persona is not None
        else Personality(**PERSONALITY_NEUTRAL_DEFAULTS)
    )
    inventory = persona.inventory if persona is not None else None
    factions = dict(persona.factions or {}) if persona is not None and persona.factions else {}
    target_candidate = trigger_target or default_target
    has_target = target_candidate is not None
    trust_by_target = _extract_relationship_trusts(user_prompt)
    target_trust = 1.0 if target_candidate is None else trust_by_target.get(target_candidate, 1.0)
    arousal = _extract_arousal(user_prompt)
    has_leader_role = _has_leader_role(persona)

    if has_target and has_leader_role and personality.conscientiousness > 0.7 and tick in {1, 4, 7}:
        return "quest_offer"
    if (
        has_target
        and personality.sadism + personality.machiavellianism > 1.0
        and target_trust <= 0.45
        and tick % 4 == 1
    ):
        return "attack_target"
    if has_target and _defend_self_trigger(trigger_text, agent_id):
        return "defend_self"
    if arousal > 0.8 and _has_threat(trigger_text):
        return "flee"
    if inventory is not None and inventory.item_ids and tick % 5 == 2:
        return "use_item"
    if personality.openness > 0.55 and tick % 5 == 1:
        return "pickup_item"
    if inventory is not None and inventory.item_ids and tick % 6 == 3:
        return "drop_item"
    if has_target and personality.fairness >= 0.5 and tick % 6 == 2:
        return "trade_offer"
    if _has_quest_trigger(trigger_text) and tick % 2 == 0:
        return "quest_accept"
    if _has_quest_trigger(trigger_text) and tick % 2 == 1:
        return "quest_complete"
    if not factions and personality.power > 0.6 and tick % 6 == 4:
        return "faction_join"
    if factions and personality.machiavellianism > 0.6 and tick % 7 == 5:
        return "faction_betray"
    if tick % 6 == 5 and (personality.openness > 0.6 or (inventory is not None and inventory.item_ids)):
        return "craft_item"
    if personality.achievement > 0.6 and tick % 8 == 6:
        return "level_up"
    if personality.need_for_cognition > 0.6 and tick % 7 == 3:
        return "use_skill"
    if tick == 0:
        return "speak" if has_trigger else "observe"

    action_cycle = [
        action_type
        for action_type in SOCIAL_ACTION_TYPES
        if action_type in {"speak", "observe", "move", "query_memory", "propose_plan"}
    ]
    if has_target:
        action_cycle.extend(
            [
                action_type
                for action_type in SOCIAL_ACTION_TYPES
                if action_type in {"offer", "accept", "refuse", "give", "take", "persuade"}
            ]
        )
    if personality.agreeableness >= 0.65 or personality.trait_empathy >= 0.6:
        action_cycle.append("comfort")
    if personality.conscientiousness >= 0.65 or personality.need_for_cognition >= 0.65:
        action_cycle.append("propose_plan")
    if personality.kantianism >= 0.6 or personality.fairness >= 0.6:
        action_cycle.append("defend")
    if personality.extraversion >= 0.58:
        action_cycle.append("gossip")
    if personality.extraversion <= 0.4:
        action_cycle.append("alone")
    if personality.risk_tolerance >= 0.6 or personality.stimulation >= 0.6:
        action_cycle.extend(["enter", "exit"])
    if personality.machiavellianism >= 0.5 or personality.narcissism >= 0.6:
        action_cycle.append("deceive")
    if personality.psychopathy + personality.sadism >= 0.75:
        action_cycle.append("threaten")
    if personality.psychopathy + personality.sadism >= 1.05:
        action_cycle.append("attack")
    if has_trigger and personality.agreeableness >= 0.6:
        action_cycle.append("offer")
    deduped_cycle = _dedupe_preserve_order(action_cycle)
    cycle_index = (tick + _stable_bucket(agent_id, location, trigger_target or "")) % len(
        deduped_cycle
    )
    return deduped_cycle[cycle_index]


def _scripted_metadata_and_topic(
    *,
    action_type: str,
    agent_id: str,
    persona: Persona | None,
    target: str | None,
    tick: int,
    trigger_text: str,
    location: str,
    language: str,
) -> tuple[dict[str, Any], str]:
    if action_type not in GAME_ACTION_TYPES:
        return {}, _scripted_topic(trigger_text, location, language)

    if action_type == "attack_target":
        damage = 6 + _stable_bucket(agent_id, str(tick)) % 5
        return {"damage": damage}, f"damage {damage}"
    if action_type == "use_skill":
        skill_id = f"skill_{1 + _stable_bucket(agent_id, str(tick)) % 3}"
        return {"skill_id": skill_id}, skill_id
    if action_type in {"use_item", "pickup_item", "drop_item"}:
        item_id = _inventory_item_id(persona, tick)
        return {"item_id": item_id}, item_id
    if action_type == "trade_offer":
        give_item = _inventory_item_id(persona, tick)
        receive_item = f"item_{(tick + 1) % 5}"
        return {
            "give_items": [give_item],
            "receive_items": [receive_item],
        }, f"{give_item} for {receive_item}"
    if action_type in {"quest_offer", "quest_accept", "quest_complete"}:
        quest_id = f"quest_{target or agent_id}_{tick}"
        return {"quest_id": quest_id}, quest_id
    if action_type in {"faction_join", "faction_betray"}:
        faction_id = _primary_faction_id(persona) or "leader"
        return {"faction_id": faction_id}, faction_id
    if action_type == "craft_item":
        item_id = f"crafted_item_{tick % 5}"
        return {
            "materials": _craft_materials(persona),
            "item_id": item_id,
        }, item_id
    if action_type == "level_up":
        stat = _level_up_stat(persona)
        return {"stat": stat}, stat
    return {}, _scripted_topic(trigger_text, location, language)


def _extract_relationship_trusts(user_prompt: str) -> dict[str, float]:
    trusts: dict[str, float] = {}
    pattern = re.compile(
        r"^- (?P<target>[A-Za-z0-9_-]+): type=[^,\n]+, weight=[-+]?\d+(?:\.\d+)?, trust=(?P<trust>[-+]?\d+(?:\.\d+)?)$",
        re.MULTILINE,
    )
    for match in pattern.finditer(user_prompt):
        trusts[match.group("target")] = float(match.group("trust"))
    return trusts


def _extract_arousal(user_prompt: str) -> float:
    match = re.search(r"arousal=(?P<arousal>[-+]?\d+(?:\.\d+)?)", user_prompt)
    return float(match.group("arousal")) if match else 0.0


def _has_leader_role(persona: Persona | None) -> bool:
    if persona is None or not persona.factions:
        return False
    return any(
        token in faction_id.lower()
        for faction_id in persona.factions
        for token in ("leader", "authority")
    )


def _has_threat(trigger_text: str) -> bool:
    normalized = trigger_text.lower()
    return any(
        token in normalized
        for token in ("threat", "attack", "danger", "ambush", "betray", "hazard")
    )


def _defend_self_trigger(trigger_text: str, agent_id: str) -> bool:
    normalized = trigger_text.lower()
    agent_token = agent_id.lower()
    return agent_token in normalized and any(
        token in normalized for token in ("attack", "attacks", "attacked", "strikes", "hits")
    )


def _has_quest_trigger(trigger_text: str) -> bool:
    normalized = trigger_text.lower()
    return "quest" in normalized or "mission" in normalized


def _primary_faction_id(persona: Persona | None) -> str | None:
    if persona is None or not persona.factions:
        return None
    return max(persona.factions.items(), key=lambda item: (item[1], item[0]))[0]


def _inventory_item_id(persona: Persona | None, tick: int) -> str:
    if persona is not None and persona.inventory is not None and persona.inventory.item_ids:
        items = list(persona.inventory.item_ids)
        return items[tick % len(items)]
    return f"item_{tick % 5}"


def _craft_materials(persona: Persona | None) -> list[str]:
    if persona is not None and persona.inventory is not None:
        materials = [item for item in persona.inventory.item_ids if item.strip()][:2]
        if materials:
            return materials
    return ["wood", "ore"]


def _level_up_stat(persona: Persona | None) -> str:
    if persona is None:
        return "achievement"
    priority = (
        "conscientiousness",
        "openness",
        "extraversion",
        "agreeableness",
        "achievement",
        "power",
    )
    return max(priority, key=lambda field_name: getattr(persona.personality, field_name))


def _render_scripted_action_content(
    *,
    action_type: str,
    agent_id: str,
    target: str | None,
    location: str,
    topic: str,
    language: str,
) -> str:
    templates = load_action_templates()
    template_language = _template_language(language)
    template = templates[template_language][action_type]
    return template.format(
        agent=agent_id,
        target=target or ("주변 사람들" if template_language == "ko" else "the group"),
        location=location,
        topic=topic,
    )


def _scripted_topic(trigger_text: str, location: str, language: str) -> str:
    template_language = _template_language(language)
    if _has_trigger(trigger_text):
        topic = re.sub(r"\s+", " ", trigger_text).strip().rstrip(".!?")
        if topic:
            return topic[:72].rstrip()
    return "공용 루틴" if template_language == "ko" else f"coordination in {location}"


def _resolved_scripted_target(
    action_type: str,
    *,
    default_target: str | None,
    trigger_target: str | None,
) -> str | None:
    if action_type in UNTARGETED_ACTION_TYPES:
        return None
    return trigger_target or default_target


def _extract_prompt_line(text: str, *, key: str, language: str) -> str | None:
    preferred_language = _prompt_line_language(language)
    prefixes = [PROMPT_LINE_PREFIXES[preferred_language][key], *(
        values[key]
        for candidate, values in PROMPT_LINE_PREFIXES.items()
        if candidate != preferred_language
    )]
    for prefix in prefixes:
        value = _extract_line_value(text, prefix)
        if value is not None:
            return value
    return None


def _extract_trigger_text(user_prompt: str, language: str) -> str:
    return _extract_prompt_line(user_prompt, key="trigger", language=language) or _no_trigger_line(
        language
    )


def _extract_trigger_target(
    user_prompt: str,
    agent_ids: list[str],
    self_id: str,
    language: str,
) -> str | None:
    trigger_text = _extract_trigger_text(user_prompt, language)
    for candidate in agent_ids:
        if candidate != self_id and candidate in trigger_text:
            return candidate
    return None


def _default_scripted_target(agent_ids: list[str], self_id: str, *, tick: int) -> str | None:
    candidates = [candidate for candidate in agent_ids if candidate != self_id]
    if not candidates:
        return None
    return candidates[_stable_bucket(self_id, str(tick)) % len(candidates)]


def _prompt_line_language(language: str) -> str:
    normalized = str(language).strip().lower()
    return normalized if normalized in PROMPT_LINE_PREFIXES else "en"


def _template_language(language: str) -> str:
    return "ko" if _prompt_line_language(language) == "ko" else "en"


def _no_trigger_line(language: str) -> str:
    return NO_TRIGGER_LINES[_prompt_line_language(language)]


def _has_trigger(trigger_text: str) -> bool:
    normalized = trigger_text.strip()
    return bool(normalized) and normalized not in set(NO_TRIGGER_LINES.values())


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _stable_bucket(*parts: str) -> int:
    payload = "|".join(part for part in parts if part)
    return sum((index + 1) * ord(character) for index, character in enumerate(payload))


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


def _monologue_markdown(
    monologues: list[Monologue],
    valence_by_tick: dict[tuple[str, int], float],
    *,
    language: str = "en",
) -> str:
    if not monologues:
        return (
            "아직 기록된 내적 독백이 없습니다. 시뮬레이션을 실행하면 에이전트별 사적 생각이 여기에 표시됩니다."
            if language == "ko"
            else "No inner monologues yet. Run the simulation to see each agent's private thoughts."
        )

    lines: list[str] = []
    for monologue in monologues:
        valence = valence_by_tick.get((monologue.agent_id, monologue.tick), 0.0)
        color = "#15803d" if valence > 0.2 else "#b91c1c" if valence < -0.2 else "#64748b"
        label = f"{monologue.agent_id} · t{monologue.tick}"
        lines.append(
            f"- <span style=\"color:{color}\"><strong>{escape(label)}</strong> {escape(monologue.text)}</span>"
        )
    return "\n".join(lines)


def _plan_markdown(
    planner: HierarchicalPlanner,
    agents: list[Persona],
    *,
    language: str = "en",
) -> str:
    planning_agents = [agent for agent in agents if agent.planning]
    if not planning_agents:
        return (
            "계층 계획이 비활성화되어 현재 계획이 없습니다."
            if language == "ko"
            else "Hierarchical planning is disabled for this run."
        )

    title = "### 현재 계획" if language == "ko" else "### Current plan"
    achievement_label = "목표 달성률" if language == "ko" else "Goal achievement rate"
    no_plan_label = (
        "분해된 목표가 아직 없습니다."
        if language == "ko"
        else "No decomposed goal is available yet."
    )
    lines = [
        title,
        f"- **{achievement_label}:** {planner.achievement_rate([agent.agent_id for agent in planning_agents]):.2f}",
    ]
    for agent in planning_agents:
        plan = planner.plan_for(agent.agent_id)
        if not plan:
            lines.append(f"- **{agent.name}**: {no_plan_label}")
            continue
        lines.append(f"- **{agent.name}**")
        for task in plan:
            depth = _task_depth(task, plan)
            prefix = "  " * depth
            status = _task_status_badge(task.status)
            lines.append(f"{prefix}- {status} {task.description}")
    return "\n".join(lines)


def _task_depth(task: Task, plan: tuple[Task, ...]) -> int:
    by_id = {candidate.task_id: candidate for candidate in plan}
    depth = 0
    current = task
    while current.parent_id is not None and current.parent_id in by_id:
        depth += 1
        current = by_id[current.parent_id]
    return depth


def _task_status_badge(status: str) -> str:
    return {
        "completed": "[x]",
        "active": "[>]",
        "failed": "[!]",
        "pending": "[ ]",
    }.get(status, "[ ]")


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
