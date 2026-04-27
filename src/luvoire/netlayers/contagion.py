"""Bosse-style affective contagion over a multi-layer relationship graph.

Each step blends a node's previous emotion (scaled by ``decay``) with
the layer-aggregated weighted mean of its neighbours' emotions
(scaled by ``susceptibility``). The model is deterministic given a
seed so trajectories can be replayed inside Luvoire's reproducibility
gates.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from luvoire.netlayers.multilayer import LAYER_NAMES, MultilayerRelationshipGraph

_JITTER_SCALE = 1e-4


def _validate_unit_factor(name: str, value: float) -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1] (got {value!r})")
    return float(value)


class AffectiveContagion:
    """Simple Bosse-style affective contagion with layer aggregation."""

    def __init__(
        self,
        graph: MultilayerRelationshipGraph,
        *,
        decay: float = 0.95,
        susceptibility: float = 0.4,
        seed: int,
    ) -> None:
        self._graph = graph
        self._decay = _validate_unit_factor("decay", decay)
        self._susceptibility = _validate_unit_factor("susceptibility", susceptibility)
        self._seed = int(seed)
        self._rng = np.random.default_rng(self._seed)

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def decay(self) -> float:
        return self._decay

    @property
    def susceptibility(self) -> float:
        return self._susceptibility

    def step(self, emotion_state: Mapping[str, float]) -> dict[str, float]:
        """Compute one Bosse-style affective contagion update.

        Convergence behaviour:

        - With ``decay < 1.0`` (the default 0.95) emotions dissipate
          exponentially toward zero in the absence of new neighbour input;
          this is the recommended regime.
        - With ``decay = 1.0`` and ``susceptibility = 1.0`` the update
          reduces to ``own + neighbour_mean`` and the state is unbounded;
          the unit-clamp below keeps the output in ``[0, 1]`` but the
          trajectory effectively saturates rather than converging to a
          dissipation fixed point. Callers should prefer ``decay < 1.0``.

        Output is clamped to ``[0, 1]`` after the additive gaussian jitter.
        """

        next_state: dict[str, float] = {}
        for node in sorted(emotion_state):
            own = float(emotion_state[node])
            neighbour_mean = self._neighbour_mean(node, emotion_state)
            mixed = self._decay * own + self._susceptibility * neighbour_mean
            jitter = float(self._rng.normal(loc=0.0, scale=_JITTER_SCALE))
            next_state[node] = min(1.0, max(0.0, mixed + jitter))
        return next_state

    def simulate(
        self,
        initial: Mapping[str, float],
        steps: int,
    ) -> tuple[dict[str, float], ...]:
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

    def _neighbour_mean(self, node: str, state: Mapping[str, float]) -> float:
        weighted_sum = 0.0
        weight_total = 0.0
        for layer in LAYER_NAMES:
            for neighbour in self._graph.neighbors(node, layer):
                if neighbour not in state:
                    continue
                edge_weight = self._graph.weight(node, neighbour, layer)
                if edge_weight is None or edge_weight <= 0.0:
                    continue
                weighted_sum += float(edge_weight) * float(state[neighbour])
                weight_total += float(edge_weight)
        if weight_total <= 0.0:
            return 0.0
        return weighted_sum / weight_total
