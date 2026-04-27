"""Tests for luvoire.calibration.abc — pure-numpy rejection ABC."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.calibration.abc import (
    AbcResult,
    RejectionAbcSpec,
    rejection_abc,
)


def _identity_simulator(theta: np.ndarray) -> np.ndarray:
    """Simulator whose output equals its parameters; useful for closed-form checks."""

    return np.asarray(theta, dtype=float).ravel()


def _linear_simulator(theta: np.ndarray) -> np.ndarray:
    """Linear simulator: y = 2*theta + 1 (elementwise)."""

    return 2.0 * np.asarray(theta, dtype=float).ravel() + 1.0


def test_rejection_abc_is_deterministic_per_seed() -> None:
    spec = RejectionAbcSpec(
        prior_bounds=((0.0, 1.0), (-1.0, 1.0)),
        epsilon=0.5,
        n_proposals=200,
        seed=42,
    )
    observed = np.array([0.5, 0.0])
    r1 = rejection_abc(_identity_simulator, observed, spec)
    r2 = rejection_abc(_identity_simulator, observed, spec)
    np.testing.assert_array_equal(r1.accepted_thetas, r2.accepted_thetas)
    assert r1.acceptance_rate == r2.acceptance_rate
    assert r1.n_accepted == r2.n_accepted


def test_rejection_abc_diverges_across_seeds() -> None:
    spec_a = RejectionAbcSpec(
        prior_bounds=((0.0, 1.0),),
        epsilon=0.2,
        n_proposals=200,
        seed=1,
    )
    spec_b = RejectionAbcSpec(
        prior_bounds=((0.0, 1.0),),
        epsilon=0.2,
        n_proposals=200,
        seed=2,
    )
    observed = np.array([0.5])
    r_a = rejection_abc(_identity_simulator, observed, spec_a)
    r_b = rejection_abc(_identity_simulator, observed, spec_b)
    # Two independent seeds should not produce identical accepted sets in
    # any non-degenerate setting; we check both that the arrays differ and
    # that the acceptance counts are not identical bit-for-bit by accident.
    different_shape = r_a.accepted_thetas.shape != r_b.accepted_thetas.shape
    different_values = (
        r_a.accepted_thetas.shape == r_b.accepted_thetas.shape
        and not np.array_equal(r_a.accepted_thetas, r_b.accepted_thetas)
    )
    assert different_shape or different_values


def test_rejection_abc_acceptance_rate_sanity() -> None:
    spec = RejectionAbcSpec(
        prior_bounds=((0.0, 1.0),),
        epsilon=10.0,  # huge tolerance: everything passes
        n_proposals=100,
        seed=7,
    )
    observed = np.array([0.5])
    result = rejection_abc(_identity_simulator, observed, spec)
    assert result.acceptance_rate == 1.0
    assert result.n_accepted == 100
    assert result.accepted_thetas.shape == (100, 1)


def test_rejection_abc_zero_epsilon_rejects_all_with_continuous_prior() -> None:
    spec = RejectionAbcSpec(
        prior_bounds=((0.0, 1.0),),
        epsilon=1e-12,
        n_proposals=50,
        seed=0,
    )
    observed = np.array([0.123456])
    result = rejection_abc(_identity_simulator, observed, spec)
    # With a continuous uniform prior the chance of hitting an exact match is
    # effectively zero, so the acceptance rate must collapse.
    assert result.n_accepted == 0
    assert result.acceptance_rate == 0.0
    assert result.accepted_thetas.shape == (0, 1)


def test_rejection_abc_respects_prior_bounds() -> None:
    spec = RejectionAbcSpec(
        prior_bounds=((-2.0, -1.0), (3.0, 4.0)),
        epsilon=100.0,  # accept everything so we can audit the prior support
        n_proposals=300,
        seed=99,
    )
    observed = np.array([0.0, 0.0])
    result = rejection_abc(_identity_simulator, observed, spec)
    assert result.n_accepted == 300
    assert result.accepted_thetas[:, 0].min() >= -2.0
    assert result.accepted_thetas[:, 0].max() <= -1.0
    assert result.accepted_thetas[:, 1].min() >= 3.0
    assert result.accepted_thetas[:, 1].max() <= 4.0


def test_rejection_abc_dataclass_is_frozen() -> None:
    spec = RejectionAbcSpec(
        prior_bounds=((0.0, 1.0),),
        epsilon=0.5,
        n_proposals=10,
        seed=1,
    )
    observed = np.array([0.5])
    result = rejection_abc(_identity_simulator, observed, spec)
    assert isinstance(result, AbcResult)
    with pytest.raises((AttributeError, TypeError)):
        result.n_accepted = 999  # type: ignore[misc]
    with pytest.raises((AttributeError, TypeError)):
        spec.epsilon = 0.0  # type: ignore[misc]


def test_rejection_abc_uses_l2_distance() -> None:
    # observed = 1.0; simulator y = 2*theta+1; accept iff |2*theta+1 - 1| <= 0.4,
    # i.e. theta in [-0.2, 0.2].
    spec = RejectionAbcSpec(
        prior_bounds=((-1.0, 1.0),),
        epsilon=0.4,
        n_proposals=2000,
        seed=11,
    )
    observed = np.array([1.0])
    result = rejection_abc(_linear_simulator, observed, spec)
    if result.n_accepted > 0:
        assert result.accepted_thetas[:, 0].min() >= -0.2 - 1e-9
        assert result.accepted_thetas[:, 0].max() <= 0.2 + 1e-9
    # Coarse rate bound: the analytical acceptance fraction is 0.4/2.0 = 0.2.
    assert 0.10 <= result.acceptance_rate <= 0.30


def test_rejection_abc_validates_epsilon() -> None:
    with pytest.raises(ValueError, match="epsilon must be non-negative"):
        rejection_abc(
            _identity_simulator,
            np.array([0.0]),
            RejectionAbcSpec(
                prior_bounds=((0.0, 1.0),),
                epsilon=-0.1,
                n_proposals=10,
                seed=0,
            ),
        )


def test_rejection_abc_validates_n_proposals() -> None:
    with pytest.raises(ValueError, match="n_proposals must be positive"):
        rejection_abc(
            _identity_simulator,
            np.array([0.0]),
            RejectionAbcSpec(
                prior_bounds=((0.0, 1.0),),
                epsilon=0.1,
                n_proposals=0,
                seed=0,
            ),
        )


def test_rejection_abc_validates_prior_bounds_ordering() -> None:
    with pytest.raises(ValueError, match="lo < hi"):
        rejection_abc(
            _identity_simulator,
            np.array([0.0]),
            RejectionAbcSpec(
                prior_bounds=((0.5, 0.1),),
                epsilon=0.1,
                n_proposals=10,
                seed=0,
            ),
        )


def test_rejection_abc_validates_simulator_output_shape() -> None:
    def bad_simulator(theta: np.ndarray) -> np.ndarray:
        return np.array([0.0, 0.0, 0.0])

    spec = RejectionAbcSpec(
        prior_bounds=((0.0, 1.0),),
        epsilon=0.1,
        n_proposals=5,
        seed=0,
    )
    with pytest.raises(ValueError, match="simulator output shape"):
        rejection_abc(bad_simulator, np.array([0.0]), spec)
