"""Counterfactual demographic scenario engine.

Under the cohort-component model, exploring policy what-if questions
(``what if fertility rises to 1.2?``, ``what if net migration falls to
0?``) reduces to perturbing the input :class:`DemographicRates` and
re-running the projector. This module provides a small, deterministic,
human-readable interface for declaring such perturbations and running
multiple labelled scenarios in one call.

Civilian Use Policy alignment
-----------------------------
- Output is **always aggregate** at the registered region label and
  matches the projector's per-region cohort vectors.
- Outputs are **counterfactual scenarios**, not predictions: each
  trajectory is an explicit ``what would happen if these aggregate rates
  held`` simulation, in line with KOSTAT 저위/중위/고위 scenario practice.
- Reproductive-age constraints (asfr zero outside ``[15, 50)``) are
  enforced by :class:`DemographicRates` itself, so multiplicative scaling
  cannot leak fertility into out-of-range cohorts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

import numpy as np

from luvoire.demography.projector import (
    REPRODUCTIVE_AGE_HI,
    REPRODUCTIVE_AGE_LO,
    CohortComponentProjector,
    CohortPopulation,
    DemographicRates,
)

ScenarioKind = Literal["fertility", "mortality", "migration", "composite"]


@dataclass(frozen=True, slots=True)
class RatePerturbation:
    """Multiplicative perturbation applied to a :class:`DemographicRates`.

    Attributes:
        fertility_scale: Multiplier applied to the entire ASFR vector
            within reproductive ages. ``1.0`` is the baseline; ``1.2``
            raises fertility by 20%; ``0.8`` lowers by 20%. Must be
            non-negative.
        mortality_scale: Multiplier applied to ASMR (both sexes). Must
            be in ``[0, 1 / max(asmr) ]`` per element after scaling, but
            we relax to non-negative here and clamp the resulting
            mortality to ``[0, 1]`` at scenario apply time.
        migration_scale: Multiplier applied to net-migration counts
            (both sexes). Negative scales are permitted and represent
            net-direction reversal.

    A :attr:`fertility_scale` of ``1.0``, :attr:`mortality_scale` of
    ``1.0``, and :attr:`migration_scale` of ``1.0`` is the **identity**
    perturbation — the resulting :class:`DemographicRates` is byte-equal
    to the baseline.
    """

    fertility_scale: float = 1.0
    mortality_scale: float = 1.0
    migration_scale: float = 1.0

    def __post_init__(self) -> None:
        for name in ("fertility_scale", "mortality_scale"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a real number")
            if value < 0:
                raise ValueError(f"{name} must be non-negative (got {value})")
        if not isinstance(self.migration_scale, (int, float)) or isinstance(
            self.migration_scale, bool
        ):
            raise TypeError("migration_scale must be a real number")

    def apply(self, baseline: DemographicRates) -> DemographicRates:
        """Return a new :class:`DemographicRates` after applying this
        perturbation to ``baseline``. The baseline is not mutated.
        """

        asfr = baseline.asfr.copy()
        asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] *= self.fertility_scale
        asmr_m = np.clip(baseline.asmr_male * self.mortality_scale, 0.0, 1.0)
        asmr_f = np.clip(baseline.asmr_female * self.mortality_scale, 0.0, 1.0)
        mig_m = baseline.net_migration_male * self.migration_scale
        mig_f = baseline.net_migration_female * self.migration_scale
        return DemographicRates(
            asfr=asfr,
            asmr_male=asmr_m,
            asmr_female=asmr_f,
            net_migration_male=mig_m,
            net_migration_female=mig_f,
            sex_ratio_at_birth=baseline.sex_ratio_at_birth,
        )


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    """Result of one labelled counterfactual scenario.

    Attributes:
        label: Human-readable scenario name (e.g. ``"low_fertility"``,
            ``"high_migration"``).
        kind: One of :data:`ScenarioKind` for downstream filtering.
        trajectory: Tuple of :class:`CohortPopulation` covering years
            ``initial.year + 1`` through ``initial.year + horizon``
            inclusive.
        perturbation: The :class:`RatePerturbation` that produced this
            trajectory.
    """

    label: str
    kind: ScenarioKind
    trajectory: tuple[CohortPopulation, ...]
    perturbation: RatePerturbation

    def total_population_series(self) -> tuple[float, ...]:
        """Return ``(year, total)`` totals reduced to a 1-D float tuple."""

        return tuple(pop.total for pop in self.trajectory)


class CounterfactualScenarioEngine:
    """Run a labelled set of rate perturbations against one baseline."""

    def __init__(self, projector: CohortComponentProjector | None = None) -> None:
        self._projector = projector or CohortComponentProjector()

    @property
    def projector(self) -> CohortComponentProjector:
        return self._projector

    def run(
        self,
        *,
        initial: CohortPopulation,
        baseline_rates: DemographicRates,
        horizon_years: int,
        scenarios: Mapping[str, tuple[ScenarioKind, RatePerturbation]],
    ) -> tuple[ScenarioResult, ...]:
        """Run each labelled ``(kind, perturbation)`` and return the results.

        Scenarios are processed in the iteration order of ``scenarios``;
        because the engine is fully deterministic, the resulting tuple
        is byte-stable across runs given byte-identical inputs.
        """

        if not isinstance(horizon_years, int) or isinstance(horizon_years, bool):
            raise TypeError("horizon_years must be int")
        if horizon_years < 0:
            raise ValueError("horizon_years must be non-negative")
        results: list[ScenarioResult] = []
        for label, (kind, perturbation) in scenarios.items():
            if not isinstance(label, str) or not label:
                raise ValueError("scenario label must be a non-empty string")
            if kind not in {"fertility", "mortality", "migration", "composite"}:
                raise ValueError(
                    f"unknown scenario kind {kind!r}; expected fertility | "
                    "mortality | migration | composite"
                )
            perturbed = perturbation.apply(baseline_rates)
            trajectory = self._projector.project(initial, perturbed, horizon_years)
            results.append(
                ScenarioResult(
                    label=label,
                    kind=kind,
                    trajectory=trajectory,
                    perturbation=perturbation,
                )
            )
        return tuple(results)


# Canonical KOSTAT-style triple (low / medium / high fertility) used as
# a default reference set. Values mirror KOSTAT 장래인구추계 2022 reference
# multipliers on the medium scenario; users are expected to tune these
# via Tier C parameters.
#
# Wrapped in :class:`types.MappingProxyType` so the canonical dict cannot
# be mutated at module scope — engine determinism depends on this set
# being identical across runs.
KOSTAT_REFERENCE_TRIPLE: Mapping[str, tuple[ScenarioKind, RatePerturbation]] = MappingProxyType(
    {
        "low_fertility": ("fertility", RatePerturbation(fertility_scale=0.85)),
        "medium_fertility": ("fertility", RatePerturbation(fertility_scale=1.00)),
        "high_fertility": ("fertility", RatePerturbation(fertility_scale=1.15)),
    }
)


__all__ = [
    "KOSTAT_REFERENCE_TRIPLE",
    "CounterfactualScenarioEngine",
    "RatePerturbation",
    "ScenarioKind",
    "ScenarioResult",
]
