"""Nested-data statistical summaries for batch playground runs.

The helpers prefer optional ``statsmodels`` and ``PyMC`` backends when available,
but keep a deterministic analytic fallback so the replay stack stays runnable in
offline environments and CI.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import NormalDist, fmean
from typing import Any, TypedDict

import numpy as np

_SMF: Any | None
_PM: Any | None

try:  # pragma: no cover - optional dependency
    import statsmodels.formula.api as _smf  # type: ignore[import-not-found,import-untyped,unused-ignore]
except ImportError:  # pragma: no cover - optional dependency
    _SMF = None
else:  # pragma: no cover - optional dependency
    _SMF = _smf

try:  # pragma: no cover - optional dependency
    import pymc as _pm  # type: ignore[import-not-found,import-untyped,unused-ignore]
except ImportError:  # pragma: no cover - optional dependency
    _PM = None
else:  # pragma: no cover - optional dependency
    _PM = _pm

COOPERATIVE_ACTIONS = frozenset(
    {
        "accept",
        "comfort",
        "give",
        "offer",
        "persuade",
        "quest_accept",
        "quest_offer",
        "speak",
        "trade_offer",
    }
)


class _MixedSummary(TypedDict):
    backend: str
    fixed_effect: float
    intercept: float
    random_intercept_sd: float
    p_value: float


class _PosteriorSummary(TypedDict):
    posterior_mean: float
    credible_interval_low: float
    credible_interval_high: float
    probability_positive: float


@dataclass(frozen=True, slots=True)
class SeedTickObservation:
    seed: int
    tick: int
    late_phase: int
    total_actions: int
    cooperative_actions: int
    cooperative_rate: float


@dataclass(frozen=True, slots=True)
class MixedEffectsPosteriorSummary:
    backend: str
    seed_count: int
    observation_count: int
    fixed_effect: float
    intercept: float
    random_intercept_sd: float
    p_value: float
    posterior_mean: float
    credible_interval_low: float
    credible_interval_high: float
    probability_positive: float
    mean_cooperative_rate: float


def summarize_seed_tick_effect(
    rows: Sequence[Mapping[str, Any]],
) -> MixedEffectsPosteriorSummary | None:
    observations = _seed_tick_observations(rows)
    if len(observations) < 4:
        return None

    # statsmodels raises ``numpy.linalg.LinAlgError`` (Singular matrix)
    # when within-group variance collapses in the test fixture data,
    # and may also raise ``ValueError`` / ``ConvergenceWarning``-shaped
    # errors on degenerate inputs. Fall back to the analytic summary
    # rather than failing the whole research pipeline — the analytic
    # path returns the same shape of dict and downstream code works
    # against either backend.
    if _SMF is None:
        mixed_summary = _analytic_mixed_summary(observations)
    else:
        try:
            mixed_summary = _statsmodels_summary(observations)
        except (np.linalg.LinAlgError, ValueError, RuntimeError):
            mixed_summary = _analytic_mixed_summary(observations)

    if _PM is not None:
        posterior_summary = _pymc_posterior(observations)
        backend = f"{mixed_summary['backend']} + pymc"
    else:
        posterior_summary = _analytic_posterior(observations)
        backend = f"{mixed_summary['backend']} + analytic posterior"

    return MixedEffectsPosteriorSummary(
        backend=backend,
        seed_count=len({observation.seed for observation in observations}),
        observation_count=len(observations),
        fixed_effect=float(mixed_summary["fixed_effect"]),
        intercept=float(mixed_summary["intercept"]),
        random_intercept_sd=float(mixed_summary["random_intercept_sd"]),
        p_value=float(mixed_summary["p_value"]),
        posterior_mean=float(posterior_summary["posterior_mean"]),
        credible_interval_low=float(posterior_summary["credible_interval_low"]),
        credible_interval_high=float(posterior_summary["credible_interval_high"]),
        probability_positive=float(posterior_summary["probability_positive"]),
        mean_cooperative_rate=fmean(observation.cooperative_rate for observation in observations),
    )


def _seed_tick_observations(rows: Sequence[Mapping[str, Any]]) -> tuple[SeedTickObservation, ...]:
    seed_rows = [
        row
        for row in rows
        if str(row.get("record_type", "")) == "seed_tick_stat"
    ]
    if not seed_rows:
        return ()

    ticks = sorted({int(row.get("tick", 0)) for row in seed_rows})
    if not ticks:
        return ()
    threshold = ticks[len(ticks) // 2]

    observations: list[SeedTickObservation] = []
    for row in seed_rows:
        action_counts = row.get("action_type_counts", {})
        if not isinstance(action_counts, Mapping):
            continue
        total_actions = int(row.get("total_actions", 0))
        if total_actions <= 0:
            continue
        cooperative_actions = sum(
            int(action_counts.get(action_type, 0))
            for action_type in COOPERATIVE_ACTIONS
        )
        tick = int(row.get("tick", 0))
        observations.append(
            SeedTickObservation(
                seed=int(row.get("seed", 0)),
                tick=tick,
                late_phase=1 if tick >= threshold else 0,
                total_actions=total_actions,
                cooperative_actions=cooperative_actions,
                cooperative_rate=cooperative_actions / total_actions,
            )
        )
    return tuple(sorted(observations, key=lambda observation: (observation.seed, observation.tick)))


def _analytic_mixed_summary(
    observations: Sequence[SeedTickObservation],
) -> _MixedSummary:
    grouped: dict[int, dict[str, list[float]]] = {}
    for observation in observations:
        bucket = grouped.setdefault(observation.seed, {"early": [], "late": []})
        phase_key = "late" if observation.late_phase else "early"
        bucket[phase_key].append(observation.cooperative_rate)

    early_means: list[float] = []
    deltas: list[float] = []
    for phases in grouped.values():
        early = phases["early"]
        late = phases["late"]
        if not early or not late:
            continue
        early_mean = fmean(early)
        early_means.append(early_mean)
        deltas.append(fmean(late) - early_mean)

    if not deltas:
        return {
            "backend": "analytic fallback",
            "fixed_effect": 0.0,
            "intercept": 0.0,
            "random_intercept_sd": 0.0,
            "p_value": 1.0,
        }

    intercept = fmean(early_means)
    fixed_effect = fmean(deltas)
    random_intercept_sd = _sample_standard_deviation(early_means)
    standard_error = _sample_standard_deviation(deltas) / math.sqrt(len(deltas)) if len(deltas) > 1 else 0.0
    if standard_error == 0.0:
        p_value = 0.0 if abs(fixed_effect) > 0 else 1.0
    else:
        z_score = fixed_effect / standard_error
        p_value = 2.0 * (1.0 - NormalDist().cdf(abs(z_score)))
    return {
        "backend": "analytic fallback",
        "fixed_effect": fixed_effect,
        "intercept": intercept,
        "random_intercept_sd": random_intercept_sd,
        "p_value": min(max(p_value, 0.0), 1.0),
    }


def _statsmodels_summary(
    observations: Sequence[SeedTickObservation],
) -> _MixedSummary:
    assert _SMF is not None
    import pandas as pd  # type: ignore[import-untyped]

    dataframe = pd.DataFrame(
        {
            "seed": [observation.seed for observation in observations],
            "late_phase": [observation.late_phase for observation in observations],
            "cooperative_rate": [observation.cooperative_rate for observation in observations],
        }
    )
    model = _SMF.mixedlm("cooperative_rate ~ late_phase", dataframe, groups=dataframe["seed"])
    fitted = model.fit(reml=False, method="lbfgs", disp=False)
    random_sd = 0.0
    covariance = getattr(fitted, "cov_re", None)
    if covariance is not None:
        try:
            random_sd = math.sqrt(float(covariance.iloc[0, 0]))
        except Exception:  # pragma: no cover - defensive optional backend handling
            random_sd = 0.0
    return {
        "backend": "statsmodels",
        "fixed_effect": float(fitted.params.get("late_phase", 0.0)),
        "intercept": float(fitted.params.get("Intercept", 0.0)),
        "random_intercept_sd": random_sd,
        "p_value": float(fitted.pvalues.get("late_phase", 1.0)),
    }


def _analytic_posterior(
    observations: Sequence[SeedTickObservation],
) -> _PosteriorSummary:
    deltas = _seed_level_deltas(observations)
    if not deltas:
        return {
            "posterior_mean": 0.0,
            "credible_interval_low": 0.0,
            "credible_interval_high": 0.0,
            "probability_positive": 0.5,
        }

    sample_mean = fmean(deltas)
    sample_var = _sample_standard_deviation(deltas) ** 2
    if sample_var == 0.0:
        posterior_sd = 1e-6
        posterior_mean = sample_mean
    else:
        likelihood_var = sample_var / len(deltas)
        prior_var = 1.0
        posterior_var = 1.0 / ((1.0 / prior_var) + (1.0 / likelihood_var))
        posterior_mean = posterior_var * (sample_mean / likelihood_var)
        posterior_sd = math.sqrt(posterior_var)
    distribution = NormalDist(mu=posterior_mean, sigma=max(posterior_sd, 1e-6))
    return {
        "posterior_mean": posterior_mean,
        "credible_interval_low": distribution.inv_cdf(0.025),
        "credible_interval_high": distribution.inv_cdf(0.975),
        "probability_positive": 1.0 - distribution.cdf(0.0),
    }


def _pymc_posterior(
    observations: Sequence[SeedTickObservation],
) -> _PosteriorSummary:
    assert _PM is not None
    deltas = _seed_level_deltas(observations)
    if not deltas:
        return {
            "posterior_mean": 0.0,
            "credible_interval_low": 0.0,
            "credible_interval_high": 0.0,
            "probability_positive": 0.5,
        }
    with _PM.Model():  # pragma: no cover - optional dependency
        delta = _PM.Normal("delta", mu=0.0, sigma=1.0)
        sigma = _PM.HalfNormal("sigma", sigma=1.0)
        _PM.Normal("obs", mu=delta, sigma=sigma, observed=deltas)
        trace = _PM.sample(
            draws=500,
            tune=300,
            chains=2,
            random_seed=20260419,
            progressbar=False,
            compute_convergence_checks=False,
            return_inferencedata=False,
        )
    samples = trace.get_values("delta", combine=True)  # pragma: no cover - optional dependency
    ordered = sorted(float(sample) for sample in samples)
    lower_index = max(0, int(0.025 * (len(ordered) - 1)))
    upper_index = min(len(ordered) - 1, int(0.975 * (len(ordered) - 1)))
    positive_count = sum(1 for sample in ordered if sample > 0.0)
    return {
        "posterior_mean": fmean(ordered),
        "credible_interval_low": ordered[lower_index],
        "credible_interval_high": ordered[upper_index],
        "probability_positive": positive_count / len(ordered),
    }


def _seed_level_deltas(observations: Sequence[SeedTickObservation]) -> list[float]:
    grouped: dict[int, dict[str, list[float]]] = {}
    for observation in observations:
        bucket = grouped.setdefault(observation.seed, {"early": [], "late": []})
        phase_key = "late" if observation.late_phase else "early"
        bucket[phase_key].append(observation.cooperative_rate)
    deltas: list[float] = []
    for phases in grouped.values():
        early = phases["early"]
        late = phases["late"]
        if early and late:
            deltas.append(fmean(late) - fmean(early))
    return deltas


def _sample_standard_deviation(values: Sequence[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean_value = fmean(values)
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(max(variance, 0.0))
