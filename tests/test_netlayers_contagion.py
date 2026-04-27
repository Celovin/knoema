"""Tests for luvoire.netlayers.contagion — Bosse-style affective contagion."""

from __future__ import annotations

import pytest

from luvoire.netlayers.contagion import AffectiveContagion
from luvoire.netlayers.multilayer import MultilayerRelationshipGraph


def _triangle_graph() -> MultilayerRelationshipGraph:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("alice", "bob", "family", 1.0)
    graph.add_edge("bob", "carol", "coworker", 1.0)
    graph.add_edge("carol", "alice", "neighbor", 1.0)
    return graph


def test_simulate_returns_requested_step_count() -> None:
    contagion = AffectiveContagion(_triangle_graph(), seed=20260427)
    trajectory = contagion.simulate(
        {"alice": 1.0, "bob": 0.0, "carol": -0.5},
        steps=6,
    )
    assert len(trajectory) == 6
    for snapshot in trajectory:
        assert set(snapshot) == {"alice", "bob", "carol"}


def test_simulate_zero_steps_is_empty() -> None:
    contagion = AffectiveContagion(_triangle_graph(), seed=0)
    assert contagion.simulate({"alice": 1.0}, steps=0) == ()


def test_simulate_negative_steps_raises() -> None:
    contagion = AffectiveContagion(_triangle_graph(), seed=0)
    with pytest.raises(ValueError):
        contagion.simulate({"alice": 1.0}, steps=-2)


def test_decay_and_susceptibility_clamped_to_unit() -> None:
    with pytest.raises(ValueError):
        AffectiveContagion(_triangle_graph(), decay=1.5, seed=0)
    with pytest.raises(ValueError):
        AffectiveContagion(_triangle_graph(), susceptibility=-0.1, seed=0)


def test_same_seed_yields_identical_trajectory() -> None:
    initial = {"alice": 1.0, "bob": 0.0, "carol": -0.5}
    a = AffectiveContagion(_triangle_graph(), seed=99).simulate(initial, steps=5)
    b = AffectiveContagion(_triangle_graph(), seed=99).simulate(initial, steps=5)
    assert a == b


def test_different_seed_yields_different_trajectory() -> None:
    initial = {"alice": 1.0, "bob": 0.0, "carol": -0.5}
    a = AffectiveContagion(_triangle_graph(), seed=1).simulate(initial, steps=5)
    b = AffectiveContagion(_triangle_graph(), seed=2).simulate(initial, steps=5)
    assert a != b


def test_isolated_node_decays_toward_zero() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_node("solo")
    contagion = AffectiveContagion(graph, decay=0.5, susceptibility=0.4, seed=0)
    trajectory = contagion.simulate({"solo": 1.0}, steps=3)
    values = [snapshot["solo"] for snapshot in trajectory]
    # decay 0.5 ^ 1, ^ 2, ^ 3 = 0.5, 0.25, 0.125, plus tiny jitter
    assert values[0] == pytest.approx(0.5, abs=5e-3)
    assert values[1] == pytest.approx(0.25, abs=5e-3)
    assert values[2] == pytest.approx(0.125, abs=5e-3)


def test_neighbour_contribution_applied() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("alice", "bob", "family", 1.0)
    contagion = AffectiveContagion(graph, decay=0.0, susceptibility=1.0, seed=0)
    trajectory = contagion.simulate({"alice": 0.0, "bob": 1.0}, steps=1)
    snapshot = trajectory[0]
    # alice has bob as neighbour with weight 1; decay=0 so result=1*bob=1 +/- jitter
    assert snapshot["alice"] == pytest.approx(1.0, abs=5e-3)
    # bob has no out-neighbour so neighbour mean=0; result=0 +/- jitter
    assert snapshot["bob"] == pytest.approx(0.0, abs=5e-3)


def test_optional_py3plex_dependency_marker() -> None:
    pytest.importorskip("py3plex")
