"""Tests for luvoire.memory.actr_weight (ACT-R base-level activation)."""

from __future__ import annotations

import math

import pytest

from luvoire.memory.actr_weight import (
    DEFAULT_DECAY_EXPONENT,
    actr_retention_weight,
    base_level_activation,
)


def test_empty_uses_returns_neg_infinity_activation() -> None:
    bla = base_level_activation([])
    assert bla.activation == -math.inf
    assert bla.use_count == 0


def test_single_recent_use_gives_positive_or_zero_activation() -> None:
    bla = base_level_activation([1.0])
    # ln(1.0**(-0.5)) = ln(1.0) = 0.0
    assert bla.activation == pytest.approx(0.0)
    assert bla.use_count == 1


def test_many_recent_uses_increases_activation() -> None:
    one = base_level_activation([1.0])
    five = base_level_activation([1.0, 1.0, 1.0, 1.0, 1.0])
    assert five.activation > one.activation


def test_older_uses_decrease_activation() -> None:
    recent = base_level_activation([1.0])
    old = base_level_activation([100.0])
    assert recent.activation > old.activation


def test_higher_decay_exponent_punishes_old_uses_more() -> None:
    soft = base_level_activation([100.0], decay_exponent=0.2)
    sharp = base_level_activation([100.0], decay_exponent=1.0)
    assert soft.activation > sharp.activation


def test_invalid_decay_exponent_rejected() -> None:
    with pytest.raises(ValueError, match="decay_exponent"):
        base_level_activation([1.0], decay_exponent=0.0)


def test_non_positive_age_rejected() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        base_level_activation([0.0, 1.0])


def test_default_decay_exponent_value() -> None:
    assert pytest.approx(0.5) == DEFAULT_DECAY_EXPONENT


def test_retention_weight_in_unit_interval() -> None:
    weight = actr_retention_weight([1.0, 5.0, 30.0])
    assert 0.0 <= weight <= 1.0


def test_retention_weight_zero_for_empty_uses() -> None:
    assert actr_retention_weight([]) == 0.0


def test_retention_weight_higher_for_more_uses() -> None:
    sparse = actr_retention_weight([10.0])
    dense = actr_retention_weight([10.0, 10.0, 10.0, 10.0, 10.0])
    assert dense > sparse


def test_retention_weight_lower_for_older_uses() -> None:
    fresh = actr_retention_weight([2.0])
    stale = actr_retention_weight([200.0])
    assert fresh > stale


def test_dataclass_is_frozen() -> None:
    bla = base_level_activation([1.0])
    with pytest.raises((AttributeError, TypeError)):
        bla.activation = 0.0  # type: ignore[misc]


def test_minimum_age_clamping_avoids_division_singularity() -> None:
    bla = base_level_activation([1e-12])
    assert math.isfinite(bla.activation)
