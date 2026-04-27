"""Stdlib-only multi-layer relationship graph.

A :class:`MultilayerRelationshipGraph` keeps one directed adjacency
dictionary per relationship layer (family / coworker / classmate /
neighbor / online). It is the data structure that
:mod:`luvoire.netlayers.diffusion` and :mod:`luvoire.netlayers.contagion`
operate on. The :meth:`flatten` method collapses the layers into the
legacy single-layer :class:`luvoire.relationship.RelationshipGraph`
so callers outside the subpackage keep working unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from luvoire.relationship import RelationshipGraph

RelationshipLayer = Literal["family", "coworker", "classmate", "neighbor", "online"]

LAYER_NAMES: tuple[RelationshipLayer, ...] = (
    "family",
    "coworker",
    "classmate",
    "neighbor",
    "online",
)


def _validate_layer(layer: str) -> RelationshipLayer:
    for name in LAYER_NAMES:
        if layer == name:
            return name
    raise ValueError(f"layer must be one of {LAYER_NAMES} (got {layer!r})")


def _validate_node(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be blank")


@dataclass(frozen=True, slots=True)
class MultilayerEdge:
    """A single directed edge inside one relationship layer."""

    source: str
    target: str
    layer: RelationshipLayer
    weight: float

    def __post_init__(self) -> None:
        _validate_node("source", self.source)
        _validate_node("target", self.target)
        _validate_layer(self.layer)
        if self.weight < 0.0:
            raise ValueError(f"weight must be non-negative (got {self.weight!r})")


class MultilayerRelationshipGraph:
    """Directed multi-layer relationship graph keyed by layer name.

    Each layer is a dict ``source -> target -> weight``. Adjacency is
    stored per-layer so deterministic neighbour iteration is cheap and
    the layers are independently editable.
    """

    def __init__(self) -> None:
        self._layers: dict[RelationshipLayer, dict[str, dict[str, float]]] = {
            layer: {} for layer in LAYER_NAMES
        }
        self._nodes: set[str] = set()

    @property
    def layers(self) -> tuple[RelationshipLayer, ...]:
        return LAYER_NAMES

    def add_node(self, node: str) -> None:
        _validate_node("node", node)
        self._nodes.add(node)

    def nodes(self) -> tuple[str, ...]:
        return tuple(sorted(self._nodes))

    def add_edge(
        self,
        source: str,
        target: str,
        layer: RelationshipLayer,
        weight: float = 1.0,
    ) -> None:
        """Insert (or replace) a directed edge in the requested layer."""

        edge = MultilayerEdge(source=source, target=target, layer=layer, weight=weight)
        adjacency = self._layers[edge.layer]
        bucket = adjacency.setdefault(edge.source, {})
        bucket[edge.target] = float(edge.weight)
        self._nodes.add(edge.source)
        self._nodes.add(edge.target)

    def remove_edge(
        self,
        source: str,
        target: str,
        layer: RelationshipLayer,
    ) -> bool:
        """Remove an edge if present. Returns ``True`` iff something was removed."""

        layer_key = _validate_layer(layer)
        bucket = self._layers[layer_key].get(source)
        if bucket is None or target not in bucket:
            return False
        del bucket[target]
        if not bucket:
            del self._layers[layer_key][source]
        return True

    def has_edge(
        self,
        source: str,
        target: str,
        layer: RelationshipLayer,
    ) -> bool:
        layer_key = _validate_layer(layer)
        bucket = self._layers[layer_key].get(source)
        return bucket is not None and target in bucket

    def neighbors(
        self,
        node: str,
        layer: RelationshipLayer,
    ) -> tuple[str, ...]:
        """Return the deterministic, sorted out-neighbours of ``node`` in ``layer``."""

        layer_key = _validate_layer(layer)
        bucket = self._layers[layer_key].get(node)
        if bucket is None:
            return ()
        return tuple(sorted(bucket))

    def weight(
        self,
        source: str,
        target: str,
        layer: RelationshipLayer,
    ) -> float | None:
        """Return the edge weight or ``None`` if the edge is missing."""

        layer_key = _validate_layer(layer)
        bucket = self._layers[layer_key].get(source)
        if bucket is None:
            return None
        if target not in bucket:
            return None
        return float(bucket[target])

    def layer_edges(self, layer: RelationshipLayer) -> tuple[MultilayerEdge, ...]:
        layer_key = _validate_layer(layer)
        edges: list[MultilayerEdge] = []
        for source in sorted(self._layers[layer_key]):
            bucket = self._layers[layer_key][source]
            for target in sorted(bucket):
                edges.append(
                    MultilayerEdge(
                        source=source,
                        target=target,
                        layer=layer_key,
                        weight=float(bucket[target]),
                    )
                )
        return tuple(edges)

    def layer_density(self, layer: RelationshipLayer) -> float:
        """Directed density for the given layer.

        Density is ``edges / (n * (n - 1))`` over the union of nodes seen
        by the graph. Returns ``0.0`` when fewer than two nodes exist.
        """

        layer_key = _validate_layer(layer)
        node_count = len(self._nodes)
        if node_count < 2:
            return 0.0
        edge_count = sum(len(bucket) for bucket in self._layers[layer_key].values())
        return float(edge_count) / float(node_count * (node_count - 1))

    def aggregate_weight(self, source: str, target: str) -> float:
        """Sum of edge weights from ``source`` to ``target`` across layers."""

        total = 0.0
        for layer_key in LAYER_NAMES:
            bucket = self._layers[layer_key].get(source)
            if bucket is None:
                continue
            value = bucket.get(target)
            if value is None:
                continue
            total += float(value)
        return total

    def flatten(self) -> RelationshipGraph:
        """Collapse the multi-layer graph into a single-layer ``RelationshipGraph``.

        Edge weights are summed across layers and clamped into the
        unit interval to satisfy the legacy graph's invariants. The
        first layer that contributes an edge between a given pair
        wins the relationship-type label, with ``family`` taking
        precedence so canon family ties survive the collapse.
        """

        from luvoire.relationship import Relationship, RelationshipGraph

        graph = RelationshipGraph()
        for node in sorted(self._nodes):
            graph.add_agent(node)
        pairs: dict[tuple[str, str], list[tuple[RelationshipLayer, float]]] = {}
        for layer_key in LAYER_NAMES:
            for source, bucket in self._layers[layer_key].items():
                for target, value in bucket.items():
                    pairs.setdefault((source, target), []).append((layer_key, float(value)))
        for (source, target), contributions in sorted(pairs.items()):
            total = sum(value for _, value in contributions)
            relationship_type = _pick_relationship_type(contributions)
            clamped = max(0.0, min(1.0, total))
            graph.set_relationship(
                Relationship(
                    source=source,
                    target=target,
                    relationship_type=relationship_type,
                    weight=clamped,
                )
            )
        return graph

    def to_dict(self) -> dict[str, dict[str, dict[str, float]]]:
        """Deterministic JSON-friendly serialisation of all layers."""

        out: dict[str, dict[str, dict[str, float]]] = {}
        for layer_key in LAYER_NAMES:
            layer_view: dict[str, dict[str, float]] = {}
            adjacency = self._layers[layer_key]
            for source in sorted(adjacency):
                bucket = adjacency[source]
                layer_view[source] = {target: float(bucket[target]) for target in sorted(bucket)}
            out[layer_key] = layer_view
        return out


def _pick_relationship_type(
    contributions: list[tuple[RelationshipLayer, float]],
) -> Literal["family", "colleague", "friend", "stranger"]:
    """Map dominant layer contributions onto legacy relationship-type labels."""

    layers = {layer for layer, _ in contributions}
    if "family" in layers:
        return "family"
    if "coworker" in layers:
        return "colleague"
    if "classmate" in layers or "neighbor" in layers or "online" in layers:
        return "friend"
    return "stranger"
