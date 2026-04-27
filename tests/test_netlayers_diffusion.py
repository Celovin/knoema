"""Tests for luvoire.netlayers.diffusion — DeGroot-style propagation."""

from __future__ import annotations

import pytest

from luvoire.netlayers.diffusion import DeGrootPropagator
from luvoire.netlayers.multilayer import MultilayerRelationshipGraph


def _ring_graph() -> MultilayerRelationshipGraph:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("alice", "bob", "family", 1.0)
    graph.add_edge("bob", "carol", "coworker", 1.0)
    graph.add_edge("carol", "alice", "online", 1.0)
    return graph


def test_propagate_returns_trajectory_with_requested_length() -> None:
    propagator = DeGrootPropagator(_ring_graph(), seed=20260427)
    trajectory = propagator.propagate(
        {"alice": 1.0, "bob": 0.0, "carol": 0.5},
        steps=5,
    )
    assert len(trajectory) == 5
    for snapshot in trajectory:
        assert set(snapshot) == {"alice", "bob", "carol"}


def test_propagate_zero_steps_is_empty() -> None:
    propagator = DeGrootPropagator(_ring_graph(), seed=1)
    assert propagator.propagate({"alice": 1.0, "bob": 0.0, "carol": 0.5}, steps=0) == ()


def test_propagate_negative_steps_raises() -> None:
    propagator = DeGrootPropagator(_ring_graph(), seed=1)
    with pytest.raises(ValueError):
        propagator.propagate({"alice": 1.0}, steps=-1)


def test_same_seed_produces_same_trajectory() -> None:
    initial = {"alice": 1.0, "bob": 0.0, "carol": 0.5}
    propagator_a = DeGrootPropagator(_ring_graph(), seed=42)
    propagator_b = DeGrootPropagator(_ring_graph(), seed=42)
    trajectory_a = propagator_a.propagate(initial, steps=4)
    trajectory_b = propagator_b.propagate(initial, steps=4)
    assert trajectory_a == trajectory_b


def test_different_seed_produces_different_trajectory() -> None:
    initial = {"alice": 1.0, "bob": 0.0, "carol": 0.5}
    trajectory_a = DeGrootPropagator(_ring_graph(), seed=1).propagate(initial, steps=4)
    trajectory_b = DeGrootPropagator(_ring_graph(), seed=2).propagate(initial, steps=4)
    assert trajectory_a != trajectory_b


def test_layer_weights_must_sum_positive() -> None:
    with pytest.raises(ValueError):
        DeGrootPropagator(
            _ring_graph(),
            layer_weights={
                "family": 0.0,
                "coworker": 0.0,
                "classmate": 0.0,
                "neighbor": 0.0,
                "online": 0.0,
            },
            seed=0,
        )


def test_layer_weights_reject_negative() -> None:
    with pytest.raises(ValueError):
        DeGrootPropagator(
            _ring_graph(),
            layer_weights={"family": -0.5},
            seed=0,
        )


def test_isolated_node_keeps_its_opinion_modulo_jitter() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_node("loner")
    propagator = DeGrootPropagator(graph, seed=7)
    trajectory = propagator.propagate({"loner": 0.7}, steps=3)
    for snapshot in trajectory:
        assert snapshot["loner"] == pytest.approx(0.7, abs=5e-3)


def test_layer_weights_normalised() -> None:
    propagator = DeGrootPropagator(
        _ring_graph(),
        layer_weights={"family": 2.0, "coworker": 2.0},
        seed=0,
    )
    weights = propagator.layer_weights
    assert weights["family"] == pytest.approx(0.5)
    assert weights["coworker"] == pytest.approx(0.5)
    assert weights["online"] == pytest.approx(0.0)


def test_optional_ndlib_dependency_marker() -> None:
    pytest.importorskip("NDlib")
