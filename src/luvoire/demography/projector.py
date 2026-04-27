"""Cohort-component demographic projector (KOSTAT 장래인구추계 standard).

This module implements the canonical cohort-component projection technique
used by KOSTAT 장래인구추계, UN World Population Prospects, and the
mainstream demography literature (Preston, Heuveline & Guillot 2001).

Method
------
For each single-year age cohort ``a`` and sex, the population one year
ahead is::

    pop_next[a + 1] = pop[a] * (1 - asmr[a]) + net_migration[a]

Births at year ``t + 1`` are aggregated from age-specific fertility rates
(ASFR) over the female reproductive ages (15-49 inclusive)::

    births = sum(female[a] * asfr[a] for a in range(15, 50))
    male_births   = births * sex_ratio_at_birth / (1 + sex_ratio_at_birth)
    female_births = births / (1 + sex_ratio_at_birth)

The projector is **fully deterministic** — given the same initial cohort
population and the same rate set, the same sequence is produced
byte-identically. There is no random component; counterfactual exploration
is achieved by perturbing the rate inputs (Tier B / Tier C parameters).

Civilian Use Policy alignment
-----------------------------
- Output is **always aggregate** at the registered region label
  (시군구 string, never coordinate). No per-person output is produced.
- Inputs are aggregate KOSIS-style rates; no individual records are read.
- This is a **demographic projection** (추계) not a prediction (예측):
  multiple counterfactual rate scenarios produce parallel trajectories
  for policy what-if comparison, in line with KOSTAT 저위/중위/고위
  scenario practice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

DEFAULT_MAX_AGE: int = 100
"""Maximum single-year age cohort. Population at ``DEFAULT_MAX_AGE`` rolls
forward into itself (open-ended top class) following KOSTAT convention."""

REPRODUCTIVE_AGE_LO: int = 15
REPRODUCTIVE_AGE_HI: int = 50  # exclusive upper bound; ages 15..49 inclusive

DEFAULT_SEX_RATIO_AT_BIRTH: float = 1.05
"""Conventional male:female sex ratio at birth used by KOSTAT."""

Sex = Literal["male", "female"]


def _as_float_array(arr: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
    out = np.asarray(arr, dtype=float)
    if out.ndim != 1:
        raise ValueError(f"expected 1-D array, got shape {out.shape}")
    return out


@dataclass(frozen=True, slots=True)
class CohortPopulation:
    """Single-year age-by-sex population vector for one region and year.

    Attributes:
        year: Calendar year.
        region_label: Region identifier as an opaque **string** (e.g.
            ``"서울특별시 강남구"``). Coordinate systems are deliberately
            excluded; ``no_real_geometry: true`` is preserved.
        male: ``(max_age + 1,)`` non-negative population by single-year
            age. Element ``i`` is the count of males aged ``i`` years.
        female: Same shape as ``male`` for females.

    Construction-time validation rejects negative counts, mismatched
    lengths, and ``region_label`` that decodes to anything other than a
    non-empty string.
    """

    year: int
    region_label: str
    male: np.ndarray
    female: np.ndarray

    def __post_init__(self) -> None:
        if not isinstance(self.year, int) or isinstance(self.year, bool):
            raise TypeError(f"year must be int (got {type(self.year).__name__})")
        if not isinstance(self.region_label, str) or not self.region_label:
            raise ValueError("region_label must be a non-empty string")
        male = _as_float_array(self.male)
        female = _as_float_array(self.female)
        if male.shape != female.shape:
            raise ValueError(
                f"male and female arrays must have the same shape "
                f"(got {male.shape} vs {female.shape})"
            )
        if (male < 0).any() or (female < 0).any():
            raise ValueError("population counts must be non-negative")
        # Re-bind through object.__setattr__ because of the frozen dataclass.
        object.__setattr__(self, "male", male)
        object.__setattr__(self, "female", female)

    @property
    def max_age(self) -> int:
        return int(self.male.shape[0]) - 1

    @property
    def total(self) -> float:
        return float(self.male.sum() + self.female.sum())


_MIGRATION_DEFAULT_SENTINEL: np.ndarray = np.zeros(0, dtype=float)


@dataclass(frozen=True, slots=True)
class DemographicRates:
    """Tier B fertility / mortality / migration rate set.

    All arrays are ``(max_age + 1,)`` shaped except :attr:`asfr`, which is
    only meaningful in the reproductive age range and is zero-padded
    elsewhere by convention. Mortality rates are annual probability of
    death within the age year; migration entries are net (positive
    inflow, negative outflow) absolute counts to be added after mortality.

    When ``net_migration_male`` / ``net_migration_female`` are not
    supplied, they default to a zero array **whose shape is derived from
    the asfr length at construction time**, so a non-default
    ``max_age`` choice transparently produces the right migration shape.

    The :attr:`sex_ratio_at_birth` is the male-to-female ratio of newborns
    (Korea historical mean ~1.05). Construction validates
    ``[0, 1]`` for asmr, ``[0, +inf)`` for asfr, and a positive
    sex_ratio_at_birth.
    """

    asfr: np.ndarray
    asmr_male: np.ndarray
    asmr_female: np.ndarray
    net_migration_male: np.ndarray = field(
        default_factory=lambda: _MIGRATION_DEFAULT_SENTINEL
    )
    net_migration_female: np.ndarray = field(
        default_factory=lambda: _MIGRATION_DEFAULT_SENTINEL
    )
    sex_ratio_at_birth: float = DEFAULT_SEX_RATIO_AT_BIRTH

    def __post_init__(self) -> None:
        asfr = _as_float_array(self.asfr)
        asmr_m = _as_float_array(self.asmr_male)
        asmr_f = _as_float_array(self.asmr_female)
        # Sentinel-driven migration default: when either migration arg
        # is omitted (sentinel zero-length array), broadcast a zero
        # array shaped from asfr so callers with non-default max_age
        # don't have to remember to supply matching migration arrays.
        raw_mig_m = self.net_migration_male
        raw_mig_f = self.net_migration_female
        if isinstance(raw_mig_m, np.ndarray) and raw_mig_m is _MIGRATION_DEFAULT_SENTINEL:
            mig_m = np.zeros_like(asfr)
        else:
            mig_m = _as_float_array(raw_mig_m)
        if isinstance(raw_mig_f, np.ndarray) and raw_mig_f is _MIGRATION_DEFAULT_SENTINEL:
            mig_f = np.zeros_like(asfr)
        else:
            mig_f = _as_float_array(raw_mig_f)
        shapes = {asfr.shape, asmr_m.shape, asmr_f.shape, mig_m.shape, mig_f.shape}
        if len(shapes) != 1:
            raise ValueError(
                f"all rate arrays must have identical shape (got {shapes})"
            )
        if (asfr < 0).any():
            raise ValueError("asfr must be non-negative")
        if (asmr_m < 0).any() or (asmr_m > 1).any():
            raise ValueError("asmr_male must lie in [0, 1]")
        if (asmr_f < 0).any() or (asmr_f > 1).any():
            raise ValueError("asmr_female must lie in [0, 1]")
        if not isinstance(self.sex_ratio_at_birth, (int, float)) or isinstance(
            self.sex_ratio_at_birth, bool
        ):
            raise TypeError("sex_ratio_at_birth must be a real number")
        if self.sex_ratio_at_birth <= 0:
            raise ValueError(
                f"sex_ratio_at_birth must be positive "
                f"(got {self.sex_ratio_at_birth})"
            )
        # Reproductive-age guard: asfr must be zero outside [15, 50).
        outside = np.r_[asfr[:REPRODUCTIVE_AGE_LO], asfr[REPRODUCTIVE_AGE_HI:]]
        if (outside != 0).any():
            raise ValueError(
                f"asfr must be zero outside ages "
                f"[{REPRODUCTIVE_AGE_LO}, {REPRODUCTIVE_AGE_HI})"
            )
        object.__setattr__(self, "asfr", asfr)
        object.__setattr__(self, "asmr_male", asmr_m)
        object.__setattr__(self, "asmr_female", asmr_f)
        object.__setattr__(self, "net_migration_male", mig_m)
        object.__setattr__(self, "net_migration_female", mig_f)

    @property
    def total_fertility_rate(self) -> float:
        """Sum of single-year ASFR over reproductive ages — the canonical
        TFR. KOSTAT ``합계출산율`` corresponds to this when ASFR is
        denominated per woman per year.
        """

        return float(self.asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI].sum())


class CohortComponentProjector:
    """Pure-numpy deterministic cohort-component projector."""

    def __init__(self, *, max_age: int = DEFAULT_MAX_AGE) -> None:
        if not isinstance(max_age, int) or isinstance(max_age, bool):
            raise TypeError("max_age must be int")
        if max_age < REPRODUCTIVE_AGE_HI:
            raise ValueError(
                f"max_age must be at least {REPRODUCTIVE_AGE_HI} to span the "
                f"reproductive age range (got {max_age})"
            )
        self._max_age = max_age

    @property
    def max_age(self) -> int:
        return self._max_age

    def step(
        self,
        population: CohortPopulation,
        rates: DemographicRates,
    ) -> CohortPopulation:
        """Project ``population`` one year forward under ``rates``.

        Mortality is applied first (each cohort survives at rate
        ``1 - asmr[a]``), then net migration is added, then surviving
        ages are shifted up by one cohort with the open-ended top class
        accumulating into itself. Births enter cohort 0 split by
        :attr:`DemographicRates.sex_ratio_at_birth`.
        """

        if population.max_age != self._max_age:
            raise ValueError(
                f"population.max_age={population.max_age} does not match "
                f"projector.max_age={self._max_age}"
            )
        if rates.asmr_male.shape[0] != self._max_age + 1:
            raise ValueError(
                f"rates length {rates.asmr_male.shape[0]} does not match "
                f"projector.max_age + 1 = {self._max_age + 1}"
            )

        # Survive: pop * (1 - asmr).
        surv_m = population.male * (1.0 - rates.asmr_male)
        surv_f = population.female * (1.0 - rates.asmr_female)

        # Add net migration (after mortality, before age advance).
        surv_m = surv_m + rates.net_migration_male
        surv_f = surv_f + rates.net_migration_female

        # Clamp to non-negative — heavy out-migration could otherwise
        # push small cohorts negative.
        surv_m = np.maximum(surv_m, 0.0)
        surv_f = np.maximum(surv_f, 0.0)

        # Births aggregate over reproductive ages.
        births = float(
            (
                population.female[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI]
                * rates.asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI]
            ).sum()
        )
        srb = rates.sex_ratio_at_birth
        male_births = births * srb / (1.0 + srb)
        female_births = births / (1.0 + srb)

        # Advance ages by one. Last cohort is open-ended (a + 1 collapses
        # back into max_age).
        next_m = np.zeros_like(surv_m)
        next_f = np.zeros_like(surv_f)
        next_m[1:-1] = surv_m[:-2]
        next_f[1:-1] = surv_f[:-2]
        # Open-ended top: max_age cohort = surv[max_age - 1] + surv[max_age].
        next_m[-1] = surv_m[-2] + surv_m[-1]
        next_f[-1] = surv_f[-2] + surv_f[-1]
        # Births enter cohort 0.
        next_m[0] = male_births
        next_f[0] = female_births

        return CohortPopulation(
            year=population.year + 1,
            region_label=population.region_label,
            male=next_m,
            female=next_f,
        )

    def project(
        self,
        initial: CohortPopulation,
        rates: DemographicRates,
        horizon_years: int,
    ) -> tuple[CohortPopulation, ...]:
        """Project ``initial`` forward by ``horizon_years`` consecutive years.

        Returns a tuple of length ``horizon_years`` containing the
        projected populations at years ``initial.year + 1`` through
        ``initial.year + horizon_years`` (inclusive). The initial
        population is **not** included — callers can prepend it if they
        need to keep it.
        """

        if not isinstance(horizon_years, int) or isinstance(horizon_years, bool):
            raise TypeError("horizon_years must be int")
        if horizon_years < 0:
            raise ValueError(
                f"horizon_years must be non-negative (got {horizon_years})"
            )
        if horizon_years == 0:
            return ()
        out: list[CohortPopulation] = []
        current = initial
        for _ in range(horizon_years):
            current = self.step(current, rates)
            out.append(current)
        return tuple(out)


__all__ = [
    "DEFAULT_MAX_AGE",
    "DEFAULT_SEX_RATIO_AT_BIRTH",
    "REPRODUCTIVE_AGE_HI",
    "REPRODUCTIVE_AGE_LO",
    "CohortComponentProjector",
    "CohortPopulation",
    "DemographicRates",
    "Sex",
]
