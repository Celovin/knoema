"""Tier A/B/C parameter validation tests for Scenario DSL v2."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from luvoire.dsl.v2.parameters import (
    TierAParam,
    TierBParam,
    TierCParam,
)


def test_tier_a_accepts_valid_code_ref() -> None:
    param = TierAParam(ref="code:luvoire.theory.rat.v1")
    assert param.tier == "A"
    assert param.ref == "code:luvoire.theory.rat.v1"


def test_tier_a_rejects_inline_value() -> None:
    with pytest.raises(ValidationError):
        TierAParam(ref="code:luvoire.theory.rat.v1", value=0.5)  # type: ignore[call-arg]


def test_tier_a_rejects_malformed_ref() -> None:
    with pytest.raises(ValidationError):
        TierAParam(ref="luvoire.theory.rat.v1")


def test_tier_b_requires_value_or_distribution() -> None:
    with pytest.raises(ValidationError):
        TierBParam(source="KOSTAT 2024")


def test_tier_b_with_value_is_valid() -> None:
    param = TierBParam(source="KOSTAT 2024", value=0.42)
    assert param.value == 0.42


def test_tier_b_with_distribution_is_valid() -> None:
    param = TierBParam(source="KOSTAT 2024", distribution="parquet:data/priors.parquet")
    assert param.distribution == "parquet:data/priors.parquet"


def test_tier_b_range_requires_default() -> None:
    with pytest.raises(ValidationError):
        TierBParam(source="KOSTAT 2024", value=0.42, range=(0.1, 0.9))


def test_tier_b_range_default_in_bounds() -> None:
    param = TierBParam(
        source="KOSTAT 2024",
        value=0.42,
        range=(0.1, 0.9),
        default=0.5,
    )
    assert param.default == 0.5


def test_tier_b_default_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        TierBParam(
            source="KOSTAT 2024",
            value=0.42,
            range=(0.1, 0.9),
            default=1.5,
        )


def test_tier_b_blank_source_rejected() -> None:
    with pytest.raises(ValidationError):
        TierBParam(source="", value=0.42)


def test_tier_c_minimum_valid() -> None:
    param = TierCParam(range=(0.1, 0.9), default=0.5)
    assert param.range == (0.1, 0.9)
    assert param.default == 0.5


def test_tier_c_with_sweep_is_valid() -> None:
    param = TierCParam(range=(0.0, 1.0), default=0.5, sweep=9)
    assert param.sweep == 9


def test_tier_c_sweep_below_minimum_rejected() -> None:
    with pytest.raises(ValidationError):
        TierCParam(range=(0.0, 1.0), default=0.5, sweep=1)


def test_tier_c_default_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        TierCParam(range=(0.1, 0.9), default=1.5)


def test_tier_c_inverted_range_rejected() -> None:
    with pytest.raises(ValidationError):
        TierCParam(range=(0.9, 0.1), default=0.5)
