"""Tests for luvoire.calibration.ema_adapter — lazy EMA-Workbench PRIM wrapper."""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

from luvoire.calibration.ema_adapter import (
    EmaWorkbenchUnavailable,
    PrimBox,
    PrimDiscoverySpec,
    prim_discovery,
)


@pytest.fixture
def block_ema_import(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Any = None,
        locals: Any = None,
        fromlist: Any = (),
        level: int = 0,
    ) -> Any:
        if name == "ema_workbench" or name.startswith("ema_workbench."):
            raise ModuleNotFoundError(f"mock: {name} blocked")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    yield


def test_ema_unavailable_is_runtime_error_subclass() -> None:
    assert issubclass(EmaWorkbenchUnavailable, RuntimeError)


def test_prim_discovery_raises_unavailable_when_missing(
    block_ema_import: None,
) -> None:
    spec = PrimDiscoverySpec(
        parameter_columns=("a",),
        outcome_column="hit",
        coverage_threshold=0.5,
        density_threshold=0.5,
    )
    with pytest.raises(EmaWorkbenchUnavailable, match="ema_workbench is not installed"):
        prim_discovery(
            {"a": np.linspace(0.0, 1.0, 10)},
            np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1]),
            spec,
        )


def test_prim_discovery_spec_is_frozen() -> None:
    spec = PrimDiscoverySpec(
        parameter_columns=("a",),
        outcome_column="hit",
        coverage_threshold=0.5,
        density_threshold=0.5,
    )
    with pytest.raises((AttributeError, TypeError)):
        spec.coverage_threshold = 0.9  # type: ignore[misc]


def test_prim_discovery_validates_coverage_threshold() -> None:
    with pytest.raises(ValueError, match="coverage_threshold must be in"):
        prim_discovery(
            {"a": np.array([0.0, 1.0])},
            np.array([0, 1]),
            PrimDiscoverySpec(
                parameter_columns=("a",),
                outcome_column="hit",
                coverage_threshold=1.5,
                density_threshold=0.5,
            ),
        )


def test_prim_discovery_validates_density_threshold() -> None:
    with pytest.raises(ValueError, match="density_threshold must be in"):
        prim_discovery(
            {"a": np.array([0.0, 1.0])},
            np.array([0, 1]),
            PrimDiscoverySpec(
                parameter_columns=("a",),
                outcome_column="hit",
                coverage_threshold=0.5,
                density_threshold=-0.1,
            ),
        )


def test_prim_discovery_validates_parameter_columns_non_empty() -> None:
    with pytest.raises(ValueError, match="parameter_columns must be non-empty"):
        prim_discovery(
            {"a": np.array([0.0, 1.0])},
            np.array([0, 1]),
            PrimDiscoverySpec(
                parameter_columns=(),
                outcome_column="hit",
                coverage_threshold=0.5,
                density_threshold=0.5,
            ),
        )


def test_prim_discovery_validates_missing_columns() -> None:
    with pytest.raises(KeyError, match="missing columns"):
        prim_discovery(
            {"a": np.array([0.0, 1.0])},
            np.array([0, 1]),
            PrimDiscoverySpec(
                parameter_columns=("a", "b"),
                outcome_column="hit",
                coverage_threshold=0.5,
                density_threshold=0.5,
            ),
        )


def test_prim_box_is_frozen() -> None:
    box = PrimBox(rules={"a": (0.0, 1.0)}, coverage=0.8, density=0.7)
    with pytest.raises((AttributeError, TypeError)):
        box.coverage = 0.0  # type: ignore[misc]


def test_prim_discovery_real_run_smoke() -> None:
    pytest.importorskip("ema_workbench")
    pytest.importorskip("pandas")

    rng = np.random.default_rng(0)
    n = 200
    x = rng.uniform(0.0, 1.0, size=n)
    y = rng.uniform(0.0, 1.0, size=n)
    # Cases of interest concentrate in the upper-right corner.
    outcomes = ((x > 0.6) & (y > 0.6)).astype(int)
    spec = PrimDiscoverySpec(
        parameter_columns=("x", "y"),
        outcome_column="hit",
        coverage_threshold=0.0,
        density_threshold=0.5,
    )
    box = prim_discovery({"x": x, "y": y}, outcomes, spec)
    assert isinstance(box, PrimBox)
    assert "x" in box.rules
    assert "y" in box.rules
