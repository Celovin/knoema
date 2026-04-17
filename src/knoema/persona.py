"""Persona model for agent identity and prompting."""

from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent

from knoema.types import AgentID, Personality


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

    def __post_init__(self) -> None:
        _validate_non_empty_string("agent_id", self.agent_id)
        _validate_non_empty_string("name", self.name)
        _validate_non_empty_string("background", self.background)
        if self.age <= 0:
            raise ValueError(f"age must be positive, got {self.age!r}")
        _validate_string_list("values", self.values)
        _validate_string_list("goals", self.goals)

    def to_system_prompt(self, language: str = "en") -> str:
        from knoema.prompts import normalize_prompt_language, render_persona_system_prompt

        if normalize_prompt_language(language) != "en":
            return render_persona_system_prompt(self, language)
        values_text = ", ".join(self.values) if self.values else "None provided"
        goals_text = ", ".join(self.goals) if self.goals else "None provided"
        return dedent(
            f"""
            You are roleplaying as {self.name}.

            Persona ID: {self.agent_id}
            Age: {self.age}
            Background: {self.background}

            Personality traits:
            - Openness: {self.personality.openness:.2f}
            - Conscientiousness: {self.personality.conscientiousness:.2f}
            - Extraversion: {self.personality.extraversion:.2f}
            - Agreeableness: {self.personality.agreeableness:.2f}
            - Neuroticism: {self.personality.neuroticism:.2f}

            Core values: {values_text}
            Active goals: {goals_text}

            Stay consistent with this persona, remember prior social context,
            and respond in a way that preserves believable long-term behavior.
            """
        ).strip()


__all__ = ["Persona"]
