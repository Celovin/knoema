"""Tests for luvoire.demography.counterfactual — scenario perturbations."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.demography.counterfactual import (
    KOSTAT_REFERENCE_TRIPLE,
    CounterfactualScenarioEngine,
    RatePerturbation,
)
from luvoire.demography.projector import (
    DEFAULT_MAX_AGE,
    REPRODUCTIVE_AGE_HI,
    REPRODUCTIVE_AGE_LO,
    CohortPopulation,
    DemographicRates,
)


def _baseline_rates() -> DemographicRates:
    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] = 0.04
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr[60:] = 0.02
    asmr[80:] = 0.05
    return DemographicRates(asfr=asfr, asmr_male=asmr, asmr_female=asmr)


def _baseline_population() -> CohortPopulation:
    return CohortPopulation(
        year=2026,
        region_label="서울특별시 강남구",
        male=np.full(DEFAULT_MAX_AGE + 1, 1000.0),
        female=np.full(DEFAULT_MAX_AGE + 1, 1000.0),
    )


# --- RatePerturbation ----------------------------------------------------


def test_perturbation_identity_round_trips() -> None:
    baseline = _baseline_rates()
    pert = RatePerturbation()  # all 1.0
    perturbed = pert.apply(baseline)
    np.testing.assert_array_equal(perturbed.asfr, baseline.asfr)
    np.testing.assert_array_equal(perturbed.asmr_male, baseline.asmr_male)
    np.testing.assert_array_equal(perturbed.asmr_female, baseline.asmr_female)


def test_perturbation_scales_only_reproductive_asfr() -> None:
    baseline = _baseline_rates()
    pert = RatePerturbation(fertility_scale=2.0)
    perturbed = pert.apply(baseline)
    np.testing.assert_array_equal(
        perturbed.asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI],
        baseline.asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] * 2.0,
    )
    np.testing.assert_array_equal(
        perturbed.asfr[:REPRODUCTIVE_AGE_LO],
        baseline.asfr[:REPRODUCTIVE_AGE_LO],
    )


def test_perturbation_clamps_mortality_to_unit() -> None:
    baseline = _baseline_rates()
    pert = RatePerturbation(mortality_scale=100.0)
    perturbed = pert.apply(baseline)
    assert (perturbed.asmr_male <= 1.0).all()
    assert (perturbed.asmr_male >= 0.0).all()


def test_perturbation_negative_migration_reverses_sign() -> None:
    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    mig = np.full(DEFAULT_MAX_AGE + 1, 10.0)
    baseline = DemographicRates(
        asfr=asfr,
        asmr_male=asmr,
        asmr_female=asmr,
        net_migration_male=mig,
        net_migration_female=mig,
    )
    pert = RatePerturbation(migration_scale=-1.0)
    perturbed = pert.apply(baseline)
    np.testing.assert_array_equal(perturbed.net_migration_male, -mig)


def test_perturbation_rejects_negative_fertility_scale() -> None:
    with pytest.raises(ValueError, match="fertility_scale"):
        RatePerturbation(fertility_scale=-0.1)


def test_perturbation_rejects_non_numeric_migration_scale() -> None:
    with pytest.raises(TypeError, match="migration_scale"):
        RatePerturbation(migration_scale="0.5")  # type: ignore[arg-type]


# --- CounterfactualScenarioEngine ---------------------------------------


def test_engine_runs_kostat_triple_and_orders_results() -> None:
    engine = CounterfactualScenarioEngine()
    results = engine.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates(),
        horizon_years=10,
        scenarios=KOSTAT_REFERENCE_TRIPLE,
    )
    assert len(results) == 3
    labels = [r.label for r in results]
    assert labels == ["low_fertility", "medium_fertility", "high_fertility"]


def test_engine_higher_fertility_yields_larger_year10_total() -> None:
    engine = CounterfactualScenarioEngine()
    results = engine.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates(),
        horizon_years=10,
        scenarios=KOSTAT_REFERENCE_TRIPLE,
    )
    by_label = {r.label: r for r in results}
    low = by_label["low_fertility"].trajectory[-1].total
    medium = by_label["medium_fertility"].trajectory[-1].total
    high = by_label["high_fertility"].trajectory[-1].total
    assert low <= medium <= high


def test_engine_results_include_perturbation_for_audit() -> None:
    engine = CounterfactualScenarioEngine()
    results = engine.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates(),
        horizon_years=2,
        scenarios=KOSTAT_REFERENCE_TRIPLE,
    )
    for r in results:
        assert r.perturbation is not None
        assert isinstance(r.perturbation.fertility_scale, float)


def test_engine_total_population_series_returns_one_value_per_year() -> None:
    engine = CounterfactualScenarioEngine()
    results = engine.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates(),
        horizon_years=5,
        scenarios={"medium": ("fertility", RatePerturbation())},
    )
    series = results[0].total_population_series()
    assert len(series) == 5


def test_engine_rejects_unknown_scenario_kind() -> None:
    engine = CounterfactualScenarioEngine()
    with pytest.raises(ValueError, match="unknown scenario kind"):
        engine.run(
            initial=_baseline_population(),
            baseline_rates=_baseline_rates(),
            horizon_years=1,
            scenarios={"weird": ("nonsense", RatePerturbation())},  # type: ignore[dict-item]
        )


def test_engine_rejects_empty_scenario_label() -> None:
    engine = CounterfactualScenarioEngine()
    with pytest.raises(ValueError, match="non-empty string"):
        engine.run(
            initial=_baseline_population(),
            baseline_rates=_baseline_rates(),
            horizon_years=1,
            scenarios={"": ("fertility", RatePerturbation())},
        )


def test_engine_is_deterministic() -> None:
    """Two engines, byte-identical inputs → byte-identical trajectories."""

    engine_a = CounterfactualScenarioEngine()
    engine_b = CounterfactualScenarioEngine()
    results_a = engine_a.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates(),
        horizon_years=10,
        scenarios=KOSTAT_REFERENCE_TRIPLE,
    )
    results_b = engine_b.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates(),
        horizon_years=10,
        scenarios=KOSTAT_REFERENCE_TRIPLE,
    )
    for ra, rb in zip(results_a, results_b, strict=True):
        for pa, pb in zip(ra.trajectory, rb.trajectory, strict=True):
            np.testing.assert_array_equal(pa.male, pb.male)
            np.testing.assert_array_equal(pa.female, pb.female)
