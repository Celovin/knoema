"""Tests for luvoire.demography.projector — cohort-component projector."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.demography.projector import (
    DEFAULT_MAX_AGE,
    REPRODUCTIVE_AGE_HI,
    REPRODUCTIVE_AGE_LO,
    CohortComponentProjector,
    CohortPopulation,
    DemographicRates,
)


def _flat_rates(
    *,
    asfr_value: float = 0.05,
    asmr_value: float = 0.005,
    max_age: int = DEFAULT_MAX_AGE,
) -> DemographicRates:
    asfr = np.zeros(max_age + 1)
    asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] = asfr_value
    asmr = np.full(max_age + 1, asmr_value)
    return DemographicRates(asfr=asfr, asmr_male=asmr, asmr_female=asmr)


def _flat_population(
    *,
    year: int = 2026,
    region_label: str = "서울특별시 강남구",
    count_per_age: float = 1000.0,
    max_age: int = DEFAULT_MAX_AGE,
) -> CohortPopulation:
    return CohortPopulation(
        year=year,
        region_label=region_label,
        male=np.full(max_age + 1, count_per_age),
        female=np.full(max_age + 1, count_per_age),
    )


# --- CohortPopulation ----------------------------------------------------


def test_cohort_population_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        CohortPopulation(
            year=2026,
            region_label="서울특별시 강남구",
            male=np.array([-1.0, 1.0]),
            female=np.array([1.0, 1.0]),
        )


def test_cohort_population_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same shape"):
        CohortPopulation(
            year=2026,
            region_label="서울특별시 강남구",
            male=np.zeros(10),
            female=np.zeros(20),
        )


def test_cohort_population_rejects_empty_region_label() -> None:
    with pytest.raises(ValueError, match="region_label"):
        CohortPopulation(
            year=2026,
            region_label="",
            male=np.zeros(10),
            female=np.zeros(10),
        )


def test_cohort_population_total_sums_both_sexes() -> None:
    pop = _flat_population(count_per_age=100.0)
    assert pop.total == pytest.approx(2.0 * 100.0 * (DEFAULT_MAX_AGE + 1))


# --- DemographicRates ----------------------------------------------------


def test_rates_reject_asfr_outside_reproductive_range() -> None:
    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asfr[10] = 0.05  # below REPRODUCTIVE_AGE_LO
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    with pytest.raises(ValueError, match="asfr must be zero outside"):
        DemographicRates(asfr=asfr, asmr_male=asmr, asmr_female=asmr)


def test_rates_reject_asmr_above_one() -> None:
    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr[80] = 1.5
    with pytest.raises(ValueError, match=r"asmr_male must lie in \[0, 1\]"):
        DemographicRates(asfr=asfr, asmr_male=asmr, asmr_female=np.zeros_like(asmr))


def test_rates_reject_negative_sex_ratio() -> None:
    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    with pytest.raises(ValueError, match="sex_ratio_at_birth"):
        DemographicRates(
            asfr=asfr,
            asmr_male=asmr,
            asmr_female=asmr,
            sex_ratio_at_birth=-1.0,
        )


def test_rates_total_fertility_rate_is_sum_over_reproductive_ages() -> None:
    rates = _flat_rates(asfr_value=0.05)
    expected = 0.05 * (REPRODUCTIVE_AGE_HI - REPRODUCTIVE_AGE_LO)
    assert rates.total_fertility_rate == pytest.approx(expected)


# --- Projector -----------------------------------------------------------


def test_projector_step_advances_year_by_one() -> None:
    pop = _flat_population(year=2026)
    rates = _flat_rates()
    proj = CohortComponentProjector()
    nxt = proj.step(pop, rates)
    assert nxt.year == 2027


def test_projector_step_preserves_region_label() -> None:
    pop = _flat_population(region_label="부산광역시 중구")
    rates = _flat_rates()
    proj = CohortComponentProjector()
    nxt = proj.step(pop, rates)
    assert nxt.region_label == "부산광역시 중구"


def test_projector_zero_rates_yields_aging_only() -> None:
    """With asmr=0, asfr=0, no migration: ages shift up by one cohort and
    the open-ended top class accumulates."""

    pop = _flat_population(count_per_age=1000.0)
    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    rates = DemographicRates(asfr=asfr, asmr_male=asmr, asmr_female=asmr)
    proj = CohortComponentProjector()
    nxt = proj.step(pop, rates)
    # No births and zero mortality → cohort 0 is empty.
    assert nxt.male[0] == pytest.approx(0.0)
    assert nxt.female[0] == pytest.approx(0.0)
    # Open-ended top accumulates two cohorts (max_age and max_age - 1).
    assert nxt.male[-1] == pytest.approx(2.0 * 1000.0)
    # Total population is conserved.
    assert nxt.total == pytest.approx(pop.total)


def test_projector_births_split_by_sex_ratio() -> None:
    """Births enter cohort 0 split by sex_ratio_at_birth."""

    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] = 0.05
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    rates = DemographicRates(
        asfr=asfr,
        asmr_male=asmr,
        asmr_female=asmr,
        sex_ratio_at_birth=1.0,  # exactly even split for the test
    )
    pop = _flat_population(count_per_age=1000.0)
    proj = CohortComponentProjector()
    nxt = proj.step(pop, rates)
    assert nxt.male[0] == pytest.approx(nxt.female[0])


def test_projector_high_mortality_reduces_total() -> None:
    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr_low = np.full(DEFAULT_MAX_AGE + 1, 0.01)
    asmr_high = np.full(DEFAULT_MAX_AGE + 1, 0.10)
    rates_low = DemographicRates(asfr=asfr, asmr_male=asmr_low, asmr_female=asmr_low)
    rates_high = DemographicRates(asfr=asfr, asmr_male=asmr_high, asmr_female=asmr_high)
    pop = _flat_population()
    proj = CohortComponentProjector()
    nxt_low = proj.step(pop, rates_low)
    nxt_high = proj.step(pop, rates_high)
    assert nxt_high.total < nxt_low.total


def test_projector_full_horizon_returns_correct_length() -> None:
    pop = _flat_population()
    rates = _flat_rates()
    proj = CohortComponentProjector()
    trajectory = proj.project(pop, rates, horizon_years=5)
    assert len(trajectory) == 5
    assert trajectory[0].year == pop.year + 1
    assert trajectory[-1].year == pop.year + 5


def test_projector_horizon_zero_returns_empty_tuple() -> None:
    pop = _flat_population()
    rates = _flat_rates()
    proj = CohortComponentProjector()
    assert proj.project(pop, rates, horizon_years=0) == ()


def test_projector_rejects_negative_horizon() -> None:
    pop = _flat_population()
    rates = _flat_rates()
    proj = CohortComponentProjector()
    with pytest.raises(ValueError, match="non-negative"):
        proj.project(pop, rates, horizon_years=-1)


def test_projector_is_deterministic() -> None:
    """Same inputs → byte-identical trajectory."""

    pop = _flat_population()
    rates = _flat_rates()
    proj_a = CohortComponentProjector()
    proj_b = CohortComponentProjector()
    traj_a = proj_a.project(pop, rates, horizon_years=10)
    traj_b = proj_b.project(pop, rates, horizon_years=10)
    for pa, pb in zip(traj_a, traj_b, strict=True):
        np.testing.assert_array_equal(pa.male, pb.male)
        np.testing.assert_array_equal(pa.female, pb.female)


def test_projector_rejects_max_age_below_reproductive_range() -> None:
    with pytest.raises(ValueError, match="reproductive age range"):
        CohortComponentProjector(max_age=20)


def test_projector_rejects_population_with_wrong_max_age() -> None:
    pop = CohortPopulation(
        year=2026,
        region_label="서울특별시 강남구",
        male=np.zeros(60),
        female=np.zeros(60),
    )
    rates = _flat_rates()  # default max_age 100
    proj = CohortComponentProjector()
    with pytest.raises(ValueError, match="max_age"):
        proj.step(pop, rates)
