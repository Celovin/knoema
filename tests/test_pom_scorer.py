"""Tests for :mod:`luvoire.pom.scorer`."""

from __future__ import annotations

import pytest

from luvoire.pom.gates import GateResult
from luvoire.pom.scorer import PomScore, score_pom


def _result(
    pattern_id: str,
    distance: float,
    *,
    passed: bool | None = None,
    weight: float = 1.0,
) -> GateResult:
    return GateResult(
        pattern_id=pattern_id,
        ks_distance=distance,
        passed=distance <= 0.1 if passed is None else passed,
        weight=weight,
    )


def test_score_pom_perfect_match_yields_one() -> None:
    results = (
        _result("G1", 0.0, passed=True),
        _result("G2", 0.0, passed=True),
        _result("G3", 0.0, passed=True),
    )
    score = score_pom(results)
    assert isinstance(score, PomScore)
    assert score.composite_score == pytest.approx(1.0, abs=1e-12)
    assert score.all_gates_passed is True
    assert score.gate_results == results


def test_score_pom_worst_case_yields_zero() -> None:
    results = (
        _result("G1", 1.0, passed=False),
        _result("G2", 1.0, passed=False),
    )
    score = score_pom(results)
    assert score.composite_score == pytest.approx(0.0, abs=1e-12)
    assert score.all_gates_passed is False


def test_score_pom_weighted_mean_distance() -> None:
    # KS distances 0.1 and 0.5 with weights 3 and 1 ->
    # weighted mean = (0.3 + 0.5) / 4 = 0.2 -> score = 0.8
    results = (
        _result("G1", 0.1, weight=3.0, passed=True),
        _result("G2", 0.5, weight=1.0, passed=False),
    )
    score = score_pom(results)
    assert score.composite_score == pytest.approx(0.8, abs=1e-12)
    assert score.all_gates_passed is False


def test_score_pom_monotonic_in_individual_distance() -> None:
    base = (
        _result("G1", 0.1, passed=True),
        _result("G2", 0.1, passed=True),
        _result("G3", 0.1, passed=True),
    )
    worse = (
        _result("G1", 0.1, passed=True),
        _result("G2", 0.2, passed=False),
        _result("G3", 0.1, passed=True),
    )
    base_score = score_pom(base)
    worse_score = score_pom(worse)
    assert worse_score.composite_score < base_score.composite_score


def test_score_pom_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="at least one"):
        score_pom(())


def test_score_pom_rejects_non_positive_weight() -> None:
    bad = (_result("G1", 0.1, weight=0.0, passed=True),)
    with pytest.raises(ValueError, match="weight must be positive"):
        score_pom(bad)


def test_score_pom_all_passed_requires_every_gate_passed() -> None:
    results = (
        _result("G1", 0.0, passed=True),
        _result("G2", 0.0, passed=False),
    )
    score = score_pom(results)
    assert score.all_gates_passed is False
    # Score itself is still 1.0 because all distances are zero.
    assert score.composite_score == pytest.approx(1.0, abs=1e-12)


def test_score_pom_clamps_floating_point_drift() -> None:
    # Distances slightly above 1.0 should not push the score below 0.0.
    results = (_result("G1", 1.0 + 1e-15, passed=False),)
    score = score_pom(results)
    assert 0.0 <= score.composite_score <= 1.0
