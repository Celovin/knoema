"""Observational social learning for opt-in agents."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Literal

from luvoire.planning import WorldState
from luvoire.types import Action, AgentID

ObservationOutcome = Literal["success", "failure", "neutral"]


@dataclass(frozen=True, slots=True)
class ObservedBehavior:
    observer_id: AgentID
    target_id: AgentID
    action: Action
    context: WorldState
    outcome: ObservationOutcome
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class LearnedSkill:
    agent_id: AgentID
    source_agent_id: AgentID
    action_type: str
    content_template: str
    observation_count: int
    success_count: int
    motivation_score: float
    last_observed_at: datetime


class SocialLearner:
    """Bandura-style attention, retention, reproduction, and motivation loop."""

    def __init__(self, *, retention_limit: int = 64, imitation_threshold: float = 0.55) -> None:
        if retention_limit < 1:
            raise ValueError("retention_limit must be positive")
        if not 0.0 <= imitation_threshold <= 1.0:
            raise ValueError("imitation_threshold must be between 0.0 and 1.0")
        self.retention_limit = retention_limit
        self.imitation_threshold = imitation_threshold
        self._observations: dict[AgentID, list[ObservedBehavior]] = {}
        self._skills: dict[AgentID, dict[str, LearnedSkill]] = {}

    def observe(
        self,
        observer_id: AgentID,
        target_id: AgentID,
        action: Action,
        outcome: ObservationOutcome,
        *,
        context: WorldState | None = None,
        observed_at: datetime | None = None,
    ) -> ObservedBehavior | None:
        if observer_id == target_id:
            return None
        if outcome not in {"success", "failure", "neutral"}:
            raise ValueError("outcome must be success, failure, or neutral")
        if action.action_type == "wait":
            return None
        behavior = ObservedBehavior(
            observer_id=observer_id,
            target_id=target_id,
            action=action,
            context=context or WorldState(),
            outcome=outcome,
            observed_at=observed_at or action.timestamp,
        )
        retained = self._observations.setdefault(observer_id, [])
        retained.append(behavior)
        del retained[:-self.retention_limit]
        self._update_skill(behavior)
        return behavior

    def consider_imitation(self, agent_id: AgentID, context: WorldState) -> Action | None:
        skills = self.get_skill_library(agent_id)
        if not skills:
            return None
        best = max(skills, key=lambda skill: (skill.motivation_score, skill.success_count))
        if best.motivation_score < self.imitation_threshold:
            return None
        return Action(
            agent_id=agent_id,
            timestamp=_timestamp_for_tick(context.tick),
            action_type=best.action_type,
            target=None,
            content=f"Imitates {best.source_agent_id}: {best.content_template}",
            location="Social learning context",
        )

    def get_skill_library(self, agent_id: AgentID) -> list[LearnedSkill]:
        return sorted(
            self._skills.get(agent_id, {}).values(),
            key=lambda skill: (skill.motivation_score, skill.last_observed_at.isoformat()),
            reverse=True,
        )

    def observations_for(self, agent_id: AgentID) -> tuple[ObservedBehavior, ...]:
        return tuple(self._observations.get(agent_id, ()))

    def _update_skill(self, behavior: ObservedBehavior) -> None:
        agent_skills = self._skills.setdefault(behavior.observer_id, {})
        key = behavior.action.action_type
        existing = agent_skills.get(key)
        success_delta = 1 if behavior.outcome == "success" else 0
        observation_count = 1 if existing is None else existing.observation_count + 1
        success_count = success_delta if existing is None else existing.success_count + success_delta
        attention = min(1.0, 0.35 + observation_count * 0.08)
        motivation = min(1.0, attention + success_count * 0.22)
        learned = LearnedSkill(
            agent_id=behavior.observer_id,
            source_agent_id=behavior.target_id,
            action_type=behavior.action.action_type,
            content_template=behavior.action.content,
            observation_count=observation_count,
            success_count=success_count,
            motivation_score=round(motivation, 3),
            last_observed_at=behavior.observed_at,
        )
        if existing is not None and existing.success_count > success_count:
            learned = replace(learned, success_count=existing.success_count)
        agent_skills[key] = learned


def _timestamp_for_tick(tick: int) -> datetime:
    return datetime(2026, 4, 19, 0, 0) + timedelta(minutes=max(0, tick))
