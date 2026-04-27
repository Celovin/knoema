"""Pure-numpy Approximate Bayesian Computation (ABC) rejection sampler.

This is the always-available fallback calibrator for ABM workflows that cannot
or do not want to depend on ``sbi``. The estimator follows the textbook
rejection-ABC scheme of Tavare et al. (1997):

1. draw a parameter vector ``theta`` uniformly from the prior box,
2. simulate one synthetic observation ``y_sim = simulator(theta)``,
3. accept ``theta`` iff ``||y_sim - observed||_2 <= epsilon``.

Given a fixed ``seed`` the proposal stream is fully deterministic, so the same
spec always returns the same accepted thetas on a given numpy version. We make
no claims about the posterior approximation quality of rejection ABC — it is
provided primarily as a smoke-test calibrator and as a reference baseline for
the optional ``sbi`` adapter.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class RejectionAbcSpec:
    """Configuration for a deterministic rejection-ABC run."""

    prior_bounds: tuple[tuple[float, float], ...]
    epsilon: float
    n_proposals: int
    seed: int


@dataclass(frozen=True, slots=True)
class AbcResult:
    """Result of a rejection-ABC pass.

    ``accepted_thetas`` has shape ``(n_accepted, d)`` where ``d`` is the prior
    dimension. ``acceptance_rate`` is ``n_accepted / n_proposals``.
    """

    accepted_thetas: np.ndarray
    acceptance_rate: float
    n_accepted: int


def rejection_abc(
    simulator: Callable[[np.ndarray], np.ndarray],
    observed: np.ndarray,
    spec: RejectionAbcSpec,
) -> AbcResult:
    """Run a deterministic rejection-ABC pass against ``observed``.

    Parameters
    ----------
    simulator:
        Callable taking a 1-D parameter vector of length ``d`` and returning a
        1-D output array. The output length must match ``observed``.
    observed:
        1-D array of summary statistics from the real system.
    spec:
        Frozen configuration. ``epsilon`` must be non-negative;
        ``n_proposals`` must be positive; each prior bound must satisfy
        ``lo < hi``.
    """

    if spec.epsilon < 0.0:
        raise ValueError(f"epsilon must be non-negative (got {spec.epsilon})")
    if spec.n_proposals <= 0:
        raise ValueError(f"n_proposals must be positive (got {spec.n_proposals})")
    if len(spec.prior_bounds) == 0:
        raise ValueError("at least one prior bound is required")
    for i, (lo, hi) in enumerate(spec.prior_bounds):
        if not lo < hi:
            raise ValueError(
                f"prior_bounds[{i}] must satisfy lo < hi (got {lo}, {hi})"
            )

    observed_arr = np.asarray(observed, dtype=float).ravel()
    if observed_arr.size == 0:
        raise ValueError("observed must be non-empty")

    rng = np.random.default_rng(spec.seed)
    d = len(spec.prior_bounds)
    accepted: list[np.ndarray] = []
    for _ in range(spec.n_proposals):
        theta = np.empty(d, dtype=float)
        for j, (lo, hi) in enumerate(spec.prior_bounds):
            theta[j] = rng.uniform(lo, hi)
        y_sim = np.asarray(simulator(theta), dtype=float).ravel()
        if y_sim.shape != observed_arr.shape:
            raise ValueError(
                f"simulator output shape {y_sim.shape} does not match "
                f"observed shape {observed_arr.shape}"
            )
        distance = float(np.linalg.norm(y_sim - observed_arr))
        if distance <= spec.epsilon:
            accepted.append(theta)

    accepted_arr = (
        np.stack(accepted, axis=0) if accepted else np.empty((0, d), dtype=float)
    )
    n_accepted = int(accepted_arr.shape[0])
    rate = n_accepted / float(spec.n_proposals)
    return AbcResult(
        accepted_thetas=accepted_arr,
        acceptance_rate=rate,
        n_accepted=n_accepted,
    )


__all__ = [
    "AbcResult",
    "RejectionAbcSpec",
    "rejection_abc",
]
