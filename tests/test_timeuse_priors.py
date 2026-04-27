"""Tests for :mod:`luvoire.timeuse.priors`."""

from __future__ import annotations

from pathlib import Path

import pytest

from luvoire.timeuse.priors import (
    ACTIVITY_CODES,
    ActivityPrior,
    EmpiricalCdfSampler,
    StrataKey,
    load_priors_from_json,
)

FIXTURE = Path(__file__).parent / "fixtures" / "timeuse" / "synthetic_priors_v1.json"


def _valid_weights() -> dict[str, float]:
    return {
        "sleep": 0.32,
        "work_or_school": 0.34,
        "commute": 0.06,
        "meals": 0.08,
        "leisure": 0.13,
        "care": 0.04,
        "other": 0.03,
    }


def _valid_strata() -> StrataKey:
    return StrataKey(day_type="weekday", age_band="adult", occupation="employed")


def test_activity_codes_canonical_order() -> None:
    assert ACTIVITY_CODES == (
        "sleep",
        "work_or_school",
        "commute",
        "meals",
        "leisure",
        "care",
        "other",
    )


def test_strata_key_rejects_invalid_day_type() -> None:
    with pytest.raises(ValueError, match="day_type"):
        StrataKey(day_type="bogus", age_band="adult", occupation="employed")  # type: ignore[arg-type]


def test_strata_key_rejects_invalid_age_band() -> None:
    with pytest.raises(ValueError, match="age_band"):
        StrataKey(day_type="weekday", age_band="ancient", occupation="employed")  # type: ignore[arg-type]


def test_strata_key_rejects_invalid_occupation() -> None:
    with pytest.raises(ValueError, match="occupation"):
        StrataKey(day_type="weekday", age_band="adult", occupation="warlord")  # type: ignore[arg-type]


def test_activity_prior_accepts_valid_weights() -> None:
    prior = ActivityPrior(
        strata=_valid_strata(), weights=_valid_weights(), source="unit-test"
    )
    assert sum(prior.ordered_weights) == pytest.approx(1.0, abs=1e-9)


def test_activity_prior_rejects_missing_code() -> None:
    weights = _valid_weights()
    del weights["other"]
    with pytest.raises(ValueError, match="canonical activity codes"):
        ActivityPrior(strata=_valid_strata(), weights=weights, source="unit-test")  # type: ignore[arg-type]


def test_activity_prior_rejects_extra_code() -> None:
    weights = _valid_weights()
    weights["studying"] = 0.0  # type: ignore[index]
    with pytest.raises(ValueError, match="canonical activity codes"):
        ActivityPrior(strata=_valid_strata(), weights=weights, source="unit-test")  # type: ignore[arg-type]


def test_activity_prior_rejects_value_above_one() -> None:
    weights = _valid_weights()
    weights["sleep"] = 1.5
    weights["work_or_school"] = -0.16  # keep sum = 1.0 to isolate the bound check
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        ActivityPrior(strata=_valid_strata(), weights=weights, source="unit-test")


def test_activity_prior_rejects_negative_weight() -> None:
    weights = _valid_weights()
    weights["sleep"] = -0.01
    weights["work_or_school"] = 0.35  # keep sum = 1.0
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        ActivityPrior(strata=_valid_strata(), weights=weights, source="unit-test")


def test_activity_prior_rejects_sum_off_target() -> None:
    weights = _valid_weights()
    weights["leisure"] = 0.50
    with pytest.raises(ValueError, match=r"sum to 1\.0"):
        ActivityPrior(strata=_valid_strata(), weights=weights, source="unit-test")


def test_activity_prior_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="source"):
        ActivityPrior(strata=_valid_strata(), weights=_valid_weights(), source="")


def test_sampler_determinism_for_same_seed() -> None:
    prior = ActivityPrior(
        strata=_valid_strata(), weights=_valid_weights(), source="unit-test"
    )
    s1 = EmpiricalCdfSampler(prior, seed=42)
    s2 = EmpiricalCdfSampler(prior, seed=42)
    seq1 = s1.sample_many(100)
    seq2 = s2.sample_many(100)
    assert seq1 == seq2
    assert len(seq1) == 100


def test_sampler_differs_across_seeds() -> None:
    prior = ActivityPrior(
        strata=_valid_strata(), weights=_valid_weights(), source="unit-test"
    )
    s1 = EmpiricalCdfSampler(prior, seed=1)
    s2 = EmpiricalCdfSampler(prior, seed=2)
    assert s1.sample_many(100) != s2.sample_many(100)


def test_sampler_sample_one_returns_canonical_code() -> None:
    prior = ActivityPrior(
        strata=_valid_strata(), weights=_valid_weights(), source="unit-test"
    )
    sampler = EmpiricalCdfSampler(prior, seed=7)
    drawn = sampler.sample_one()
    assert drawn in ACTIVITY_CODES


def test_sampler_sample_many_zero_returns_empty() -> None:
    prior = ActivityPrior(
        strata=_valid_strata(), weights=_valid_weights(), source="unit-test"
    )
    sampler = EmpiricalCdfSampler(prior, seed=0)
    assert sampler.sample_many(0) == ()


def test_sampler_rejects_negative_n() -> None:
    prior = ActivityPrior(
        strata=_valid_strata(), weights=_valid_weights(), source="unit-test"
    )
    sampler = EmpiricalCdfSampler(prior, seed=0)
    with pytest.raises(ValueError, match="non-negative"):
        sampler.sample_many(-1)


def test_sampler_concentrated_prior_returns_only_dominant_code() -> None:
    weights: dict[str, float] = dict.fromkeys(ACTIVITY_CODES, 0.0)
    weights["sleep"] = 1.0
    prior = ActivityPrior(
        strata=_valid_strata(), weights=weights, source="unit-test"  # type: ignore[arg-type]
    )
    sampler = EmpiricalCdfSampler(prior, seed=123)
    assert all(code == "sleep" for code in sampler.sample_many(50))


def test_load_priors_from_json_roundtrip() -> None:
    priors = load_priors_from_json(FIXTURE)
    assert len(priors) == 2
    weekday = priors[0]
    assert weekday.strata == StrataKey(
        day_type="weekday", age_band="adult", occupation="employed"
    )
    assert weekday.weights["sleep"] == pytest.approx(0.32)
    assert weekday.revision == "2026-04-27"
    assert weekday.source == "synthetic-luvoire-fixture"
    weekend = priors[1]
    assert weekend.strata.day_type == "weekend"
    assert weekend.strata.occupation == "student"
    # Each loaded prior must satisfy the same invariants as constructor-built ones.
    for prior in priors:
        assert sum(prior.ordered_weights) == pytest.approx(1.0, abs=1e-9)
