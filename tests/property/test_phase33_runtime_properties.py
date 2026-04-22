from __future__ import annotations

from datetime import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from luvoire import Personality, RelationshipGraph, RetrievalWeights
from luvoire.emotion import EmotionState, EmotionStimulus
from luvoire.types import Action, Emotion

_UNIT_FLOATS = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
_PAD_VALENCE = st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False)
_FINITE_DELTAS = st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False)


@given(
    openness=_UNIT_FLOATS,
    conscientiousness=_UNIT_FLOATS,
    extraversion=_UNIT_FLOATS,
    agreeableness=_UNIT_FLOATS,
    neuroticism=_UNIT_FLOATS,
)
@settings(max_examples=25)
def test_phase33_personality_accepts_unit_interval_traits(
    openness: float,
    conscientiousness: float,
    extraversion: float,
    agreeableness: float,
    neuroticism: float,
) -> None:
    personality = Personality(
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism,
    )

    assert personality.openness == openness
    assert personality.conscientiousness == conscientiousness
    assert personality.extraversion == extraversion
    assert personality.agreeableness == agreeableness
    assert personality.neuroticism == neuroticism


@given(
    semantic=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
    temporal=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
    importance=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=25)
def test_phase33_retrieval_weights_normalize_and_keep_scores_bounded(
    semantic: float,
    temporal: float,
    importance: float,
) -> None:
    weights = RetrievalWeights(
        semantic=semantic,
        temporal=temporal,
        importance=importance,
    ).normalized()

    assert weights.semantic + weights.temporal + weights.importance == pytest.approx(1.0)
    assert 0.0 <= weights.score(
        semantic_score=0.25,
        temporal_score=0.5,
        importance_score=0.75,
    ) <= 1.0


@given(
    valence=_PAD_VALENCE,
    arousal=_UNIT_FLOATS,
    dominance=_UNIT_FLOATS,
    valence_delta=_FINITE_DELTAS,
    arousal_delta=_FINITE_DELTAS,
    dominance_delta=_FINITE_DELTAS,
)
@settings(max_examples=25)
def test_phase33_emotion_state_clamps_after_arbitrary_stimuli(
    valence: float,
    arousal: float,
    dominance: float,
    valence_delta: float,
    arousal_delta: float,
    dominance_delta: float,
) -> None:
    state = EmotionState(Emotion(valence=valence, arousal=arousal, dominance=dominance))

    updated = state.apply(
        EmotionStimulus(
            valence_delta=valence_delta,
            arousal_delta=arousal_delta,
            dominance_delta=dominance_delta,
        )
    )

    assert -1.0 <= updated.valence <= 1.0
    assert 0.0 <= updated.arousal <= 1.0
    assert 0.0 <= updated.dominance <= 1.0


@given(outcome=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=25)
def test_phase33_relationship_updates_keep_graph_metrics_bounded(outcome: float) -> None:
    graph = RelationshipGraph()
    action = Action(
        agent_id="alice",
        timestamp=datetime(2026, 4, 18, 9, 0),
        action_type="speak",
        target="bob",
        content="checks in with Bob",
        location="Lab",
    )

    updated = graph.update_after_interaction("alice", "bob", action, outcome)
    reverse = graph.get_relationship("bob", "alice")

    for relationship in [updated, reverse]:
        assert 0.0 <= relationship.weight <= 1.0
        assert 0.0 <= relationship.trust <= 1.0
        assert 0.0 <= relationship.familiarity <= 1.0
