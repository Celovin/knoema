"""Persona model for agent identity and prompting."""

from __future__ import annotations

from dataclasses import dataclass, field

from luvoire.game.inventory import Inventory
from luvoire.game.schedule import RoutineEntry
from luvoire.theory_of_mind import TheoryOfMindProfile
from luvoire.types import AgentID, Personality


def _validate_non_empty_string(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be blank")


def _validate_string_list(name: str, values: list[str]) -> None:
    for index, value in enumerate(values):
        if not value.strip():
            raise ValueError(f"{name}[{index}] must not be blank")


@dataclass(slots=True)
class Persona:
    agent_id: AgentID
    name: str
    age: int
    background: str
    personality: Personality
    values: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    theory_of_mind: TheoryOfMindProfile = field(default_factory=TheoryOfMindProfile)
    inventory: Inventory | None = None
    factions: dict[str, float] | None = None
    routine: list[RoutineEntry] | None = None
    planning: bool = False
    social_learning: bool = False

    def __post_init__(self) -> None:
        _validate_non_empty_string("agent_id", self.agent_id)
        _validate_non_empty_string("name", self.name)
        _validate_non_empty_string("background", self.background)
        if self.age <= 0:
            raise ValueError(f"age must be positive, got {self.age!r}")
        _validate_string_list("values", self.values)
        _validate_string_list("goals", self.goals)
        if self.factions is not None:
            self.factions = {
                str(faction_id): float(score)
                for faction_id, score in self.factions.items()
            }
        if self.routine is not None:
            self.routine = list(self.routine)

    def to_system_prompt(self, language: str = "en") -> str:
        from luvoire.prompts import render_persona_system_prompt

        return render_persona_system_prompt(self, language)


__all__ = ["Persona"]
