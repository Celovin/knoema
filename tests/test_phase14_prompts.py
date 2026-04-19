from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import pytest

from knoema import (
    SUPPORTED_PROMPT_LANGUAGES,
    DecisionEngine,
    EnvironmentContext,
    LocalClient,
    Memory,
    Persona,
    Personality,
    Relationship,
    normalize_prompt_language,
    render_persona_system_prompt,
)
from knoema.decision import build_decision_messages
from knoema.protocols import Message
from knoema.types import Emotion, WorldEvent


def _persona() -> Persona:
    return Persona(
        agent_id="alice",
        name="Alice",
        age=17,
        background="Dormitory student who keeps careful notes.",
        personality=Personality(0.7, 0.6, 0.3, 0.8, 0.4),
        values=["honesty"],
        goals=["keep peace with roommate"],
    )


def _environment() -> EnvironmentContext:
    return EnvironmentContext(
        agent_id="alice",
        timestamp=datetime(2026, 4, 18, 9, 0),
        location_path=("Korea", "Seoul", "Dormitory"),
        conditions={"weather": "rain"},
    )


def _memory() -> Memory:
    return Memory(
        id="mem-001",
        agent_id="alice",
        timestamp=datetime(2026, 4, 18, 8, 30),
        content="Bob helped Alice clean the shared desk.",
        memory_type="episodic",
        importance=0.8,
    )


def test_phase14_prompt_language_aliases_are_normalized() -> None:
    assert SUPPORTED_PROMPT_LANGUAGES == ("en", "ko", "ja", "zh")
    assert normalize_prompt_language("ko-KR") == "ko"
    assert normalize_prompt_language("ja_jp") == "ja"
    assert normalize_prompt_language("zh-Hans") == "zh"

    with pytest.raises(ValueError, match="unsupported prompt language"):
        normalize_prompt_language("fr")


def test_phase14_persona_system_prompt_templates_cover_four_languages() -> None:
    persona = _persona()
    prompts = {
        language: render_persona_system_prompt(persona, language)
        for language in SUPPORTED_PROMPT_LANGUAGES
    }

    assert "You are roleplaying as Alice." in prompts["en"]
    assert "당신은 Alice 역할을 일관되게 연기합니다." in prompts["ko"]
    assert prompts["ja"].splitlines()[0] != prompts["en"].splitlines()[0]
    assert prompts["zh"].splitlines()[0] != prompts["en"].splitlines()[0]
    assert all("Persona ID: alice" in prompt for prompt in prompts.values())
    assert all("honesty" in prompt for prompt in prompts.values())


def test_phase14_decision_prompt_templates_keep_json_schema_stable() -> None:
    trigger = WorldEvent(
        timestamp=datetime(2026, 4, 18, 9, 0),
        event_type="request",
        participants=["alice", "bob"],
        location="Korea > Seoul > Dormitory",
        description="Bob asks to borrow a notebook.",
    )

    messages = build_decision_messages(
        persona=_persona(),
        memories=[_memory()],
        relationships={"bob": Relationship(source="alice", target="bob", weight=0.5, trust=0.7)},
        environment=_environment(),
        emotion=Emotion(valence=0.2, arousal=0.4, dominance=0.5),
        trigger=trigger,
        language="ko",
    )

    assert "엄격한 JSON" in messages[1]["content"]
    assert '{"action_type": str, "target": str | null, "content": str}' in messages[1]["content"]
    assert "Bob helped Alice" in messages[1]["content"]
    assert "Bob asks to borrow a notebook" in messages[1]["content"]


def test_phase14_decision_engine_passes_language_to_prompt_builder() -> None:
    seen_messages: list[Sequence[Message]] = []

    def responder(messages: Sequence[Message]) -> str:
        seen_messages.append(messages)
        return '{"action_type": "speak", "target": "bob", "content": "醫뗭븘."}'

    engine = DecisionEngine(LocalClient(responder), language="ko")

    action = engine.decide(
        persona=_persona(),
        memories=[_memory()],
        relationships={"bob": Relationship(source="alice", target="bob", weight=0.5, trust=0.7)},
        environment=_environment(),
        emotion=Emotion(valence=0.2, arousal=0.4, dominance=0.5),
    )

    assert action.content == "醫뗭븘."
    assert "당신은 Alice 역할을 일관되게 연기합니다." in seen_messages[0][0]["content"]
    assert "다음 행동" in seen_messages[0][1]["content"]


def test_phase14_persona_prompt_emits_dark_tetrad_section_only_when_non_neutral() -> None:
    baseline_prompt = render_persona_system_prompt(_persona(), "en")
    assert "Tier C - Dark Tetrad" not in baseline_prompt

    intensified = Persona(
        agent_id="alice",
        name="Alice",
        age=17,
        background="Dormitory student who keeps careful notes.",
        personality=Personality(
            0.7,
            0.6,
            0.3,
            0.8,
            0.4,
            machiavellianism=1.0,
            sadism=1.0,
        ),
        values=["honesty"],
        goals=["keep peace with roommate"],
    )
    intensified_prompt = render_persona_system_prompt(intensified, "en")

    assert "Tier C - Dark Tetrad" in intensified_prompt
    assert "Machiavellianism: 1.00" in intensified_prompt
    assert "Sadism: 1.00" in intensified_prompt
