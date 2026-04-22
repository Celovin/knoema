"""Phase 4 tests for LLM gateway and decision engine."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import pytest

from luvoire import (
    DecisionEngine,
    EnvironmentContext,
    LLMGateway,
    LocalClient,
    Memory,
    Persona,
    Personality,
    Relationship,
)
from luvoire.decision import build_decision_messages, parse_action_response
from luvoire.protocols import Message
from luvoire.types import Emotion, WorldEvent


class StaticClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        self.calls += 1
        return self.response


class FailingClient:
    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        raise RuntimeError("provider unavailable")


def _persona() -> Persona:
    return Persona(
        agent_id="alice",
        name="Alice",
        age=17,
        background="Dormitory student",
        personality=Personality(0.7, 0.6, 0.3, 0.8, 0.4),
        values=["honesty"],
        goals=["keep peace with roommate"],
    )


def _environment() -> EnvironmentContext:
    return EnvironmentContext(
        agent_id="alice",
        timestamp=datetime(2026, 4, 18, 9, 0),
        location_path=("Korea", "Seoul", "Dormitory", "Room 201"),
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


def test_gateway_returns_first_successful_provider() -> None:
    first = StaticClient("first response")
    second = StaticClient("second response")
    gateway = LLMGateway([("first", first), ("second", second)])

    response = gateway.complete([{"role": "user", "content": "hello"}])

    assert response == "first response"
    assert first.calls == 1
    assert second.calls == 0


def test_gateway_falls_back_after_provider_failure() -> None:
    backup = StaticClient("backup response")
    gateway = LLMGateway([("primary", FailingClient()), ("backup", backup)])

    response = gateway.complete([{"role": "user", "content": "hello"}])

    assert response == "backup response"
    assert [record.success for record in gateway.records] == [False, True]


def test_gateway_raises_when_all_providers_fail() -> None:
    gateway = LLMGateway([("primary", FailingClient())])

    with pytest.raises(RuntimeError, match="all LLM providers failed"):
        gateway.complete([{"role": "user", "content": "hello"}])


def test_gateway_records_estimated_usage_cost() -> None:
    gateway = LLMGateway([("local", StaticClient("hello world"))])

    gateway.complete([{"role": "user", "content": "x" * 100}])

    assert gateway.records[0].prompt_tokens > 0
    assert gateway.records[0].completion_tokens > 0
    assert gateway.records[0].estimated_cost_usd > 0.0


def test_local_client_uses_custom_responder() -> None:
    client = LocalClient(lambda messages: f"seen {len(messages)}")

    assert client.complete([{"role": "user", "content": "hello"}]) == "seen 1"


def test_local_client_default_echoes_last_user_content() -> None:
    client = LocalClient()

    assert client.complete([{"role": "user", "content": "final prompt"}]) == "final prompt"


def test_build_decision_messages_include_context() -> None:
    messages = build_decision_messages(
        persona=_persona(),
        memories=[_memory()],
        relationships={"bob": Relationship(source="alice", target="bob", weight=0.5, trust=0.7)},
        environment=_environment(),
        emotion=Emotion(valence=0.2, arousal=0.4, dominance=0.5),
        trigger=WorldEvent(
            timestamp=datetime(2026, 4, 18, 9, 0),
            event_type="request",
            participants=["alice", "bob"],
            location="Korea > Seoul > Dormitory > Room 201",
            description="Bob asks to borrow a notebook.",
        ),
    )

    assert messages[0]["role"] == "system"
    assert "Bob helped Alice" in messages[1]["content"]
    assert "Bob asks to borrow a notebook" in messages[1]["content"]


def test_parse_action_response_accepts_strict_json() -> None:
    action = parse_action_response(
        '{"action_type": "speak", "target": "bob", "content": "Sure."}',
        agent_id="alice",
        timestamp=datetime(2026, 4, 18, 9, 0),
        location="Dorm",
    )

    assert action.action_type == "speak"
    assert action.target == "bob"
    assert action.content == "Sure."


def test_parse_action_response_falls_back_to_raw_text() -> None:
    action = parse_action_response(
        "I need a moment to think.",
        agent_id="alice",
        timestamp=datetime(2026, 4, 18, 9, 0),
        location="Dorm",
    )

    assert action.action_type == "speak"
    assert action.content == "I need a moment to think."


def test_decision_engine_returns_action_from_mock_llm() -> None:
    llm = StaticClient('{"action_type": "speak", "target": "bob", "content": "Thanks for asking."}')
    engine = DecisionEngine(llm)

    action = engine.decide(
        persona=_persona(),
        memories=[_memory()],
        relationships={"bob": Relationship(source="alice", target="bob", weight=0.5, trust=0.7)},
        environment=_environment(),
        emotion=Emotion(valence=0.2, arousal=0.4, dominance=0.5),
    )

    assert action.agent_id == "alice"
    assert action.target == "bob"
    assert action.content == "Thanks for asking."
