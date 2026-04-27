"""Tests for luvoire.demography.dp — differential privacy noise layer."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.demography.dp import (
    DpBudget,
    add_dp_noise,
    gaussian_noise_sigma,
    laplace_noise_scale,
)

# --- DpBudget ------------------------------------------------------------


def test_dp_budget_default_delta_is_zero() -> None:
    budget = DpBudget(epsilon=1.0)
    assert budget.delta == 0.0


def test_dp_budget_default_sensitivity_is_one() -> None:
    budget = DpBudget(epsilon=1.0)
    assert budget.sensitivity == 1.0


def test_dp_budget_rejects_zero_epsilon() -> None:
    with pytest.raises(ValueError, match="epsilon"):
        DpBudget(epsilon=0.0)


def test_dp_budget_rejects_negative_epsilon() -> None:
    with pytest.raises(ValueError, match="epsilon"):
        DpBudget(epsilon=-1.0)


def test_dp_budget_rejects_delta_above_one() -> None:
    with pytest.raises(ValueError, match="delta"):
        DpBudget(epsilon=1.0, delta=1.5)


def test_dp_budget_accepts_zero_delta() -> None:
    budget = DpBudget(epsilon=1.0, delta=0.0)
    assert budget.delta == 0.0


def test_dp_budget_rejects_zero_sensitivity() -> None:
    with pytest.raises(ValueError, match="sensitivity"):
        DpBudget(epsilon=1.0, sensitivity=0.0)


def test_dp_budget_is_frozen() -> None:
    budget = DpBudget(epsilon=1.0)
    with pytest.raises(AttributeError):
        budget.epsilon = 2.0  # type: ignore[misc]


# --- Scale / sigma helpers ----------------------------------------------


def test_laplace_scale_is_sensitivity_over_epsilon() -> None:
    budget = DpBudget(epsilon=2.0, sensitivity=4.0)
    assert laplace_noise_scale(budget) == pytest.approx(2.0)


def test_gaussian_sigma_is_correct_calibration() -> None:
    budget = DpBudget(epsilon=1.0, delta=1e-5, sensitivity=1.0)
    expected = float(np.sqrt(2.0 * np.log(1.25 / 1e-5))) / 1.0
    assert gaussian_noise_sigma(budget) == pytest.approx(expected)


def test_gaussian_sigma_requires_positive_delta() -> None:
    budget = DpBudget(epsilon=1.0, delta=0.0)
    with pytest.raises(ValueError, match="delta > 0"):
        gaussian_noise_sigma(budget)


# --- add_dp_noise -------------------------------------------------------


def test_add_dp_noise_laplace_returns_float_array_same_length() -> None:
    counts = np.array([100.0, 200.0, 300.0])
    budget = DpBudget(epsilon=1.0)
    noisy = add_dp_noise(counts, budget=budget, seed=42)
    assert noisy.shape == counts.shape
    assert noisy.dtype == np.float64


def test_add_dp_noise_is_deterministic_under_same_seed() -> None:
    counts = np.array([100.0, 200.0, 300.0])
    budget = DpBudget(epsilon=1.0)
    noisy_a = add_dp_noise(counts, budget=budget, seed=42)
    noisy_b = add_dp_noise(counts, budget=budget, seed=42)
    np.testing.assert_array_equal(noisy_a, noisy_b)


def test_add_dp_noise_diverges_under_different_seeds() -> None:
    counts = np.array([100.0, 200.0, 300.0])
    budget = DpBudget(epsilon=1.0)
    noisy_a = add_dp_noise(counts, budget=budget, seed=1)
    noisy_b = add_dp_noise(counts, budget=budget, seed=2)
    assert not np.array_equal(noisy_a, noisy_b)


def test_add_dp_noise_lower_epsilon_yields_higher_variance() -> None:
    counts = np.full(1000, 100.0)
    strict = DpBudget(epsilon=0.1)
    relaxed = DpBudget(epsilon=10.0)
    strict_noisy = add_dp_noise(counts, budget=strict, seed=42)
    relaxed_noisy = add_dp_noise(counts, budget=relaxed, seed=42)
    assert float(np.var(strict_noisy - counts)) > float(
        np.var(relaxed_noisy - counts)
    )


def test_add_dp_noise_clamps_non_negative_by_default() -> None:
    # Tiny counts with strict epsilon often pushes raw noise negative;
    # the default clamp should keep released values non-negative.
    counts = np.array([1.0, 2.0, 3.0])
    budget = DpBudget(epsilon=0.1)
    noisy = add_dp_noise(counts, budget=budget, seed=1)
    assert (noisy >= 0).all()


def test_add_dp_noise_can_disable_clamp() -> None:
    counts = np.array([0.0])
    budget = DpBudget(epsilon=0.1)
    found_negative = False
    for seed in range(20):
        noisy = add_dp_noise(
            counts, budget=budget, seed=seed, clamp_non_negative=False
        )
        if noisy[0] < 0:
            found_negative = True
            break
    assert found_negative


def test_add_dp_noise_rejects_2d_counts() -> None:
    counts = np.zeros((3, 3))
    budget = DpBudget(epsilon=1.0)
    with pytest.raises(ValueError, match="1-D"):
        add_dp_noise(counts, budget=budget, seed=1)


def test_add_dp_noise_rejects_negative_counts() -> None:
    counts = np.array([1.0, -1.0])
    budget = DpBudget(epsilon=1.0)
    with pytest.raises(ValueError, match="non-negative"):
        add_dp_noise(counts, budget=budget, seed=1)


def test_add_dp_noise_rejects_non_int_seed() -> None:
    counts = np.array([1.0])
    budget = DpBudget(epsilon=1.0)
    with pytest.raises(TypeError, match="seed"):
        add_dp_noise(counts, budget=budget, seed="42")  # type: ignore[arg-type]


def test_add_dp_noise_gaussian_mechanism_works() -> None:
    counts = np.array([100.0, 200.0])
    budget = DpBudget(epsilon=1.0, delta=1e-5)
    noisy = add_dp_noise(counts, budget=budget, mechanism="gaussian", seed=42)
    assert noisy.shape == counts.shape


def test_add_dp_noise_gaussian_requires_positive_delta() -> None:
    counts = np.array([100.0])
    budget = DpBudget(epsilon=1.0, delta=0.0)
    with pytest.raises(ValueError, match="delta > 0"):
        add_dp_noise(counts, budget=budget, mechanism="gaussian", seed=42)


def test_add_dp_noise_rejects_unknown_mechanism() -> None:
    counts = np.array([100.0])
    budget = DpBudget(epsilon=1.0)
    with pytest.raises(ValueError, match="unknown mechanism"):
        add_dp_noise(counts, budget=budget, mechanism="snake", seed=42)  # type: ignore[arg-type]


# --- Integration with CellPopulation aggregates --------------------------


def test_gaussian_sigma_rejects_epsilon_above_one() -> None:
    """Classical Gaussian mechanism only valid for epsilon in (0, 1].

    For larger epsilon the Dwork-Roth Theorem A.1 sigma calibration is
    not a sound DP guarantee; callers must use the analytic Gaussian
    mechanism (Balle & Wang 2018) instead.
    """

    budget = DpBudget(epsilon=2.0, delta=1e-5)
    with pytest.raises(ValueError, match="classical Gaussian"):
        gaussian_noise_sigma(budget)


def test_add_dp_noise_gaussian_rejects_epsilon_above_one() -> None:
    counts = np.array([100.0])
    budget = DpBudget(epsilon=2.0, delta=1e-5)
    with pytest.raises(ValueError, match="classical Gaussian"):
        add_dp_noise(counts, budget=budget, mechanism="gaussian", seed=1)


def test_add_dp_noise_gaussian_at_epsilon_one_boundary_works() -> None:
    counts = np.array([100.0])
    budget = DpBudget(epsilon=1.0, delta=1e-5)
    noisy = add_dp_noise(counts, budget=budget, mechanism="gaussian", seed=1)
    assert noisy.shape == counts.shape


def test_laplace_mechanism_unaffected_by_epsilon_one_cap() -> None:
    counts = np.array([100.0])
    budget = DpBudget(epsilon=10.0, sensitivity=1.0)
    noisy = add_dp_noise(counts, budget=budget, mechanism="laplace", seed=1)
    assert noisy.shape == counts.shape


def test_add_dp_noise_round_trip_on_cell_population_totals() -> None:
    """Apply DP noise to per-cell totals — noisy values should still
    be in roughly the same scale and sum to a similar total under
    moderate epsilon.
    """

    cell_totals = np.array([5000.0, 4800.0, 5100.0, 4900.0, 5200.0])
    budget = DpBudget(epsilon=2.0, sensitivity=1.0)
    noisy = add_dp_noise(cell_totals, budget=budget, seed=42)
    # Under epsilon=2.0 + sensitivity=1.0 the Laplace scale is 0.5;
    # noise standard deviation ~0.71 << 5000. Per-cell deviation should
    # be within 10 even at extreme tails.
    assert (np.abs(noisy - cell_totals) < 10.0).all()
