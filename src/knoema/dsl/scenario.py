"""Pydantic models for Scenario DSL v1."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from knoema.environment import Environment
from knoema.game.schedule import RoutineEntry
from knoema.llm import LocalClient
from knoema.persona import Persona
from knoema.simulator import Simulator
from knoema.types import Personality, WorldEvent

ScenarioDomain = Literal["game", "public_safety_research", "academic_research"]
MetricKind = Literal["count", "ratio", "score", "latency"]


class PersonalitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)
    honesty_humility: float = Field(default=0.5, ge=0.0, le=1.0)
    machiavellianism: float = Field(default=0.0, ge=0.0, le=1.0)
    narcissism: float = Field(default=0.0, ge=0.0, le=1.0)
    psychopathy: float = Field(default=0.0, ge=0.0, le=1.0)
    sadism: float = Field(default=0.0, ge=0.0, le=1.0)
    kantianism: float = Field(default=0.5, ge=0.0, le=1.0)
    humanism: float = Field(default=0.5, ge=0.0, le=1.0)
    faith_in_humanity: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    locus_of_control: float = Field(default=0.5, ge=0.0, le=1.0)
    need_for_cognition: float = Field(default=0.5, ge=0.0, le=1.0)
    trait_empathy: float = Field(default=0.5, ge=0.0, le=1.0)
    care_harm: float = Field(default=0.5, ge=0.0, le=1.0)
    fairness: float = Field(default=0.5, ge=0.0, le=1.0)
    binding_morals: float = Field(default=0.5, ge=0.0, le=1.0)
    self_direction: float = Field(default=0.5, ge=0.0, le=1.0)
    stimulation: float = Field(default=0.5, ge=0.0, le=1.0)
    hedonism: float = Field(default=0.5, ge=0.0, le=1.0)
    achievement: float = Field(default=0.5, ge=0.0, le=1.0)
    power: float = Field(default=0.5, ge=0.0, le=1.0)
    security: float = Field(default=0.5, ge=0.0, le=1.0)
    conformity: float = Field(default=0.5, ge=0.0, le=1.0)
    tradition: float = Field(default=0.5, ge=0.0, le=1.0)
    benevolence: float = Field(default=0.5, ge=0.0, le=1.0)
    universalism: float = Field(default=0.5, ge=0.0, le=1.0)

    def to_domain(self) -> Personality:
        return Personality(**self.model_dump())


class AgentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    age: int = Field(gt=0)
    background: str = Field(min_length=1)
    personality: PersonalitySpec
    values: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    location_path: tuple[str, ...] | None = None
    routine: list[RoutineSpec] = Field(default_factory=list)
    synthetic: bool = True

    def to_domain(self) -> Persona:
        return Persona(
            agent_id=self.agent_id,
            name=self.name,
            age=self.age,
            background=self.background,
            personality=self.personality.to_domain(),
            values=list(self.values),
            goals=list(self.goals),
            routine=[entry.to_domain() for entry in self.routine] or None,
        )


class RoutineSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_hour: int = Field(ge=0, le=24)
    end_hour: int = Field(ge=0, le=24)
    location_path: tuple[str, ...] = Field(min_length=1)
    default_action: str = Field(min_length=1)
    default_target: str | None = None

    def to_domain(self) -> RoutineEntry:
        return RoutineEntry(
            start_hour=self.start_hour,
            end_hour=self.end_hour,
            location_path=self.location_path,
            default_action=self.default_action,
            default_target=self.default_target,
        )


class EnvironmentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_time: datetime
    location_path: tuple[str, ...] = Field(min_length=1)
    conditions: dict[str, str | int | float | bool] = Field(default_factory=dict)

    def to_domain(self) -> Environment:
        return Environment(
            start_time=self.start_time,
            location_path=self.location_path,
            conditions=dict(self.conditions),
        )


class EventSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    event_type: str = Field(min_length=1)
    participants: list[str] = Field(min_length=1)
    location: str = Field(min_length=1)
    description: str = Field(min_length=1)

    def to_domain(self) -> WorldEvent:
        return WorldEvent(
            timestamp=self.timestamp,
            event_type=self.event_type,
            participants=list(self.participants),
            location=self.location,
            description=self.description,
        )


class MetricSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    kind: MetricKind
    description: str = Field(min_length=1)


class EthicsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fictional: bool = True
    no_real_people: bool = True
    no_prediction: bool = True
    no_suspect_scoring: bool = True
    sensitive_domain: bool = False
    irb_notes: str | None = None


AgentSpec.model_rebuild()


class Scenario(BaseModel):
    """Scenario DSL v1 root object."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    scenario_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    domain: ScenarioDomain
    description: str = Field(min_length=1)
    seed: int = Field(ge=0)
    tick_duration_minutes: int = Field(default=60, ge=1)
    duration_days: int = Field(default=1, ge=1)
    environment: EnvironmentSpec
    agents: list[AgentSpec] = Field(min_length=1)
    events: list[EventSpec] = Field(default_factory=list)
    metrics: list[MetricSpec] = Field(default_factory=list)
    ethics: EthicsSpec = Field(default_factory=EthicsSpec)
    local_response: str = (
        '{"action_type": "observe", "target": null, "content": "records the scenario state."}'
    )

    def to_simulator(self) -> Simulator:
        environment = self.environment.to_domain()
        agents = [agent.to_domain() for agent in self.agents]
        for agent in self.agents:
            if agent.location_path is not None:
                environment.set_agent_location(agent.agent_id, agent.location_path)

        simulator = Simulator(
            agents=agents,
            environment=environment,
            tick_duration_minutes=self.tick_duration_minutes,
            llm=LocalClient(lambda messages: self.local_response),
        )
        for event in self.events:
            simulator.scheduler.schedule(event.to_domain())
        return simulator
