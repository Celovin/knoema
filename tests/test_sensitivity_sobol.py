"""Tests for luvoire.sensitivity.sobol — deterministic Saltelli/Sobol."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.sensitivity.sobol import (
    SaltelliSamples,
    SobolIndices,
    saltelli_sample,
    sobol_indices,
)

BOUNDS_3 = ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0))


def test_saltelli_sample_shapes() -> None:
    samples = saltelli_sample(BOUNDS_3, n=64, seed=20260427)
    assert samples.n == 64
    assert samples.d == 3
    assert samples.a.shape == (64, 3)
    assert samples.b.shape == (64, 3)
    assert samples.ab.shape == (3, 64, 3)
    assert samples.total_evaluations == 64 * 5


def test_saltelli_sample_is_deterministic_per_seed() -> None:
    a1 = saltelli_sample(BOUNDS_3, n=32, seed=11)
    a2 = saltelli_sample(BOUNDS_3, n=32, seed=11)
    np.testing.assert_array_equal(a1.a, a2.a)
    np.testing.assert_array_equal(a1.b, a2.b)
    np.testing.assert_array_equal(a1.ab, a2.ab)


def test_saltelli_sample_changes_with_seed() -> None:
    a1 = saltelli_sample(BOUNDS_3, n=32, seed=11)
    a2 = saltelli_sample(BOUNDS_3, n=32, seed=12)
    assert not np.array_equal(a1.a, a2.a)


def test_saltelli_sample_respects_bounds() -> None:
    bounds = ((0.1, 0.9), (-1.0, 1.0))
    samples = saltelli_sample(bounds, n=16, seed=5)
    assert samples.a.min() >= -1.0
    assert samples.a.max() <= 1.0
    assert samples.a[:, 0].min() >= 0.1
    assert samples.a[:, 0].max() <= 0.9


def test_saltelli_rejects_inverted_bounds() -> None:
    with pytest.raises(ValueError, match="lo < hi"):
        saltelli_sample(((0.5, 0.1),), n=16, seed=5)


def test_sobol_indices_first_variable_dominant() -> None:
    bounds = ((0.0, 1.0), (0.0, 1.0))
    samples = saltelli_sample(bounds, n=4096, seed=7)

    def model(x: np.ndarray) -> np.ndarray:
        return 5.0 * x[:, 0] + 0.1 * x[:, 1]

    indices = sobol_indices(samples, model, ("x0", "x1"))
    assert indices.first_order[0] > indices.first_order[1]
    assert indices.total_order[0] > indices.total_order[1]


def test_sobol_indices_constant_model_zero() -> None:
    samples = saltelli_sample(BOUNDS_3, n=128, seed=3)

    def model(x: np.ndarray) -> np.ndarray:
        return np.full(x.shape[0], 0.5)

    indices = sobol_indices(samples, model, ("a", "b", "c"))
    np.testing.assert_array_equal(indices.first_order, np.zeros(3))
    np.testing.assert_array_equal(indices.total_order, np.zeros(3))


def test_sobol_indices_dataclass_serialisation() -> None:
    samples = saltelli_sample(BOUNDS_3, n=128, seed=21)

    def model(x: np.ndarray) -> np.ndarray:
        return x.sum(axis=1)

    indices = sobol_indices(samples, model, ("motivation", "exposure", "gap"))
    payload = indices.as_dict()
    assert set(payload.keys()) == {"motivation", "exposure", "gap"}
    for entry in payload.values():
        assert "first_order" in entry
        assert "total_order" in entry


def test_sobol_indices_variable_name_length_mismatch() -> None:
    samples = saltelli_sample(BOUNDS_3, n=32, seed=1)

    def model(x: np.ndarray) -> np.ndarray:
        return x.sum(axis=1)

    with pytest.raises(ValueError, match="variable_names length"):
        sobol_indices(samples, model, ("x0", "x1"))


def test_saltelli_sample_n_must_be_positive() -> None:
    with pytest.raises(ValueError, match="n must be positive"):
        saltelli_sample(BOUNDS_3, n=0, seed=1)


def test_saltelli_sample_requires_at_least_one_variable() -> None:
    with pytest.raises(ValueError, match="at least one variable"):
        saltelli_sample((), n=8, seed=1)


def test_sobol_indices_dataclass_is_frozen() -> None:
    indices = SobolIndices(
        first_order=np.array([0.5]),
        total_order=np.array([0.6]),
        variable_names=("x",),
        base_sample_count=8,
    )
    with pytest.raises((AttributeError, TypeError)):
        indices.base_sample_count = 99  # type: ignore[misc]


def test_saltelli_samples_dataclass_is_frozen() -> None:
    samples = saltelli_sample(BOUNDS_3, n=8, seed=1)
    assert isinstance(samples, SaltelliSamples)
    with pytest.raises((AttributeError, TypeError)):
        samples.bounds = ()  # type: ignore[misc]
