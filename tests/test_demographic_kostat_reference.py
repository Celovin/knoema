"""Synthetic KOSTAT-reference qualitative invariants for the cohort-component
projector.

These tests do **not** consume real KOSTAT 장래인구추계 microdata. They build
synthetic baseline rates anchored to the canonical Korean 2024 reference
(TFR ~0.7, total reproductive-age fertility spread over ages 15-49) and
verify that the projector + counterfactual triple reproduce the *qualitative
patterns* KOSTAT publishes:

- 저위 ≤ 중위 ≤ 고위 fertility ordering (population totals at horizon).
- Sub-replacement TFR (0.7 baseline) yields population decline under the
  low-fertility scenario, and even the high-fertility (x1.15) scenario does
  not cross the replacement level so no growth above baseline is produced.
- Ordering is preserved when the horizon stretches to 50 years.
- Population stays strictly positive over a 30-year horizon (no collapse to
  zero from numerical drift).
- The age pyramid ages under low fertility (60+ share rises).
- Cohort counts remain non-negative under extreme mortality (clamp survives).
- The pinned scenario YAML keeps ``demographic_method`` at Tier A with the
  canonical cohort-component reference.

Source modules under test are **not** modified by this test file; only their
public APIs are exercised.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

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

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_YAML = ROOT / "scenarios" / "seoul_demography_30y" / "scenario.yaml"

BASELINE_TFR_KOREA_2024 = 0.7
REPRODUCTIVE_SPAN = REPRODUCTIVE_AGE_HI - REPRODUCTIVE_AGE_LO  # 35
REPLACEMENT_TFR = 2.1


def _baseline_rates_at_tfr(tfr: float = BASELINE_TFR_KOREA_2024) -> DemographicRates:
    """Build a synthetic baseline rate set anchored at the given TFR.

    ASFR is uniform across the 15-49 reproductive ages so the sum equals
    ``tfr``. Mortality is a stylised step function (low until 60, modest
    rise after 60, sharper rise after 80) chosen to produce demographically
    plausible age pyramids without claiming numeric fidelity to any KOSTAT
    life table.
    """

    asfr = np.zeros(DEFAULT_MAX_AGE + 1)
    asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] = tfr / REPRODUCTIVE_SPAN
    asmr = np.zeros(DEFAULT_MAX_AGE + 1)
    asmr[60:] = 0.02
    asmr[80:] = 0.05
    asmr[95:] = 0.15
    return DemographicRates(asfr=asfr, asmr_male=asmr, asmr_female=asmr)


def _baseline_population() -> CohortPopulation:
    """Synthetic stationary-ish population: 1000 of each sex per single-year age."""

    return CohortPopulation(
        year=2026,
        region_label="서울특별시 강남구",
        male=np.full(DEFAULT_MAX_AGE + 1, 1000.0),
        female=np.full(DEFAULT_MAX_AGE + 1, 1000.0),
    )


def _run_triple(horizon_years: int) -> dict[str, float]:
    """Run the canonical KOSTAT triple at ``horizon_years`` and return totals
    keyed by scenario label at the final year."""

    engine = CounterfactualScenarioEngine()
    results = engine.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates_at_tfr(),
        horizon_years=horizon_years,
        scenarios=KOSTAT_REFERENCE_TRIPLE,
    )
    return {r.label: r.trajectory[-1].total for r in results}


# --- Qualitative ordering ------------------------------------------------


def test_kostat_reference_triple_orders_low_medium_high() -> None:
    totals = _run_triple(horizon_years=30)
    assert totals["low_fertility"] <= totals["medium_fertility"] <= totals["high_fertility"]


def test_kostat_low_fertility_yields_population_decline_under_baseline_07() -> None:
    """At TFR 0.7 baseline, x0.85 fertility is deeply sub-replacement and
    must produce a smaller 30-year total than the starting population.
    """

    initial = _baseline_population()
    totals = _run_triple(horizon_years=30)
    assert totals["low_fertility"] < initial.total


def test_kostat_high_fertility_dampens_decline_but_not_growth() -> None:
    """Effective TFR under high_fertility = 1.15 * 0.7 = 0.805, still well
    below the 2.1 replacement level. The 30-year total must therefore
    remain below the initial baseline population (high fertility dampens
    decline; it does not flip it into growth)."""

    initial = _baseline_population()
    # Assert the algebra holds: high effective TFR is sub-replacement.
    high_effective_tfr = 1.15 * BASELINE_TFR_KOREA_2024
    assert high_effective_tfr < REPLACEMENT_TFR

    totals = _run_triple(horizon_years=30)
    assert totals["high_fertility"] < initial.total


def test_kostat_horizon_extension_preserves_ordering() -> None:
    """KOSTAT publishes 30-, 50-year scenario tables. The qualitative
    low <= medium <= high ordering must not flip when we stretch the
    horizon to 50 years."""

    totals = _run_triple(horizon_years=50)
    assert totals["low_fertility"] <= totals["medium_fertility"] <= totals["high_fertility"]


# --- Canonical label set -------------------------------------------------


def test_kostat_reference_uses_kostat_canonical_label_set() -> None:
    """The reference triple must expose exactly the three canonical KOSTAT
    fertility scenario labels (low/medium/high)."""

    expected = {"low_fertility", "medium_fertility", "high_fertility"}
    assert set(KOSTAT_REFERENCE_TRIPLE.keys()) == expected
    assert len(KOSTAT_REFERENCE_TRIPLE) == 3


# --- Scenario YAML invariants --------------------------------------------


def test_demographic_method_tier_a_locked() -> None:
    """The seoul_demography_30y scenario must keep demographic_method at
    Tier A with the canonical cohort-component code reference, so demo
    runs cannot silently swap in an alternative projector."""

    with SCENARIO_YAML.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    method = doc["parameters"]["demographic_method"]
    assert method["tier"] == "A"
    assert method["ref"] == "code:luvoire.demography.cohort_component.v1"


# --- Aging / pyramid -----------------------------------------------------


def _share_60_plus(pop: CohortPopulation) -> float:
    total = pop.total
    if total <= 0:
        return 0.0
    elders = float(pop.male[60:].sum() + pop.female[60:].sum())
    return float(elders / total)


def test_age_pyramid_aging_under_low_fertility_30y() -> None:
    """Under the low-fertility scenario, the 60+ share at year 30 must
    exceed the baseline year's 60+ share (population aging signature)."""

    initial = _baseline_population()
    initial_share = _share_60_plus(initial)

    engine = CounterfactualScenarioEngine()
    results = engine.run(
        initial=initial,
        baseline_rates=_baseline_rates_at_tfr(),
        horizon_years=30,
        scenarios={"low_fertility": KOSTAT_REFERENCE_TRIPLE["low_fertility"]},
    )
    final = results[0].trajectory[-1]
    assert _share_60_plus(final) > initial_share


# --- Robustness ----------------------------------------------------------


def test_population_total_strictly_positive_after_30y() -> None:
    """No scenario should collapse the synthetic population to zero over
    the 30-year horizon; the projector must remain numerically well-posed."""

    totals = _run_triple(horizon_years=30)
    for label, total in totals.items():
        assert total > 0, f"{label} collapsed to non-positive total {total}"


def test_no_cohort_negative_after_high_mortality() -> None:
    """At extreme mortality_scale (clamped to ASMR <= 1) every cohort
    count must remain non-negative across the full trajectory."""

    engine = CounterfactualScenarioEngine()
    results = engine.run(
        initial=_baseline_population(),
        baseline_rates=_baseline_rates_at_tfr(),
        horizon_years=30,
        scenarios={
            "extreme_mortality": (
                "mortality",
                RatePerturbation(mortality_scale=5.0),
            ),
        },
    )
    for pop in results[0].trajectory:
        assert (pop.male >= 0).all()
        assert (pop.female >= 0).all()
