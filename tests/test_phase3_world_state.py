"""Phase 3 tests for relationship, environment, and emotion models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from luvoire import (
    Action,
    EmotionState,
    EmotionStimulus,
    Environment,
    Relationship,
    RelationshipGraph,
)
from luvoire.types import Emotion, WorldEvent


def _action(target: str | None = "bob") -> Action:
    return Action(
        agent_id="alice",
        timestamp=datetime(2026, 4, 18, 9, 0),
        action_type="speak",
        target=target,
        content="Can we share the desk schedule?",
        location="Dorm Room 201",
    )


def test_relationship_graph_stores_ten_agents_for_visualization() -> None:
    graph = RelationshipGraph()
    for index in range(10):
        graph.add_agent(f"agent-{index}")
    graph.set_relationship(
        Relationship(
            source="agent-0",
            target="agent-1",
            relationship_type="colleague",
            weight=0.4,
            trust=0.6,
            familiarity=0.3,
        )
    )

    networkx_graph = graph.to_networkx()

    assert networkx_graph.number_of_nodes() == 10
    assert networkx_graph["agent-0"]["agent-1"]["relationship_type"] == "colleague"


def test_relationship_update_after_positive_interaction_increases_weight_and_trust() -> None:
    graph = RelationshipGraph()
    graph.set_relationship(Relationship(source="alice", target="bob", weight=0.3, trust=0.4))

    updated = graph.update_after_interaction("alice", "bob", _action(), "positive")

    assert updated.weight > 0.3
    assert updated.trust > 0.4
    assert graph.get_relationship("bob", "alice").familiarity > 0.0


def test_relationship_update_after_negative_interaction_can_mark_enemy() -> None:
    graph = RelationshipGraph()
    graph.set_relationship(Relationship(source="alice", target="bob", weight=0.25, trust=0.25))

    updated = graph.update_after_interaction("alice", "bob", _action(), "negative")

    assert updated.relationship_type == "enemy"


def test_environment_returns_agent_specific_context_and_conditions() -> None:
    environment = Environment(
        start_time=datetime(2026, 3, 2, 9, 0),
        location_path=("Korea", "Seoul", "Dormitory"),
        conditions={"weather": "rain", "semester": "spring"},
    )
    environment.set_agent_location("alice", ("Korea", "Seoul", "Dormitory", "Room 201"))
    environment.advance_time(timedelta(minutes=30))

    context = environment.get_context("alice")

    assert context.location == "Korea > Seoul > Dormitory > Room 201"
    assert context.timestamp == datetime(2026, 3, 2, 9, 30)
    assert context.conditions["weather"] == "rain"


def test_environment_event_propagates_to_agent_context() -> None:
    environment = Environment(
        start_time=datetime(2026, 3, 2, 9, 0),
        location_path=("Korea", "Seoul", "Dormitory"),
    )
    event = WorldEvent(
        timestamp=datetime(2026, 3, 2, 9, 15),
        event_type="announcement",
        participants=["alice", "bob"],
        location="Korea > Seoul > Dormitory",
        description="Dorm quiet hours changed.",
    )

    environment.apply_event(event, {"quiet_hours": "22:00"})
    context = environment.get_context("alice")

    assert context.conditions["quiet_hours"] == "22:00"
    assert context.recent_events == [event]


def test_emotion_state_applies_stimulus_and_clamps_bounds() -> None:
    state = EmotionState(Emotion(valence=0.9, arousal=0.95, dominance=0.1))

    emotion = state.apply(EmotionStimulus(valence_delta=0.5, arousal_delta=0.5, dominance_delta=-0.5))

    assert emotion.valence == 1.0
    assert emotion.arousal == 1.0
    assert emotion.dominance == 0.0


def test_emotion_state_decay_moves_toward_neutral() -> None:
    state = EmotionState(Emotion(valence=-0.8, arousal=0.8, dominance=0.9))

    emotion = state.decay(rate=0.25)

    assert emotion.valence == pytest.approx(-0.6)
    assert emotion.arousal == pytest.approx(0.6)
    assert emotion.dominance == pytest.approx(0.8)


def test_emotion_state_rejects_unknown_outcome() -> None:
    state = EmotionState()

    with pytest.raises(ValueError, match="unknown outcome"):
        state.update_after_outcome("confusing")
