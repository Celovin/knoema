"""Saltelli sampling and Sobol first-order/total-order indices.

The estimators are deterministic given an integer seed; the same seed always
yields the same matrices and the same indices on a given numpy version. We
report the radial-form estimators of Saltelli (2002):

    S_i  = V_i / V         (first-order)
    S_Ti = E_X~i[V_Xi(Y|X~i)] / V    (total order)

with the standard A/B/AB matrix construction, which is what SALib uses by
default. We use Jansen (1999) for V_i and Saltelli (2010) for V_Ti, both of
which are recommended in SALib's docs and are numerically stable for small
sample counts.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SaltelliSamples:
    """A radial Saltelli sample design.

    ``A`` and ``B`` have shape ``(n, d)`` where ``n`` is the base sample count
    and ``d`` is the number of input variables. ``AB`` has shape ``(d, n, d)``;
    ``AB[i]`` is matrix ``A`` with column ``i`` replaced by column ``i`` of
    ``B``. The total number of model evaluations is ``n * (d + 2)``.
    """

    a: np.ndarray
    b: np.ndarray
    ab: np.ndarray
    bounds: tuple[tuple[float, float], ...]

    @property
    def n(self) -> int:
        return int(self.a.shape[0])

    @property
    def d(self) -> int:
        return int(self.a.shape[1])

    @property
    def total_evaluations(self) -> int:
        return self.n * (self.d + 2)


@dataclass(frozen=True, slots=True)
class SobolIndices:
    first_order: np.ndarray
    total_order: np.ndarray
    variable_names: tuple[str, ...]
    base_sample_count: int

    def as_dict(self) -> dict[str, dict[str, float]]:
        return {
            name: {
                "first_order": float(self.first_order[i]),
                "total_order": float(self.total_order[i]),
            }
            for i, name in enumerate(self.variable_names)
        }


def saltelli_sample(
    bounds: Sequence[tuple[float, float]],
    n: int,
    *,
    seed: int,
) -> SaltelliSamples:
    """Build a deterministic radial Saltelli design over the given bounds."""

    if n <= 0:
        raise ValueError(f"n must be positive (got {n})")
    rng = np.random.default_rng(seed)
    d = len(bounds)
    if d == 0:
        raise ValueError("at least one variable bound is required")
    a_unit = rng.random((n, d))
    b_unit = rng.random((n, d))
    a = _scale_to_bounds(a_unit, bounds)
    b = _scale_to_bounds(b_unit, bounds)
    ab = np.empty((d, n, d), dtype=float)
    for i in range(d):
        radial = a.copy()
        radial[:, i] = b[:, i]
        ab[i] = radial
    return SaltelliSamples(a=a, b=b, ab=ab, bounds=tuple(bounds))


def sobol_indices(
    samples: SaltelliSamples,
    model: Callable[[np.ndarray], np.ndarray],
    variable_names: Sequence[str],
) -> SobolIndices:
    """Estimate first-order and total-order Sobol indices for ``model``.

    ``model`` must accept an array of shape ``(n, d)`` and return a 1-D
    output array of length ``n``. The estimator uses Jansen (1999) for the
    first-order term and Saltelli (2010) for the total-order term, matching
    SALib defaults.
    """

    if len(variable_names) != samples.d:
        raise ValueError(
            f"variable_names length {len(variable_names)} does not match "
            f"sample dimension {samples.d}"
        )
    y_a = np.asarray(model(samples.a), dtype=float)
    y_b = np.asarray(model(samples.b), dtype=float)
    y_ab = np.empty((samples.d, samples.n), dtype=float)
    for i in range(samples.d):
        y_ab[i] = np.asarray(model(samples.ab[i]), dtype=float)
    var = float(np.var(np.concatenate([y_a, y_b]), ddof=1))
    if var <= 0.0:
        first = np.zeros(samples.d, dtype=float)
        total = np.zeros(samples.d, dtype=float)
        return SobolIndices(
            first_order=first,
            total_order=total,
            variable_names=tuple(variable_names),
            base_sample_count=samples.n,
        )
    first = np.empty(samples.d, dtype=float)
    total = np.empty(samples.d, dtype=float)
    for i in range(samples.d):
        first[i] = (
            float(np.mean(y_b * (y_ab[i] - y_a))) / var
        )
        total[i] = (
            0.5 * float(np.mean((y_a - y_ab[i]) ** 2)) / var
        )
    return SobolIndices(
        first_order=first,
        total_order=total,
        variable_names=tuple(variable_names),
        base_sample_count=samples.n,
    )


def _scale_to_bounds(
    unit: np.ndarray,
    bounds: Sequence[tuple[float, float]],
) -> np.ndarray:
    out = np.empty_like(unit)
    for i, (lo, hi) in enumerate(bounds):
        if not lo < hi:
            raise ValueError(
                f"bounds[{i}] must satisfy lo < hi (got {lo}, {hi})"
            )
        out[:, i] = lo + (hi - lo) * unit[:, i]
    return out


__all__ = [
    "SaltelliSamples",
    "SobolIndices",
    "saltelli_sample",
    "sobol_indices",
]
