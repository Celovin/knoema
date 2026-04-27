"""Differential privacy noise layer for aggregate demographic output.

Adds calibrated Laplace or Gaussian noise to aggregate counts so the
released values satisfy ``ε``-DP (Laplace) or ``(ε, δ)``-DP (Gaussian)
under the standard count-query interpretation. The noise magnitude is
calibrated to a caller-declared ``sensitivity`` (the maximum
contribution one individual can make to any single count, typically
``1`` for population counts).

References
----------
- Dwork & Roth, *The Algorithmic Foundations of Differential Privacy*
  (2014). Laplace mechanism: Theorem 3.6. Gaussian mechanism: Theorem
  A.1, requires ``sigma >= sensitivity * sqrt(2 * ln(1.25 / delta)) / epsilon``.

The mechanism is **fully deterministic** under a fixed integer seed:
the same seed and the same input counts produce byte-identical noisy
counts. This preserves Luvoire's auditable replay guarantees while
still satisfying the formal DP definition (DP is a property of the
release distribution, not of any single sample — auditing requires
that someone observing the released noisy count cannot distinguish
the true count from neighbouring datasets within the privacy budget).

Civilian Use Policy alignment
-----------------------------
This layer applies on top of aggregate counts (``CellPopulation`` or
similar). It is **not** a sufficient privacy mitigation on its own
for individual-level release — it is a defence-in-depth layer for
already-aggregate counts. Sub-시군구 / per-person release is forbidden
by :mod:`luvoire.demography.byod` independently of any DP mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

DpMechanism = Literal["laplace", "gaussian"]
"""Supported DP mechanisms. Laplace gives pure ε-DP; Gaussian gives
(ε, δ)-DP with weaker tail concentration but matched lower variance
for repeated composition."""


@dataclass(frozen=True, slots=True)
class DpBudget:
    """Differential privacy budget parameters.

    Attributes:
        epsilon: Privacy budget. Smaller is stricter (more noise).
            Must be positive.
        delta: Failure parameter for Gaussian mechanism — the
            probability that the privacy guarantee fails. Must be in
            ``[0, 1)``. Ignored by the Laplace mechanism but kept on
            the dataclass for uniform plumbing. Typically very small
            (``1e-5`` or smaller) so the failure mode is rare.
        sensitivity: Maximum contribution any individual can make to
            any single count being released. ``1`` for population
            counts; higher for sums of bounded values. Must be
            positive.
    """

    epsilon: float
    delta: float = 0.0
    sensitivity: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.epsilon, (int, float)) or isinstance(self.epsilon, bool):
            raise TypeError("epsilon must be a real number")
        if self.epsilon <= 0:
            raise ValueError(f"epsilon must be positive (got {self.epsilon})")
        if not isinstance(self.delta, (int, float)) or isinstance(self.delta, bool):
            raise TypeError("delta must be a real number")
        if not 0.0 <= self.delta < 1.0:
            raise ValueError(f"delta must be in [0, 1) (got {self.delta})")
        if not isinstance(self.sensitivity, (int, float)) or isinstance(
            self.sensitivity, bool
        ):
            raise TypeError("sensitivity must be a real number")
        if self.sensitivity <= 0:
            raise ValueError(f"sensitivity must be positive (got {self.sensitivity})")


def _laplace_scale(budget: DpBudget) -> float:
    return budget.sensitivity / budget.epsilon


def _gaussian_sigma(budget: DpBudget) -> float:
    if budget.delta <= 0:
        raise ValueError(
            f"gaussian mechanism requires delta > 0 (got {budget.delta})"
        )
    return budget.sensitivity * float(np.sqrt(2.0 * np.log(1.25 / budget.delta))) / budget.epsilon


def add_dp_noise(
    counts: np.ndarray,
    *,
    budget: DpBudget,
    mechanism: DpMechanism = "laplace",
    seed: int,
    clamp_non_negative: bool = True,
) -> np.ndarray:
    """Return ``counts`` with calibrated DP noise added.

    Parameters
    ----------
    counts:
        Non-negative integer or float aggregate counts.
    budget:
        :class:`DpBudget` carrying ``epsilon``, ``delta``, and
        ``sensitivity``.
    mechanism:
        ``"laplace"`` (default) for pure ε-DP, ``"gaussian"`` for
        (ε, δ)-DP. ``"gaussian"`` requires ``budget.delta > 0``.
    seed:
        Integer seed for the deterministic numpy RNG.
    clamp_non_negative:
        When ``True`` (default) the result is clamped to ``[0, +inf)``
        so released counts stay non-negative; this is a standard
        post-processing step that does not alter the DP guarantee
        because post-processing of DP outputs is itself DP (Theorem
        3.5 of Dwork & Roth).
    """

    arr = np.asarray(counts, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"counts must be 1-D (got shape {arr.shape})")
    if (arr < 0).any():
        raise ValueError("counts must be non-negative for DP noise application")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be int")

    rng = np.random.default_rng(seed)
    if mechanism == "laplace":
        scale = _laplace_scale(budget)
        noise = rng.laplace(loc=0.0, scale=scale, size=arr.shape)
    elif mechanism == "gaussian":
        sigma = _gaussian_sigma(budget)
        noise = rng.normal(loc=0.0, scale=sigma, size=arr.shape)
    else:
        raise ValueError(
            f"unknown mechanism {mechanism!r}; expected 'laplace' or 'gaussian'"
        )

    noisy = arr + noise
    if clamp_non_negative:
        noisy = np.maximum(noisy, 0.0)
    return noisy


def laplace_noise_scale(budget: DpBudget) -> float:
    """Return the Laplace scale ``b = sensitivity / epsilon``.

    Public helper exposed for diagnostic / reporting — the noise
    standard deviation under the Laplace mechanism is ``b * sqrt(2)``.
    """

    return _laplace_scale(budget)


def gaussian_noise_sigma(budget: DpBudget) -> float:
    """Return the Gaussian standard deviation
    ``sigma = sensitivity * sqrt(2 * ln(1.25 / delta)) / epsilon``.

    Raises ``ValueError`` if ``budget.delta <= 0``.
    """

    return _gaussian_sigma(budget)


__all__ = [
    "DpBudget",
    "DpMechanism",
    "add_dp_noise",
    "gaussian_noise_sigma",
    "laplace_noise_scale",
]
