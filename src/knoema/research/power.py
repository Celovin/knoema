"""Power-analysis helpers for research-facing playground workflows."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from statistics import NormalDist
from typing import Literal

PowerTestFamily = Literal["independent_t", "paired_t", "two_proportions"]


@dataclass(frozen=True)
class PowerAnalysisPlan:
    """Deterministic sample-size recommendation for a planned study."""

    test_family: PowerTestFamily
    effect_size: float
    alpha: float
    target_power: float
    tails: int
    sample_size_per_group: int
    total_sample_size: int
    method: str


def estimate_sample_size(
    *,
    effect_size: float,
    alpha: float = 0.05,
    target_power: float = 0.8,
    test_family: PowerTestFamily = "independent_t",
    tails: int = 2,
) -> PowerAnalysisPlan:
    """Estimate a balanced sample size using a normal-approximation rule.

    The formulas are intentionally lightweight so the playground can surface a
    G*Power-style planning recommendation without pulling in a heavier stats
    stack. ``effect_size`` is interpreted as Cohen's ``d`` for the t-test
    variants and Cohen's ``h`` for ``two_proportions``.
    """

    if effect_size <= 0:
        raise ValueError("effect_size must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 < target_power < 1:
        raise ValueError("target_power must be between 0 and 1")
    if tails not in {1, 2}:
        raise ValueError("tails must be 1 or 2")

    normal = NormalDist()
    z_alpha = normal.inv_cdf(1.0 - (alpha / tails))
    z_beta = normal.inv_cdf(target_power)
    base_requirement = ((z_alpha + z_beta) ** 2) / (effect_size**2)

    if test_family == "independent_t":
        sample_size_per_group = ceil(2.0 * base_requirement)
        total_sample_size = sample_size_per_group * 2
        method = "Balanced two-sample t-test approximation (Cohen's d)"
    elif test_family == "paired_t":
        sample_size_per_group = ceil(base_requirement)
        total_sample_size = sample_size_per_group
        method = "Paired-samples t-test approximation (Cohen's d)"
    elif test_family == "two_proportions":
        sample_size_per_group = ceil(2.0 * base_requirement)
        total_sample_size = sample_size_per_group * 2
        method = "Two-proportion z-test approximation (Cohen's h)"
    else:  # pragma: no cover - Literal guards valid families.
        raise ValueError(f"unsupported test_family: {test_family}")

    return PowerAnalysisPlan(
        test_family=test_family,
        effect_size=effect_size,
        alpha=alpha,
        target_power=target_power,
        tails=tails,
        sample_size_per_group=sample_size_per_group,
        total_sample_size=total_sample_size,
        method=method,
    )
