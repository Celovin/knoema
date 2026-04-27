"""Tests for luvoire.netlayers.multilayer — stdlib multi-layer graph."""

from __future__ import annotations

import pytest

from luvoire.netlayers.multilayer import (
    LAYER_NAMES,
    MultilayerEdge,
    MultilayerRelationshipGraph,
)
from luvoire.relationship import RelationshipGraph


def test_layer_names_canonical_order() -> None:
    assert LAYER_NAMES == ("family", "coworker", "classmate", "neighbor", "online")


def test_multilayer_edge_validates_inputs() -> None:
    edge = MultilayerEdge(source="a", target="b", layer="family", weight=0.5)
    assert edge.source == "a"
    assert edge.target == "b"
    assert edge.layer == "family"
    assert edge.weight == pytest.approx(0.5)

    with pytest.raises(ValueError):
        MultilayerEdge(source=" ", target="b", layer="family", weight=0.5)
    with pytest.raises(ValueError):
        MultilayerEdge(source="a", target="b", layer="bogus", weight=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        MultilayerEdge(source="a", target="b", layer="family", weight=-0.1)


def test_add_edge_and_weight_lookup() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("alice", "bob", "family", 0.6)
    graph.add_edge("alice", "carol", "coworker", 0.3)
    assert graph.weight("alice", "bob", "family") == pytest.approx(0.6)
    assert graph.weight("alice", "carol", "coworker") == pytest.approx(0.3)
    assert graph.weight("alice", "bob", "coworker") is None
    assert graph.weight("ghost", "bob", "family") is None


def test_neighbors_sorted_for_determinism() -> None:
    graph = MultilayerRelationshipGraph()
    for target in ("zoe", "alice", "marcus", "bob"):
        graph.add_edge("hub", target, "online", 1.0)
    assert graph.neighbors("hub", "online") == ("alice", "bob", "marcus", "zoe")
    assert graph.neighbors("hub", "family") == ()
    assert graph.neighbors("missing", "online") == ()


def test_layer_density_uses_directed_pair_count() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_node("alice")
    graph.add_node("bob")
    graph.add_node("carol")
    graph.add_edge("alice", "bob", "family", 1.0)
    graph.add_edge("bob", "alice", "family", 1.0)
    # 2 edges over 3*2 = 6 directed pairs
    assert graph.layer_density("family") == pytest.approx(2.0 / 6.0)
    assert graph.layer_density("coworker") == pytest.approx(0.0)


def test_layer_density_zero_for_singleton() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_node("solo")
    assert graph.layer_density("family") == 0.0


def test_aggregate_weight_sums_across_layers() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("alice", "bob", "family", 0.4)
    graph.add_edge("alice", "bob", "coworker", 0.3)
    graph.add_edge("alice", "bob", "online", 0.2)
    assert graph.aggregate_weight("alice", "bob") == pytest.approx(0.9)
    assert graph.aggregate_weight("alice", "ghost") == pytest.approx(0.0)


def test_remove_edge_returns_status() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("alice", "bob", "family", 0.5)
    assert graph.has_edge("alice", "bob", "family")
    assert graph.remove_edge("alice", "bob", "family") is True
    assert graph.has_edge("alice", "bob", "family") is False
    assert graph.remove_edge("alice", "bob", "family") is False


def test_to_dict_is_deterministic_and_includes_all_layers() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("b", "a", "family", 1.0)
    graph.add_edge("a", "b", "family", 0.5)
    payload = graph.to_dict()
    assert set(payload) == set(LAYER_NAMES)
    family_sources = list(payload["family"])
    assert family_sources == ["a", "b"]
    assert payload["coworker"] == {}
    assert payload["family"]["a"] == {"b": 0.5}


def test_flatten_round_trip_into_relationship_graph() -> None:
    graph = MultilayerRelationshipGraph()
    graph.add_edge("alice", "bob", "family", 0.6)
    graph.add_edge("alice", "bob", "coworker", 0.3)
    graph.add_edge("carol", "dave", "coworker", 0.5)
    flat = graph.flatten()
    assert isinstance(flat, RelationshipGraph)
    rel_alice = flat.get_relationship("alice", "bob")
    assert rel_alice.relationship_type == "family"
    assert rel_alice.weight == pytest.approx(0.9)
    rel_carol = flat.get_relationship("carol", "dave")
    assert rel_carol.relationship_type == "colleague"
    assert rel_carol.weight == pytest.approx(0.5)


def test_flatten_clamps_weights_to_unit_interval() -> None:
    graph = MultilayerRelationshipGraph()
    for layer in LAYER_NAMES:
        graph.add_edge("alice", "bob", layer, 1.0)
    flat = graph.flatten()
    assert flat.get_relationship("alice", "bob").weight == pytest.approx(1.0)


def test_invalid_layer_name_raises() -> None:
    graph = MultilayerRelationshipGraph()
    with pytest.raises(ValueError):
        graph.add_edge("a", "b", "bogus", 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        graph.layer_density("bogus")  # type: ignore[arg-type]


def test_blank_node_rejected() -> None:
    graph = MultilayerRelationshipGraph()
    with pytest.raises(ValueError):
        graph.add_node("   ")
