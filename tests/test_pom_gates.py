"""Tests for :mod:`luvoire.pom.gates`."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.pom.gates import (
    GateConfig,
    GateResult,
    evaluate_gate,
    evaluate_three_gates,
)
from luvoire.pom.patterns import Pattern


def _uniform_pattern(bins: int, pattern_id: str = "uniform") -> Pattern:
    return Pattern(
        pattern_id=pattern_id,
        description="uniform",
        target_distribution=tuple([1.0 / bins] * bins),
        bins=bins,
    )


def _point_mass_pattern(bins: int, pattern_id: str = "point_mass") -> Pattern:
    target = [0.0] * bins
    target[0] = 1.0
    return Pattern(
        pattern_id=pattern_id,
        description="point mass",
        target_distribution=tuple(target),
        bins=bins,
    )


def test_gate_config_rejects_threshold_above_one() -> None:
    pattern = _uniform_pattern(4)
    with pytest.raises(ValueError, match="ks_threshold"):
        GateConfig(pattern=pattern, ks_threshold=1.5)


def test_gate_config_rejects_negative_threshold() -> None:
    pattern = _uniform_pattern(4)
    with pytest.raises(ValueError, match="ks_threshold"):
        GateConfig(pattern=pattern, ks_threshold=-0.1)


def test_gate_config_rejects_non_positive_weight() -> None:
    pattern = _uniform_pattern(4)
    with pytest.raises(ValueError, match="weight"):
        GateConfig(pattern=pattern, ks_threshold=0.1, weight=0.0)


def test_uniform_simulated_against_uniform_target_yields_zero_distance() -> None:
    rng = np.random.default_rng(0)
    bins = 10
    pattern = _uniform_pattern(bins)
    # Construct a sample whose binned histogram is exactly uniform.
    samples = np.array(
        [(i + 0.5) / bins for i in range(bins) for _ in range(100)],
        dtype=float,
    )
    rng.shuffle(samples)
    config = GateConfig(pattern=pattern, ks_threshold=0.05)
    result = evaluate_gate(samples, config)
    assert result.ks_distance == pytest.approx(0.0, abs=1e-9)
    assert result.passed is True
    assert result.pattern_id == "uniform"
    assert result.weight == 1.0


def test_point_mass_against_uniform_target_yields_distance_close_to_one() -> None:
    bins = 5
    pattern = _uniform_pattern(bins)
    # All samples sit in the first bin only, so the histogram is a point mass.
    samples = np.full(200, 0.0, dtype=float)
    config = GateConfig(pattern=pattern, ks_threshold=0.5)
    result = evaluate_gate(samples, config)
    # Discrete KS distance for point-mass vs. uniform is (bins-1)/bins.
    assert result.ks_distance == pytest.approx((bins - 1) / bins, abs=1e-9)
    assert result.passed is False


def test_identical_simulated_and_target_pass() -> None:
    bins = 4
    pattern = _uniform_pattern(bins)
    samples = np.array(
        [(i + 0.5) / bins for i in range(bins) for _ in range(50)],
        dtype=float,
    )
    config = GateConfig(pattern=pattern, ks_threshold=0.0)
    result = evaluate_gate(samples, config)
    assert result.ks_distance == pytest.approx(0.0, abs=1e-12)
    assert result.passed is True


def test_threshold_boundary_just_below_passes() -> None:
    bins = 5
    pattern = _uniform_pattern(bins)
    # Construct a small deliberate skew: 30% in first bin, 17.5% in others.
    samples = np.concatenate(
        [
            np.full(30, 0.05),
            np.full(17, 0.25),
            np.full(18, 0.45),
            np.full(17, 0.65),
            np.full(18, 0.85),
        ]
    )
    # Compute the actual distance once, then place threshold just above it.
    config_loose = GateConfig(pattern=pattern, ks_threshold=1.0)
    distance = evaluate_gate(samples, config_loose).ks_distance
    config_tight_pass = GateConfig(
        pattern=pattern, ks_threshold=distance + 1e-9
    )
    config_tight_fail = GateConfig(
        pattern=pattern, ks_threshold=max(distance - 1e-6, 0.0)
    )
    assert evaluate_gate(samples, config_tight_pass).passed is True
    assert evaluate_gate(samples, config_tight_fail).passed is False


def test_evaluate_gate_is_deterministic() -> None:
    bins = 8
    pattern = _uniform_pattern(bins)
    samples = np.linspace(0.0, 1.0, 200)
    config = GateConfig(pattern=pattern, ks_threshold=0.1)
    result_a = evaluate_gate(samples, config)
    result_b = evaluate_gate(samples, config)
    assert result_a == result_b


def test_evaluate_gate_rejects_empty_samples() -> None:
    pattern = _uniform_pattern(4)
    config = GateConfig(pattern=pattern, ks_threshold=0.1)
    with pytest.raises(ValueError, match="at least one value"):
        evaluate_gate(np.asarray([], dtype=float), config)


def test_evaluate_gate_single_bin_pattern() -> None:
    pattern = Pattern(
        pattern_id="single",
        description="single bin",
        target_distribution=(1.0,),
        bins=1,
    )
    samples = np.array([1.0, 2.0, 3.0])
    config = GateConfig(pattern=pattern, ks_threshold=0.0)
    result = evaluate_gate(samples, config)
    assert result.ks_distance == pytest.approx(0.0, abs=1e-12)
    assert result.passed is True


def test_evaluate_gate_rejects_non_finite_samples() -> None:
    pattern = _uniform_pattern(3)
    config = GateConfig(pattern=pattern, ks_threshold=0.1)
    with pytest.raises(ValueError, match="finite"):
        evaluate_gate(np.array([1.0, np.inf, 2.0]), config)


def test_evaluate_three_gates_returns_three_results() -> None:
    pattern_g1 = _uniform_pattern(4, pattern_id="G1")
    pattern_g2 = _uniform_pattern(4, pattern_id="G2")
    pattern_g3 = _point_mass_pattern(4, pattern_id="G3")
    sim = np.array([(i + 0.5) / 4 for i in range(4) for _ in range(25)])
    pm = np.zeros(50, dtype=float)
    configs = (
        GateConfig(pattern=pattern_g1, ks_threshold=0.05),
        GateConfig(pattern=pattern_g2, ks_threshold=0.05),
        GateConfig(pattern=pattern_g3, ks_threshold=0.05),
    )
    results = evaluate_three_gates(sim, sim, pm, configs)
    assert len(results) == 3
    assert all(isinstance(r, GateResult) for r in results)
    assert results[0].pattern_id == "G1"
    assert results[2].pattern_id == "G3"
    assert results[2].ks_distance == pytest.approx(0.0, abs=1e-12)


def test_ks_distance_degenerate_simulated_vs_spread_target() -> None:
    """Audit-coverage: simulated samples collapse to bin 0 vs spread target."""

    spread = _uniform_pattern(5, pattern_id="spread")
    point_samples = np.zeros(40, dtype=float)
    config = GateConfig(pattern=spread, ks_threshold=0.9)
    result = evaluate_gate(point_samples, config)
    # All-mass-in-bin-0 vs uniform-over-5-bins gives KS = 4/5 = 0.8.
    assert result.ks_distance == pytest.approx(0.8, abs=1e-9)
    assert result.passed is True


def test_gate_passes_when_distance_equals_threshold() -> None:
    """Audit-coverage: gate boundary is inclusive (distance == threshold passes)."""

    pattern = _uniform_pattern(2, pattern_id="boundary")
    point_samples = np.zeros(8, dtype=float)
    # KS distance for all-mass-bin-0 vs uniform-over-2 is exactly 0.5.
    config = GateConfig(pattern=pattern, ks_threshold=0.5)
    result = evaluate_gate(point_samples, config)
    assert result.ks_distance == pytest.approx(0.5, abs=1e-9)
    assert result.passed is True
