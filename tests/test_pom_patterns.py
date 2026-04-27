"""Tests for :mod:`luvoire.pom.patterns`."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.pom.patterns import (
    Pattern,
    activity_diversity_pattern,
    hotspot_distribution_pattern,
    pattern_from_samples,
    time_of_day_pattern,
)


def test_pattern_target_must_sum_to_one() -> None:
    Pattern(
        pattern_id="p",
        description="ok",
        target_distribution=(0.25, 0.25, 0.25, 0.25),
        bins=4,
    )


def test_pattern_rejects_distribution_not_summing_to_one() -> None:
    with pytest.raises(ValueError, match=r"sum to 1\.0"):
        Pattern(
            pattern_id="p",
            description="bad",
            target_distribution=(0.3, 0.3, 0.3, 0.3),
            bins=4,
        )


def test_pattern_rejects_negative_probabilities() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Pattern(
            pattern_id="p",
            description="bad",
            target_distribution=(-0.1, 0.5, 0.6),
            bins=3,
        )


def test_pattern_rejects_bin_count_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match bins"):
        Pattern(
            pattern_id="p",
            description="bad",
            target_distribution=(0.5, 0.5),
            bins=3,
        )


def test_pattern_rejects_empty_pattern_id() -> None:
    with pytest.raises(ValueError, match="pattern_id"):
        Pattern(
            pattern_id="",
            description="bad",
            target_distribution=(1.0,),
            bins=1,
        )


def test_pattern_rejects_non_positive_bins() -> None:
    with pytest.raises(ValueError, match="bins must be positive"):
        Pattern(
            pattern_id="p",
            description="bad",
            target_distribution=(),
            bins=0,
        )


def test_pattern_target_array_returns_float_array() -> None:
    pattern = Pattern(
        pattern_id="p",
        description="ok",
        target_distribution=(0.5, 0.5),
        bins=2,
    )
    arr = pattern.target_array()
    assert arr.dtype == np.float64
    assert arr.shape == (2,)
    assert np.isclose(arr.sum(), 1.0)


def test_pattern_from_samples_uniform_input() -> None:
    rng = np.random.default_rng(42)
    samples = rng.uniform(0.0, 1.0, size=10_000)
    pattern = pattern_from_samples(
        "uniform_test",
        samples,
        bins=10,
        description="uniform check",
    )
    assert pattern.bins == 10
    arr = pattern.target_array()
    # Each bin should hold ~10% of the mass.
    assert np.allclose(arr, np.full(10, 0.1), atol=0.02)
    assert abs(arr.sum() - 1.0) < 1e-6


def test_pattern_from_samples_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one value"):
        pattern_from_samples(
            "p",
            np.asarray([], dtype=float),
            bins=4,
            description="empty",
        )


def test_pattern_from_samples_rejects_non_positive_bins() -> None:
    with pytest.raises(ValueError, match="bins must be positive"):
        pattern_from_samples(
            "p",
            np.asarray([1.0, 2.0, 3.0]),
            bins=0,
            description="bad",
        )


def test_pattern_from_samples_collapses_identical_values() -> None:
    samples = np.full(50, 7.0)
    pattern = pattern_from_samples(
        "p",
        samples,
        bins=4,
        description="collapsed",
    )
    arr = pattern.target_array()
    assert pytest.approx(arr[0]) == 1.0
    assert np.all(arr[1:] == 0.0)


def test_pattern_from_samples_rejects_non_finite() -> None:
    with pytest.raises(ValueError, match="finite"):
        pattern_from_samples(
            "p",
            np.asarray([1.0, np.nan, 3.0]),
            bins=3,
            description="bad",
        )


def test_time_of_day_pattern_factory() -> None:
    target = np.full(24, 1.0 / 24.0)
    pattern = time_of_day_pattern(target)
    assert pattern.pattern_id == "G1_time_of_day"
    assert pattern.bins == 24
    assert abs(sum(pattern.target_distribution) - 1.0) < 1e-6


def test_activity_diversity_pattern_factory() -> None:
    target = np.array([0.5, 0.3, 0.2])
    pattern = activity_diversity_pattern(target)
    assert pattern.pattern_id == "G2_activity_diversity"
    assert pattern.bins == 3
    assert pytest.approx(sum(pattern.target_distribution)) == 1.0


def test_hotspot_distribution_pattern_factory() -> None:
    # Power-law-ish synthetic structural reference.
    raw = np.array([0.5, 0.25, 0.125, 0.0625, 0.0625])
    pattern = hotspot_distribution_pattern(raw)
    assert pattern.pattern_id == "G3_hotspot_distribution"
    assert pattern.bins == 5
    assert "synthetic" in pattern.description.lower()
