"""Multilingual prompt templates for Knoema agents and decisions."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Literal, Protocol

from knoema.relationship import Relationship
from knoema.types import (
    PERSONALITY_NEUTRAL_DEFAULTS,
    AgentID,
    Emotion,
    Memory,
    Personality,
    WorldEvent,
)

PromptLanguage = Literal["en", "ko", "ja", "zh"]
SUPPORTED_PROMPT_LANGUAGES: tuple[PromptLanguage, ...] = ("en", "ko", "ja", "zh")

_LANGUAGE_ALIASES: Mapping[str, PromptLanguage] = {
    "en": "en",
    "eng": "en",
    "english": "en",
    "en-us": "en",
    "en-gb": "en",
    "ko": "ko",
    "kor": "ko",
    "korean": "ko",
    "ko-kr": "ko",
    "kr": "ko",
    "ja": "ja",
    "jpn": "ja",
    "japanese": "ja",
    "ja-jp": "ja",
    "jp": "ja",
    "zh": "zh",
    "zho": "zh",
    "chinese": "zh",
    "zh-cn": "zh",
    "zh-hans": "zh",
    "cn": "zh",
}

_PERSONA_COPY: Mapping[PromptLanguage, Mapping[str, str]] = {
    "en": {
        "role": "You are roleplaying as {name}.",
        "age": "Age",
        "background": "Background",
        "traits": "Personality traits",
        "values": "Core values",
        "goals": "Active goals",
        "empty": "None provided",
        "guidance": (
            "Stay consistent with this persona, remember prior social context, "
            "and respond in a way that preserves believable long-term behavior."
        ),
    },
    "ko": {
        "role": "당신은 {name} 역할을 일관되게 연기합니다.",
        "age": "나이",
        "background": "배경",
        "traits": "성격 특성",
        "values": "핵심 가치",
        "goals": "현재 목표",
        "empty": "제공되지 않음",
        "guidance": "이 페르소나와 이전 사회적 맥락을 유지하며, 장기적으로 믿을 수 있는 행동을 하세요.",
    },
    "ja": {
        "role": "あなたは{name}として一貫してロールプレイします。",
        "age": "年齢",
        "background": "背景",
        "traits": "性格特性",
        "values": "中核価値",
        "goals": "現在の目標",
        "empty": "未指定",
        "guidance": "このペルソナと過去の社会的文脈を保ち、長期的に自然な行動をしてください。",
    },
    "zh": {
        "role": "你将持续以{name}的身份进行角色扮演。",
        "age": "年龄",
        "background": "背景",
        "traits": "人格特征",
        "values": "核心价值",
        "goals": "当前目标",
        "empty": "未提供",
        "guidance": "保持该角色与既有社会语境的一致性, 并给出长期可信的行为。",
    },
}

_DECISION_COPY: Mapping[PromptLanguage, Mapping[str, str]] = {
    "en": {
        "instruction": "Choose the next action as strict JSON.",
        "schema": 'Schema: {"action_type": str, "target": str | null, "content": str}',
        "time": "Time",
        "location": "Location",
        "conditions": "Conditions",
        "emotion": "Emotion",
        "trigger": "Trigger",
        "no_trigger": "No immediate trigger.",
        "memories": "Memories",
        "relationships": "Relationships",
        "none": "- None",
    },
    "ko": {
        "instruction": "다음 행동을 엄격한 JSON으로 선택하세요.",
        "schema": '스키마: {"action_type": str, "target": str | null, "content": str}',
        "time": "시간",
        "location": "위치",
        "conditions": "조건",
        "emotion": "감정",
        "trigger": "트리거",
        "no_trigger": "즉시 반응할 트리거가 없습니다.",
        "memories": "기억",
        "relationships": "관계",
        "none": "- 없음",
    },
    "ja": {
        "instruction": "次の行動を厳密なJSONとして選択してください。",
        "schema": 'スキーマ: {"action_type": str, "target": str | null, "content": str}',
        "time": "時刻",
        "location": "場所",
        "conditions": "条件",
        "emotion": "感情",
        "trigger": "トリガー",
        "no_trigger": "直近のトリガーはありません。",
        "memories": "記憶",
        "relationships": "関係",
        "none": "- なし",
    },
    "zh": {
        "instruction": "请以严格JSON选择下一步行动。",
        "schema": '模式: {"action_type": str, "target": str | null, "content": str}',
        "time": "时间",
        "location": "位置",
        "conditions": "条件",
        "emotion": "情绪",
        "trigger": "触发事件",
        "no_trigger": "没有需要立即回应的触发事件。",
        "memories": "记忆",
        "relationships": "关系",
        "none": "- 无",
    },
}

_BIG_FIVE_LINES: tuple[tuple[str, str], ...] = (
    ("Openness", "openness"),
    ("Conscientiousness", "conscientiousness"),
    ("Extraversion", "extraversion"),
    ("Agreeableness", "agreeableness"),
    ("Neuroticism", "neuroticism"),
)
_PERSONALITY_TIER_LINES: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    (
        "Tier B - HEXACO + Light Triad",
        (
            ("Honesty-Humility", "honesty_humility"),
            ("Kantianism", "kantianism"),
            ("Humanism", "humanism"),
            ("Faith in humanity", "faith_in_humanity"),
        ),
    ),
    (
        "Tier C - Dark Tetrad",
        (
            ("Machiavellianism", "machiavellianism"),
            ("Narcissism", "narcissism"),
            ("Psychopathy", "psychopathy"),
            ("Sadism", "sadism"),
        ),
    ),
    (
        "Tier E - Behavioral dispositions",
        (
            ("Risk tolerance", "risk_tolerance"),
            ("Locus of control", "locus_of_control"),
            ("Need for cognition", "need_for_cognition"),
            ("Trait empathy", "trait_empathy"),
        ),
    ),
    (
        "Tier F - Moral foundations",
        (
            ("Care / Harm", "care_harm"),
            ("Fairness", "fairness"),
            ("Binding morals", "binding_morals"),
        ),
    ),
    (
        "Tier G - Schwartz 10 values",
        (
            ("Self-direction", "self_direction"),
            ("Stimulation", "stimulation"),
            ("Hedonism", "hedonism"),
            ("Achievement", "achievement"),
            ("Power", "power"),
            ("Security", "security"),
            ("Conformity", "conformity"),
            ("Tradition", "tradition"),
            ("Benevolence", "benevolence"),
            ("Universalism", "universalism"),
        ),
    ),
)


class PromptPersona(Protocol):
    agent_id: AgentID
    name: str
    age: int
    background: str
    personality: Personality
    values: list[str]
    goals: list[str]


class DecisionPromptEnvironment(Protocol):
    @property
    def timestamp(self) -> datetime: ...

    @property
    def location(self) -> str: ...

    @property
    def conditions(self) -> Mapping[str, Any]: ...


def normalize_prompt_language(language: str | PromptLanguage) -> PromptLanguage:
    """Normalize language aliases to Knoema's prompt language codes."""

    normalized = str(language).strip().lower().replace("_", "-")
    try:
        return _LANGUAGE_ALIASES[normalized]
    except KeyError as exc:
        supported = ", ".join(SUPPORTED_PROMPT_LANGUAGES)
        raise ValueError(f"unsupported prompt language {language!r}; expected one of: {supported}") from exc


def render_persona_system_prompt(
    persona: PromptPersona,
    language: str | PromptLanguage = "en",
) -> str:
    """Render a persona system prompt in English, Korean, Japanese, or Chinese."""

    resolved = normalize_prompt_language(language)
    copy = _PERSONA_COPY[resolved]
    values = _join_or_empty(persona.values, copy["empty"])
    goals = _join_or_empty(persona.goals, copy["empty"])
    theory_of_mind = getattr(persona, "theory_of_mind", None)
    theory_of_mind_text = (
        "enabled (persona opt-in belief tracking)"
        if getattr(theory_of_mind, "enabled", False)
        else "disabled"
    )
    lines = [
        copy["role"].format(name=persona.name),
        "",
        f"Persona ID: {persona.agent_id}",
        f"{copy['age']}: {persona.age}",
        f"{copy['background']}: {persona.background}",
        "",
        f"{copy['traits']}:",
        *[
            f"- {label}: {getattr(persona.personality, field_name):.2f}"
            for label, field_name in _BIG_FIVE_LINES
        ],
    ]
    for title, tier_fields in _PERSONALITY_TIER_LINES:
        if not _tier_has_signal(persona.personality, tier_fields):
            continue
        lines.extend(
            [
                "",
                f"{title}:",
                *[
                    f"- {label}: {getattr(persona.personality, field_name):.2f}"
                    for label, field_name in tier_fields
                ],
            ]
        )
    lines.extend(
        [
            "",
            f"{copy['values']}: {values}",
            f"{copy['goals']}: {goals}",
            f"{copy.get('tom', 'Theory of mind')}: {theory_of_mind_text}",
            f"Hierarchical planning: {'enabled' if getattr(persona, 'planning', False) else 'disabled'}",
            f"Social learning: {'enabled' if getattr(persona, 'social_learning', False) else 'disabled'}",
            "",
            copy["guidance"],
        ]
    )
    return "\n".join(lines)


def render_decision_user_prompt(
    *,
    memories: Sequence[Memory],
    relationships: Mapping[AgentID, Relationship],
    environment: DecisionPromptEnvironment,
    emotion: Emotion,
    trigger: WorldEvent | None,
    theory_of_mind_notes: Sequence[str] | None = None,
    language: str | PromptLanguage = "en",
) -> str:
    """Render the user-side decision prompt in a supported language."""

    resolved = normalize_prompt_language(language)
    copy = _DECISION_COPY[resolved]
    memory_lines = "\n".join(
        f"- {memory.timestamp.isoformat()} [{memory.memory_type}] {memory.content}"
        for memory in memories[:8]
    )
    relationship_lines = "\n".join(
        f"- {target}: type={relationship.relationship_type}, "
        f"weight={relationship.weight:.2f}, trust={relationship.trust:.2f}"
        for target, relationship in relationships.items()
    )
    trigger_text = trigger.description if trigger is not None else copy["no_trigger"]
    lines = [
        copy["instruction"],
        copy["schema"],
        f"{copy['time']}: {environment.timestamp.isoformat()}",
        f"{copy['location']}: {environment.location}",
        f"{copy['conditions']}: {json.dumps(environment.conditions, ensure_ascii=False, sort_keys=True)}",
        f"{copy['emotion']}: valence={emotion.valence:.2f}, arousal={emotion.arousal:.2f}, dominance={emotion.dominance:.2f}",
        f"{copy['trigger']}: {trigger_text}",
        f"{copy['memories']}:",
        memory_lines or copy["none"],
        f"{copy['relationships']}:",
        relationship_lines or copy["none"],
    ]
    if theory_of_mind_notes:
        lines.extend(
            [
                f"{copy.get('tom', 'Theory of mind')}:",
                *theory_of_mind_notes,
            ]
        )
    return "\n".join(lines)


def _join_or_empty(values: Sequence[str], empty_text: str) -> str:
    return ", ".join(values) if values else empty_text


def _tier_has_signal(
    personality: Personality,
    tier_fields: Sequence[tuple[str, str]],
) -> bool:
    for _, field_name in tier_fields:
        if abs(getattr(personality, field_name) - PERSONALITY_NEUTRAL_DEFAULTS[field_name]) > 1e-9:
            return True
    return False


__all__ = [
    "SUPPORTED_PROMPT_LANGUAGES",
    "PromptLanguage",
    "normalize_prompt_language",
    "render_decision_user_prompt",
    "render_persona_system_prompt",
]
