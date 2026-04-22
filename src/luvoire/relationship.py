"""Relationship graph model for social agents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import networkx as nx

from luvoire.types import Action, AgentID, RelationshipType

InteractionOutcome = Literal["positive", "neutral", "negative"]


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(slots=True)
class Relationship:
    source: AgentID
    target: AgentID
    relationship_type: RelationshipType = "stranger"
    weight: float = 0.0
    trust: float = 0.5
    familiarity: float = 0.0

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be blank")
        if not self.target.strip():
            raise ValueError("target must not be blank")
        self.weight = _clamp_unit(self.weight)
        self.trust = _clamp_unit(self.trust)
        self.familiarity = _clamp_unit(self.familiarity)


class RelationshipGraph:
    """Directed social relationship graph with typed, weighted edges."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph[AgentID] = nx.DiGraph()

    def add_agent(self, agent_id: AgentID) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id must not be blank")
        self._graph.add_node(agent_id)

    def set_relationship(self, relationship: Relationship) -> None:
        self.add_agent(relationship.source)
        self.add_agent(relationship.target)
        self._graph.add_edge(
            relationship.source,
            relationship.target,
            relationship_type=relationship.relationship_type,
            weight=relationship.weight,
            trust=relationship.trust,
            familiarity=relationship.familiarity,
        )

    def get_relationship(self, source: AgentID, target: AgentID) -> Relationship:
        if not self._graph.has_edge(source, target):
            return Relationship(source=source, target=target)
        data = self._graph[source][target]
        return Relationship(
            source=source,
            target=target,
            relationship_type=data["relationship_type"],
            weight=float(data["weight"]),
            trust=float(data["trust"]),
            familiarity=float(data["familiarity"]),
        )

    def neighbors(self, agent_id: AgentID) -> dict[AgentID, Relationship]:
        return {
            target: self.get_relationship(agent_id, target)
            for target in self._graph.successors(agent_id)
        }

    def update_after_interaction(
        self,
        agent_a: AgentID,
        agent_b: AgentID,
        action: Action,
        outcome: InteractionOutcome | float,
    ) -> Relationship:
        relationship = self.get_relationship(agent_a, agent_b)
        delta = self._outcome_delta(outcome)
        familiarity = _clamp_unit(relationship.familiarity + 0.08)
        trust = _clamp_unit(relationship.trust + (delta * 0.6))
        weight = _clamp_unit(relationship.weight + delta + 0.02)
        relationship_type = self._infer_type(weight, trust, relationship.relationship_type)
        updated = Relationship(
            source=agent_a,
            target=agent_b,
            relationship_type=relationship_type,
            weight=weight,
            trust=trust,
            familiarity=familiarity,
        )
        self.set_relationship(updated)
        if action.target == agent_b:
            reverse = self.get_relationship(agent_b, agent_a)
            self.set_relationship(
                Relationship(
                    source=agent_b,
                    target=agent_a,
                    relationship_type=self._infer_type(
                        _clamp_unit(reverse.weight + delta * 0.5),
                        _clamp_unit(reverse.trust + delta * 0.3),
                        reverse.relationship_type,
                    ),
                    weight=_clamp_unit(reverse.weight + delta * 0.5 + 0.01),
                    trust=_clamp_unit(reverse.trust + delta * 0.3),
                    familiarity=_clamp_unit(reverse.familiarity + 0.04),
                )
            )
        return updated

    def to_networkx(self) -> nx.DiGraph[AgentID]:
        return self._graph.copy()

    def __len__(self) -> int:
        return self._graph.number_of_nodes()

    @staticmethod
    def _outcome_delta(outcome: InteractionOutcome | float) -> float:
        if isinstance(outcome, float | int):
            return max(-0.25, min(0.25, float(outcome)))
        mapping: dict[InteractionOutcome, float] = {
            "positive": 0.12,
            "neutral": 0.0,
            "negative": -0.16,
        }
        return mapping[outcome]

    @staticmethod
    def _infer_type(
        weight: float,
        trust: float,
        current: RelationshipType,
    ) -> RelationshipType:
        if current in {"family", "romantic", "colleague"}:
            return current
        if trust < 0.25 and weight < 0.35:
            return "enemy"
        if trust >= 0.65 and weight >= 0.45:
            return "friend"
        return "stranger"


__all__ = ["InteractionOutcome", "Relationship", "RelationshipGraph"]
