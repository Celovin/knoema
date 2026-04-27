"""ACT-R-inspired base-level activation weighting for memory recall.

This module ports a single idea from ACT-R (Anderson 2007) into Luvoire's
memory layer: a memory chunk's retrieval probability rises with how often
it has been used and falls with how long ago. The classical formula is:

    B_i = ln( sum_{j=1..n}  (t - t_j) ** (-d) )

where ``t_j`` are the past-use timestamps of chunk ``i`` and ``d`` is a
decay exponent (default ``0.5`` per Anderson 2007).

We expose the formula as a standalone helper so it can be plugged into the
existing :class:`luvoire.memory.SharedDecayScheduler` weight without
touching the locked replay artifacts. The helper is pure, deterministic,
and numpy-vectorised; unit tests cover monotonicity, decay-exponent
sensitivity, and the multi-recall summation property.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

DEFAULT_DECAY_EXPONENT: float = 0.5
"""Default ACT-R decay exponent (Anderson 2007)."""

MINIMUM_AGE_SECONDS: float = 1.0
"""Floor applied to age values so ``(t - t_j)`` never goes to zero."""


@dataclass(frozen=True, slots=True)
class BaseLevelActivation:
    """Result of a base-level activation calculation."""

    activation: float
    use_count: int
    decay_exponent: float


def base_level_activation(
    use_ages_seconds: Sequence[float],
    *,
    decay_exponent: float = DEFAULT_DECAY_EXPONENT,
) -> BaseLevelActivation:
    """Compute ACT-R base-level activation for a single chunk.

    ``use_ages_seconds`` is the sequence of ages (in seconds, all positive)
    of past uses of the chunk relative to the present moment. Ages below
    :data:`MINIMUM_AGE_SECONDS` are clamped up so the power term stays
    finite.

    Returns the activation value (a real number; can be negative for very
    old, rarely-used chunks) plus diagnostic metadata.

    Raises:
        ValueError: When any age is non-positive or the decay exponent is
            non-positive.
    """

    if decay_exponent <= 0.0:
        raise ValueError(
            f"decay_exponent must be positive (got {decay_exponent})"
        )
    if not use_ages_seconds:
        return BaseLevelActivation(
            activation=-math.inf,
            use_count=0,
            decay_exponent=decay_exponent,
        )
    ages = np.asarray(use_ages_seconds, dtype=float)
    if (ages <= 0.0).any():
        raise ValueError("all use ages must be strictly positive")
    clipped = np.maximum(ages, MINIMUM_AGE_SECONDS)
    weighted_sum = float(np.sum(clipped ** (-decay_exponent)))
    activation = math.log(weighted_sum)
    return BaseLevelActivation(
        activation=activation,
        use_count=len(ages),
        decay_exponent=decay_exponent,
    )


def actr_retention_weight(
    use_ages_seconds: Sequence[float],
    *,
    decay_exponent: float = DEFAULT_DECAY_EXPONENT,
) -> float:
    """Convert base-level activation to a ``[0, 1]`` retention weight.

    The conversion uses a logistic squashing of the raw activation so the
    output can be plugged into Luvoire's existing decay-score combination
    (which expects retention in ``[0, 1]``).
    """

    bla = base_level_activation(
        use_ages_seconds, decay_exponent=decay_exponent
    )
    if bla.activation == -math.inf:
        return 0.0
    return 1.0 / (1.0 + math.exp(-bla.activation))


__all__ = [
    "DEFAULT_DECAY_EXPONENT",
    "MINIMUM_AGE_SECONDS",
    "BaseLevelActivation",
    "actr_retention_weight",
    "base_level_activation",
]
