"""DeGroot opinion diffusion on a multi-layer relationship graph.

Each step computes, for every node, a layer-weighted neighbour
weight-mean of the previous opinions and adds a deterministic,
seed-controlled jitter term so we exercise stochastic code paths
without giving up reproducibility. Pure numpy + stdlib; NDlib stays
optional and is only consulted by tests that opt in via
``pytest.importorskip``.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from luvoire.netlayers.multilayer import (
    LAYER_NAMES,
    MultilayerRelationshipGraph,
    RelationshipLayer,
)

_JITTER_SCALE = 1e-3


def _normalise_layer_weights(
    layer_weights: Mapping[RelationshipLayer, float] | None,
) -> dict[RelationshipLayer, float]:
    if layer_weights is None:
        equal = 1.0 / float(len(LAYER_NAMES))
        return dict.fromkeys(LAYER_NAMES, equal)
    out: dict[RelationshipLayer, float] = {}
    total = 0.0
    for layer in LAYER_NAMES:
        value = float(layer_weights.get(layer, 0.0))
        if value < 0.0:
            raise ValueError(f"layer weight for {layer!r} must be non-negative (got {value!r})")
        out[layer] = value
        total += value
    if total <= 0.0:
        raise ValueError("layer_weights must sum to a positive value")
    return {layer: out[layer] / total for layer in LAYER_NAMES}


class DeGrootPropagator:
    """Layer-weighted DeGroot opinion update on a multi-layer graph."""

    def __init__(
        self,
        graph: MultilayerRelationshipGraph,
        *,
        layer_weights: Mapping[RelationshipLayer, float] | None = None,
        seed: int,
    ) -> None:
        self._graph = graph
        self._layer_weights = _normalise_layer_weights(layer_weights)
        self._seed = int(seed)
        self._rng = np.random.default_rng(self._seed)

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def layer_weights(self) -> dict[RelationshipLayer, float]:
        return dict(self._layer_weights)

    def step(self, state: Mapping[str, float]) -> dict[str, float]:
        """Compute a single DeGroot update."""

        nodes = sorted(state)
        next_state: dict[str, float] = {}
        for node in nodes:
            current = float(state[node])
            mixed = self._mix_neighbours(node, state)
            updated = current if mixed is None else mixed
            jitter = float(self._rng.normal(loc=0.0, scale=_JITTER_SCALE))
            next_state[node] = updated + jitter
        return next_state

    def propagate(
        self,
        initial: Mapping[str, float],
        steps: int,
    ) -> tuple[dict[str, float], ...]:
        """Run ``steps`` DeGroot updates, returning the trajectory."""

        if steps < 0:
            raise ValueError(f"steps must be non-negative (got {steps!r})")
        if steps == 0:
            return ()
        trajectory: list[dict[str, float]] = []
        current: dict[str, float] = {key: float(value) for key, value in initial.items()}
        for _ in range(steps):
            current = self.step(current)
            trajectory.append(current)
        return tuple(trajectory)

    def _mix_neighbours(
        self,
        node: str,
        state: Mapping[str, float],
    ) -> float | None:
        weighted_sum = 0.0
        weight_total = 0.0
        for layer in LAYER_NAMES:
            layer_weight = self._layer_weights[layer]
            if layer_weight <= 0.0:
                continue
            for neighbour in self._graph.neighbors(node, layer):
                if neighbour not in state:
                    continue
                edge_weight = self._graph.weight(node, neighbour, layer)
                if edge_weight is None or edge_weight <= 0.0:
                    continue
                contribution = layer_weight * float(edge_weight)
                weighted_sum += contribution * float(state[neighbour])
                weight_total += contribution
        if weight_total <= 0.0:
            return None
        return weighted_sum / weight_total
