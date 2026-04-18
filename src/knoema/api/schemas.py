"""Pydantic schemas for the Knoema API server."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from knoema.environment import Environment
from knoema.persona import Persona
from knoema.theory_of_mind import TheoryOfMindProfile
from knoema.types import Memory, Personality, WorldEvent

SimulationStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


class ApiPersonalityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)

    def to_domain(self) -> Personality:
        return Personality(
            openness=self.openness,
            conscientiousness=self.conscientiousness,
            extraversion=self.extraversion,
            agreeableness=self.agreeableness,
            neuroticism=self.neuroticism,
        )


class TheoryOfMindConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    max_modeled_agents: int = Field(default=3, ge=1)
    max_objects: int = Field(default=4, ge=1)

    def to_domain(self) -> TheoryOfMindProfile:
        return TheoryOfMindProfile(
            enabled=self.enabled,
            max_modeled_agents=self.max_modeled_agents,
            max_objects=self.max_objects,
        )


class ApiAgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str
    name: str
    age: int = Field(gt=0)
    background: str
    personality: ApiPersonalityConfig
    values: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    location_path: tuple[str, ...] | None = None
    theory_of_mind: TheoryOfMindConfig = Field(default_factory=TheoryOfMindConfig)
    planning: bool = False

    def to_domain(self) -> Persona:
        return Persona(
            agent_id=self.agent_id,
            name=self.name,
            age=self.age,
            background=self.background,
            personality=self.personality.to_domain(),
            values=list(self.values),
            goals=list(self.goals),
            theory_of_mind=self.theory_of_mind.to_domain(),
            planning=self.planning,
        )


class ApiEnvironmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: datetime
    location_path: tuple[str, ...]
    conditions: dict[str, Any] = Field(default_factory=dict)

    def to_domain(self) -> Environment:
        return Environment(
            start_time=self.start_time,
            location_path=self.location_path,
            conditions=dict(self.conditions),
        )


class ApiEventConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime | None = None
    event_type: str
    participants: list[str] = Field(default_factory=list)
    location: str | None = None
    description: str

    def to_domain(self, *, default_timestamp: datetime, default_location: str) -> WorldEvent:
        return WorldEvent(
            timestamp=self.timestamp or default_timestamp,
            event_type=self.event_type,
            participants=list(self.participants),
            location=self.location or default_location,
            description=self.description,
        )


class ApiRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_days: int = Field(default=1, ge=1)
    tick_duration_minutes: int = Field(default=30, ge=1)
    prompt_language: str = "en"
    stream_delay_seconds: float = Field(default=0.0, ge=0.0, le=1.0)
    export_path: Path | None = None


class CreateSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime: ApiRuntimeConfig = Field(default_factory=ApiRuntimeConfig)
    environment: ApiEnvironmentConfig
    agents: list[ApiAgentConfig] = Field(min_length=1)
    events: list[ApiEventConfig] = Field(default_factory=list)
    local_response: str = '{"action_type": "wait", "target": null, "content": "observes the situation."}'


class SimulationStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    status: SimulationStatus
    agent_count: int
    completed_ticks: int
    total_ticks: int
    scheduled_events: int
    started_at: datetime
    updated_at: datetime
    error: str | None = None


class AgentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str
    name: str
    location: str
    memory_count: int
    theory_of_mind_enabled: bool


class AgentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    agents: list[AgentSummary]


class MemoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    agent_id: str
    timestamp: datetime
    content: str
    memory_type: str
    importance: float

    @classmethod
    def from_domain(cls, memory: Memory) -> MemoryItem:
        return cls(
            id=memory.id,
            agent_id=memory.agent_id,
            timestamp=memory.timestamp,
            content=memory.content,
            memory_type=memory.memory_type,
            importance=memory.importance,
        )


class MemoryListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    agent_id: str
    memories: list[MemoryItem]


class InjectedEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    accepted: bool
    scheduled_events: int
    event: ApiEventConfig


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    total_simulations: int
    active_simulations: int


__all__ = [
    "AgentListResponse",
    "AgentSummary",
    "ApiAgentConfig",
    "ApiEnvironmentConfig",
    "ApiEventConfig",
    "ApiPersonalityConfig",
    "ApiRuntimeConfig",
    "CreateSimulationRequest",
    "HealthResponse",
    "InjectedEventResponse",
    "MemoryItem",
    "MemoryListResponse",
    "SimulationStatus",
    "SimulationStatusResponse",
    "TheoryOfMindConfig",
]
