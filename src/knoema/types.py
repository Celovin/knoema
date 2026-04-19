"""Core domain types shared across the Knoema runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

AgentID = str
MemoryType = Literal["episodic", "semantic", "procedural"]
ActionType = Literal[
    "speak",
    "observe",
    "move",
    "give",
    "take",
    "threaten",
    "deceive",
    "comfort",
    "query_memory",
    "propose_plan",
    "exit",
    "enter",
    "attack",
    "defend",
    "offer",
    "accept",
    "refuse",
    "gossip",
    "persuade",
    "alone",
]
ACTION_TYPES: tuple[str, ...] = (
    "speak",
    "observe",
    "move",
    "give",
    "take",
    "threaten",
    "deceive",
    "comfort",
    "query_memory",
    "propose_plan",
    "exit",
    "enter",
    "attack",
    "defend",
    "offer",
    "accept",
    "refuse",
    "gossip",
    "persuade",
    "alone",
)
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


PERSONALITY_NEUTRAL_DEFAULTS: dict[str, float] = {
    "openness": 0.5,
    "conscientiousness": 0.5,
    "extraversion": 0.5,
    "agreeableness": 0.5,
    "neuroticism": 0.5,
    "honesty_humility": 0.5,
    "machiavellianism": 0.0,
    "narcissism": 0.0,
    "psychopathy": 0.0,
    "sadism": 0.0,
    "kantianism": 0.5,
    "humanism": 0.5,
    "faith_in_humanity": 0.5,
    "risk_tolerance": 0.5,
    "locus_of_control": 0.5,
    "need_for_cognition": 0.5,
    "trait_empathy": 0.5,
    "care_harm": 0.5,
    "fairness": 0.5,
    "binding_morals": 0.5,
    "self_direction": 0.5,
    "stimulation": 0.5,
    "hedonism": 0.5,
    "achievement": 0.5,
    "power": 0.5,
    "security": 0.5,
    "conformity": 0.5,
    "tradition": 0.5,
    "benevolence": 0.5,
    "universalism": 0.5,
}
PERSONALITY_FIELDS: tuple[str, ...] = tuple(PERSONALITY_NEUTRAL_DEFAULTS)
BIG_FIVE_FIELDS: tuple[str, ...] = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)


@dataclass(slots=True)
class Personality:
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    honesty_humility: float = 0.5
    machiavellianism: float = 0.0
    narcissism: float = 0.0
    psychopathy: float = 0.0
    sadism: float = 0.0
    kantianism: float = 0.5
    humanism: float = 0.5
    faith_in_humanity: float = 0.5
    risk_tolerance: float = 0.5
    locus_of_control: float = 0.5
    need_for_cognition: float = 0.5
    trait_empathy: float = 0.5
    care_harm: float = 0.5
    fairness: float = 0.5
    binding_morals: float = 0.5
    self_direction: float = 0.5
    stimulation: float = 0.5
    hedonism: float = 0.5
    achievement: float = 0.5
    power: float = 0.5
    security: float = 0.5
    conformity: float = 0.5
    tradition: float = 0.5
    benevolence: float = 0.5
    universalism: float = 0.5

    def __post_init__(self) -> None:
        for field_name in PERSONALITY_FIELDS:
            _validate_closed_interval(
                field_name,
                float(getattr(self, field_name)),
                minimum=0.0,
                maximum=1.0,
            )

    def to_dict(self) -> dict[str, float]:
        return {field_name: float(getattr(self, field_name)) for field_name in PERSONALITY_FIELDS}

    @classmethod
    def from_dict(cls, payload: Mapping[str, float]) -> Personality:
        values: dict[str, float] = {}
        for field_name, default in PERSONALITY_NEUTRAL_DEFAULTS.items():
            if field_name in BIG_FIVE_FIELDS:
                values[field_name] = float(payload[field_name])
            else:
                values[field_name] = float(payload.get(field_name, default))
        return cls(**values)


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
    action_type: ActionType | str
    target: AgentID | None
    content: str
    location: str
    metadata: dict[str, Any] = field(default_factory=dict)

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
    "ACTION_TYPES",
    "BIG_FIVE_FIELDS",
    "PERSONALITY_FIELDS",
    "PERSONALITY_NEUTRAL_DEFAULTS",
    "Action",
    "ActionType",
    "AgentID",
    "Emotion",
    "Memory",
    "MemoryType",
    "Personality",
    "RelationshipType",
    "WorldEvent",
]
