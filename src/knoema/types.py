"""Core domain types shared across the Knoema runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

AgentID = str
MemoryType = Literal["episodic", "semantic", "procedural"]
RelationshipType = Literal[
    "family",
    "friend",
    "enemy",
    "stranger",
    "romantic",
    "colleague",
]


def _validate_closed_interval(name: str, value: float, *, minimum: float, maximum: float) -> None:
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}, got {value!r}")


def _validate_non_empty_string(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be blank")


def _validate_agent_id(name: str, value: AgentID | None) -> None:
    if value is None:
        return
    _validate_non_empty_string(name, value)


def _validate_embedding(values: list[float] | None) -> None:
    if values is None:
        return
    if not values:
        raise ValueError("embedding must not be empty when provided")


@dataclass(slots=True)
class Personality:
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

    def __post_init__(self) -> None:
        _validate_closed_interval("openness", self.openness, minimum=0.0, maximum=1.0)
        _validate_closed_interval(
            "conscientiousness",
            self.conscientiousness,
            minimum=0.0,
            maximum=1.0,
        )
        _validate_closed_interval("extraversion", self.extraversion, minimum=0.0, maximum=1.0)
        _validate_closed_interval("agreeableness", self.agreeableness, minimum=0.0, maximum=1.0)
        _validate_closed_interval("neuroticism", self.neuroticism, minimum=0.0, maximum=1.0)


@dataclass(slots=True)
class Emotion:
    valence: float
    arousal: float
    dominance: float

    def __post_init__(self) -> None:
        _validate_closed_interval("valence", self.valence, minimum=-1.0, maximum=1.0)
        _validate_closed_interval("arousal", self.arousal, minimum=0.0, maximum=1.0)
        _validate_closed_interval("dominance", self.dominance, minimum=0.0, maximum=1.0)


@dataclass(slots=True)
class Memory:
    id: str
    agent_id: AgentID
    timestamp: datetime
    content: str
    memory_type: MemoryType
    importance: float
    embedding: list[float] | None = None

    def __post_init__(self) -> None:
        _validate_non_empty_string("id", self.id)
        _validate_agent_id("agent_id", self.agent_id)
        _validate_non_empty_string("content", self.content)
        _validate_closed_interval("importance", self.importance, minimum=0.0, maximum=1.0)
        _validate_embedding(self.embedding)


@dataclass(slots=True)
class Action:
    agent_id: AgentID
    timestamp: datetime
    action_type: str
    target: AgentID | None
    content: str
    location: str

    def __post_init__(self) -> None:
        _validate_agent_id("agent_id", self.agent_id)
        _validate_agent_id("target", self.target)
        _validate_non_empty_string("action_type", self.action_type)
        _validate_non_empty_string("content", self.content)
        _validate_non_empty_string("location", self.location)


@dataclass(slots=True)
class WorldEvent:
    timestamp: datetime
    event_type: str
    participants: list[AgentID]
    location: str
    description: str

    def __post_init__(self) -> None:
        _validate_non_empty_string("event_type", self.event_type)
        _validate_non_empty_string("location", self.location)
        _validate_non_empty_string("description", self.description)
        for index, participant in enumerate(self.participants):
            _validate_agent_id(f"participants[{index}]", participant)


__all__ = [
    "Action",
    "AgentID",
    "Emotion",
    "Memory",
    "MemoryType",
    "Personality",
    "RelationshipType",
    "WorldEvent",
]
