"""Tests for luvoire.calibration.optuna_adapter — lazy Optuna wrapper."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

import pytest

from luvoire.calibration.optuna_adapter import (
    OptunaResult,
    OptunaSweepSpec,
    OptunaUnavailable,
    run_optuna_sweep,
)


@pytest.fixture
def block_optuna_import(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: Any = (),
        level: int = 0,
    ) -> Any:
        if name == "optuna" or name.startswith("optuna."):
            raise ModuleNotFoundError(f"mock: {name} blocked")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    yield


def test_optuna_unavailable_is_runtime_error_subclass() -> None:
    assert issubclass(OptunaUnavailable, RuntimeError)


def test_run_optuna_sweep_raises_unavailable_when_missing(
    block_optuna_import: None,
) -> None:
    spec = OptunaSweepSpec(
        param_ranges={"x": (0.0, 1.0)},
        n_trials=2,
        seed=0,
        direction="minimize",
    )
    with pytest.raises(OptunaUnavailable, match="optuna is not installed"):
        run_optuna_sweep(lambda params: params["x"], spec)


def test_optuna_sweep_spec_is_frozen() -> None:
    spec = OptunaSweepSpec(
        param_ranges={"x": (0.0, 1.0)},
        n_trials=1,
        seed=0,
        direction="minimize",
    )
    with pytest.raises((AttributeError, TypeError)):
        spec.n_trials = 99  # type: ignore[misc]


def test_run_optuna_sweep_validates_n_trials() -> None:
    with pytest.raises(ValueError, match="n_trials must be positive"):
        run_optuna_sweep(
            lambda params: 0.0,
            OptunaSweepSpec(
                param_ranges={"x": (0.0, 1.0)},
                n_trials=0,
                seed=0,
                direction="minimize",
            ),
        )


def test_run_optuna_sweep_validates_direction() -> None:
    with pytest.raises(ValueError, match="direction must be"):
        run_optuna_sweep(
            lambda params: 0.0,
            OptunaSweepSpec(
                param_ranges={"x": (0.0, 1.0)},
                n_trials=1,
                seed=0,
                direction="sideways",  # type: ignore[arg-type]
            ),
        )


def test_run_optuna_sweep_validates_param_ranges_non_empty() -> None:
    with pytest.raises(ValueError, match="param_ranges must contain"):
        run_optuna_sweep(
            lambda params: 0.0,
            OptunaSweepSpec(
                param_ranges={},
                n_trials=1,
                seed=0,
                direction="minimize",
            ),
        )


def test_run_optuna_sweep_validates_range_ordering() -> None:
    with pytest.raises(ValueError, match="lo < hi"):
        run_optuna_sweep(
            lambda params: 0.0,
            OptunaSweepSpec(
                param_ranges={"x": (1.0, 0.0)},
                n_trials=1,
                seed=0,
                direction="minimize",
            ),
        )


def test_optuna_result_is_frozen() -> None:
    result = OptunaResult(
        best_params={"x": 0.5},
        best_value=0.25,
        trial_count=10,
    )
    with pytest.raises((AttributeError, TypeError)):
        result.trial_count = 99  # type: ignore[misc]


def test_run_optuna_sweep_real_run_smoke() -> None:
    optuna = pytest.importorskip("optuna")
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    spec = OptunaSweepSpec(
        param_ranges={"x": (-2.0, 2.0)},
        n_trials=10,
        seed=42,
        direction="minimize",
    )

    def quadratic(params: dict[str, float]) -> float:
        return float((params["x"] - 0.7) ** 2)

    result = run_optuna_sweep(quadratic, spec)
    assert isinstance(result, OptunaResult)
    assert result.trial_count == 10
    assert "x" in result.best_params
    assert -2.0 <= result.best_params["x"] <= 2.0
    assert result.best_value >= 0.0
