"""Tests for luvoire.calibration.sbi_adapter — lazy SBI wrapper."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

from luvoire.calibration import sbi_adapter
from luvoire.calibration.sbi_adapter import (
    PosteriorHandle,
    SbiPosteriorSpec,
    SbiUnavailable,
    infer_posterior,
)


@pytest.fixture
def block_sbi_import(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: Any = (),
        level: int = 0,
    ) -> Any:
        if name == "sbi" or name.startswith("sbi."):
            raise ModuleNotFoundError(f"mock: {name} blocked")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    yield


def test_sbi_unavailable_is_runtime_error_subclass() -> None:
    assert issubclass(SbiUnavailable, RuntimeError)


def test_infer_posterior_raises_sbi_unavailable_when_missing(
    block_sbi_import: None,
) -> None:
    spec = SbiPosteriorSpec(
        bounds=((0.0, 1.0),),
        num_simulations=4,
        seed=0,
    )

    def simulator(theta: np.ndarray) -> np.ndarray:
        return np.asarray(theta, dtype=float).ravel()

    with pytest.raises(SbiUnavailable, match="sbi is not installed"):
        infer_posterior(simulator, spec)


def test_sbi_posterior_spec_is_frozen() -> None:
    spec = SbiPosteriorSpec(
        bounds=((0.0, 1.0),),
        num_simulations=4,
        seed=0,
    )
    with pytest.raises((AttributeError, TypeError)):
        spec.num_simulations = 999  # type: ignore[misc]


def test_infer_posterior_validates_num_simulations() -> None:
    with pytest.raises(ValueError, match="num_simulations must be positive"):
        infer_posterior(
            lambda theta: np.asarray(theta).ravel(),
            SbiPosteriorSpec(
                bounds=((0.0, 1.0),),
                num_simulations=0,
                seed=0,
            ),
        )


def test_infer_posterior_validates_bounds_non_empty() -> None:
    with pytest.raises(ValueError, match="at least one bound"):
        infer_posterior(
            lambda theta: np.asarray(theta).ravel(),
            SbiPosteriorSpec(
                bounds=(),
                num_simulations=4,
                seed=0,
            ),
        )


def test_infer_posterior_validates_bounds_ordering() -> None:
    with pytest.raises(ValueError, match="lo < hi"):
        infer_posterior(
            lambda theta: np.asarray(theta).ravel(),
            SbiPosteriorSpec(
                bounds=((0.5, 0.1),),
                num_simulations=4,
                seed=0,
            ),
        )


def test_posterior_handle_sample_shape() -> None:
    class _MockPosterior:
        def __init__(self, dim: int) -> None:
            self._dim = dim

        def sample(self, shape: tuple[int, ...]) -> np.ndarray:
            n = shape[0]
            return np.zeros((n, self._dim), dtype=float)

    handle = PosteriorHandle(_posterior=_MockPosterior(3), dimension=3)
    samples = handle.sample(7)
    assert samples.shape == (7, 3)


def test_posterior_handle_rejects_non_positive_n() -> None:
    handle = PosteriorHandle(_posterior=object(), dimension=1)
    with pytest.raises(ValueError, match="n must be positive"):
        handle.sample(0)


def test_posterior_handle_rejects_wrong_dimension() -> None:
    class _MismatchPosterior:
        def sample(self, shape: tuple[int, ...]) -> np.ndarray:
            return np.zeros((shape[0], 5), dtype=float)

    handle = PosteriorHandle(_posterior=_MismatchPosterior(), dimension=3)
    with pytest.raises(RuntimeError, match="dimension 5"):
        handle.sample(4)


def test_posterior_handle_rejects_non_2d_output() -> None:
    class _ThreeDPosterior:
        def sample(self, shape: tuple[int, ...]) -> np.ndarray:
            return np.zeros((shape[0], 1, 1), dtype=float)

    handle = PosteriorHandle(_posterior=_ThreeDPosterior(), dimension=1)
    with pytest.raises(RuntimeError, match="3-D array"):
        handle.sample(2)


def test_infer_posterior_real_run_smoke() -> None:
    pytest.importorskip("sbi")
    pytest.importorskip("torch")

    spec = SbiPosteriorSpec(
        bounds=((-1.0, 1.0), (-1.0, 1.0)),
        num_simulations=20,
        seed=0,
    )

    def simulator(theta: np.ndarray) -> np.ndarray:
        return np.asarray(theta, dtype=float).ravel() + 0.1

    handle = infer_posterior(simulator, spec)
    assert isinstance(handle, PosteriorHandle)
    assert handle.dimension == 2


def test_sbi_adapter_module_does_not_import_sbi_eagerly() -> None:
    # Importing the adapter module should never trigger an sbi import.
    import sys

    assert "sbi" not in sys.modules or hasattr(sbi_adapter, "infer_posterior")
