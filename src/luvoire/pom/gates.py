"""Three-gate Pattern-Oriented Modeling validation primitives.

Each gate compares a simulated empirical distribution against a target
:class:`~luvoire.pom.patterns.Pattern` using the Kolmogorov-Smirnov (KS)
distance between their cumulative distribution functions. A gate "passes"
when the KS distance is at or below a configured threshold.

The KS distance is computed entirely from binned histograms (numpy + stdlib
only); we deliberately do not depend on ``scipy.stats`` so the POM subpackage
remains importable from a clean ``pip install -e .`` without research extras.
For two normalised histograms with the same number of bins, the discrete
KS distance equals ``max |F_sim(k) - F_target(k)|`` over bin index ``k``.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from luvoire.pom.patterns import Pattern


@dataclass(frozen=True, slots=True)
class GateConfig:
    """Configuration for a single POM gate.

    Attributes
    ----------
    pattern:
        Target pattern to compare against.
    ks_threshold:
        Maximum KS distance for which the gate is considered to pass.
        Must lie in ``[0.0, 1.0]``.
    weight:
        Relative weight in the composite POM score. Must be positive.
    """

    pattern: Pattern
    ks_threshold: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.ks_threshold <= 1.0:
            raise ValueError(
                f"ks_threshold must lie in [0.0, 1.0] (got {self.ks_threshold})"
            )
        if self.weight <= 0.0:
            raise ValueError(f"weight must be positive (got {self.weight})")


@dataclass(frozen=True, slots=True)
class GateResult:
    """Outcome of evaluating a single gate."""

    pattern_id: str
    ks_distance: float
    passed: bool
    weight: float


def _empirical_histogram(samples: np.ndarray, bins: int) -> np.ndarray:
    """Bin ``samples`` into a normalised histogram of length ``bins``.

    The binning uses ``[samples.min(), samples.max()]`` for the range to
    mirror :func:`luvoire.pom.patterns.pattern_from_samples`. When all
    samples are identical the function returns a histogram with all mass
    in the first bin so the bin layout is preserved.
    """

    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        raise ValueError("simulated samples must contain at least one value")
    if not np.all(np.isfinite(arr)):
        raise ValueError("simulated samples must contain finite values")
    lo = float(arr.min())
    hi = float(arr.max())
    if lo == hi:
        hist = np.zeros(bins, dtype=float)
        hist[0] = 1.0
        return hist
    counts, _ = np.histogram(arr, bins=bins, range=(lo, hi))
    total = counts.sum()
    if total == 0:
        raise ValueError("simulated histogram contains zero counts")
    hist = counts.astype(float) / float(total)
    normalised: np.ndarray = hist / hist.sum()
    return normalised


def _ks_distance(simulated: np.ndarray, target: np.ndarray) -> float:
    """Compute the discrete KS distance between two binned distributions."""

    if simulated.shape != target.shape:
        raise ValueError(
            f"simulated and target shapes differ: {simulated.shape} vs {target.shape}"
        )
    cdf_sim = np.cumsum(simulated)
    cdf_tgt = np.cumsum(target)
    return float(np.max(np.abs(cdf_sim - cdf_tgt)))


def evaluate_gate(simulated: np.ndarray, config: GateConfig) -> GateResult:
    """Evaluate a single POM gate against ``simulated`` samples.

    Parameters
    ----------
    simulated:
        Raw simulated samples (1-D array). The function bins them with the
        same ``bins`` count as ``config.pattern``.
    config:
        Gate configuration.
    """

    pattern = config.pattern
    sim_hist = _empirical_histogram(np.asarray(simulated, dtype=float), pattern.bins)
    target_hist = pattern.target_array()
    distance = _ks_distance(sim_hist, target_hist)
    return GateResult(
        pattern_id=pattern.pattern_id,
        ks_distance=distance,
        passed=distance <= config.ks_threshold,
        weight=config.weight,
    )


def evaluate_three_gates(
    simulated_g1: np.ndarray,
    simulated_g2: np.ndarray,
    simulated_g3: np.ndarray,
    configs: tuple[GateConfig, GateConfig, GateConfig],
) -> tuple[GateResult, GateResult, GateResult]:
    """Evaluate the canonical three-gate POM bundle (G1, G2, G3)."""

    cfg_g1, cfg_g2, cfg_g3 = configs
    return (
        evaluate_gate(simulated_g1, cfg_g1),
        evaluate_gate(simulated_g2, cfg_g2),
        evaluate_gate(simulated_g3, cfg_g3),
    )


__all__ = [
    "GateConfig",
    "GateResult",
    "evaluate_gate",
    "evaluate_three_gates",
]
