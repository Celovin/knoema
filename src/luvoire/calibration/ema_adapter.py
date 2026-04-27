"""Lazy adapter for the optional ``ema_workbench`` PRIM scenario discovery.

PRIM (Patient Rule Induction Method) is the standard scenario-discovery
algorithm in the deep-uncertainty / exploratory-modelling literature. We wrap
``ema_workbench.analysis.prim`` behind a tiny :class:`PrimBox` so callers do
not have to consume the upstream Box object directly. The package itself is
optional; calling :func:`prim_discovery` without it raises
:class:`EmaWorkbenchUnavailable`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


class EmaWorkbenchUnavailable(RuntimeError):  # noqa: N818
    """Raised when :mod:`ema_workbench` is requested but not importable."""


@dataclass(frozen=True, slots=True)
class PrimDiscoverySpec:
    """Configuration for a PRIM scenario-discovery pass."""

    parameter_columns: tuple[str, ...]
    outcome_column: str
    coverage_threshold: float
    density_threshold: float


@dataclass(frozen=True, slots=True)
class PrimBox:
    """Wrapper around the selected PRIM box."""

    rules: dict[str, tuple[float, float]]
    coverage: float
    density: float


def prim_discovery(
    experiments: dict[str, np.ndarray],
    outcomes: np.ndarray,
    spec: PrimDiscoverySpec,
) -> PrimBox:
    """Run PRIM and return the first box meeting both thresholds.

    Parameters
    ----------
    experiments:
        Mapping ``parameter_name -> 1-D array`` of design-of-experiment inputs.
        Every column listed in ``spec.parameter_columns`` must be present and
        have the same length as ``outcomes``.
    outcomes:
        1-D boolean / 0-1 array marking each row as a "case of interest".
    spec:
        Frozen configuration. ``coverage_threshold`` and ``density_threshold``
        must lie in ``[0, 1]``.

    Raises
    ------
    EmaWorkbenchUnavailable
        If ``ema_workbench`` is not importable in the current environment.
    """

    if not 0.0 <= spec.coverage_threshold <= 1.0:
        raise ValueError(
            f"coverage_threshold must be in [0, 1] (got {spec.coverage_threshold})"
        )
    if not 0.0 <= spec.density_threshold <= 1.0:
        raise ValueError(
            f"density_threshold must be in [0, 1] (got {spec.density_threshold})"
        )
    if not spec.parameter_columns:
        raise ValueError("parameter_columns must be non-empty")
    missing = [c for c in spec.parameter_columns if c not in experiments]
    if missing:
        raise KeyError(
            f"experiments is missing columns: {sorted(missing)!r}"
        )

    outcomes_arr = np.asarray(outcomes).ravel()
    n = outcomes_arr.shape[0]
    for col in spec.parameter_columns:
        arr = np.asarray(experiments[col]).ravel()
        if arr.shape[0] != n:
            raise ValueError(
                f"experiments[{col!r}] length {arr.shape[0]} does not match "
                f"outcomes length {n}"
            )

    prim_module = _load_prim_module()
    pandas = _load_pandas()

    frame = pandas.DataFrame(
        {col: np.asarray(experiments[col]).ravel() for col in spec.parameter_columns}
    )
    flag = outcomes_arr.astype(bool)
    alg = prim_module.Prim(
        frame,
        flag,
        threshold=spec.density_threshold,
    )
    box = alg.find_box()
    rules = _extract_box_rules(box, spec.parameter_columns)
    coverage = _extract_box_metric(box, "coverage", default=0.0)
    density = _extract_box_metric(box, "density", default=0.0)
    if coverage < spec.coverage_threshold:
        # The caller asked for a minimum coverage; surface what PRIM actually
        # found rather than silently returning a worse box.
        raise RuntimeError(
            f"PRIM box coverage {coverage:.3f} below threshold "
            f"{spec.coverage_threshold:.3f}"
        )
    return PrimBox(rules=rules, coverage=float(coverage), density=float(density))


def _load_prim_module() -> Any:
    try:
        from ema_workbench.analysis import (  # type: ignore[import-not-found]
            prim as prim_module,
        )
    except ModuleNotFoundError as exc:  # pragma: no cover - import-path guard
        raise EmaWorkbenchUnavailable(
            "ema_workbench is not installed; install with `pip install "
            "ema_workbench` to use prim_discovery"
        ) from exc
    return prim_module


def _load_pandas() -> Any:
    try:
        import pandas  # type: ignore[import-untyped]
    except ModuleNotFoundError as exc:  # pragma: no cover - import-path guard
        raise EmaWorkbenchUnavailable(
            "pandas is required by ema_workbench; install with `pip install "
            "pandas`"
        ) from exc
    return pandas


def _extract_box_rules(
    box: Any,
    parameter_columns: tuple[str, ...],
) -> dict[str, tuple[float, float]]:
    limits = getattr(box, "box_lims", None)
    if limits is None or len(limits) == 0:
        return {col: (float("-inf"), float("inf")) for col in parameter_columns}
    last = limits[-1]
    rules: dict[str, tuple[float, float]] = {}
    for col in parameter_columns:
        if col in getattr(last, "columns", ()):
            lo = float(np.asarray(last[col]).ravel()[0])
            hi = float(np.asarray(last[col]).ravel()[-1])
            rules[col] = (lo, hi)
        else:
            rules[col] = (float("-inf"), float("inf"))
    return rules


def _extract_box_metric(box: Any, name: str, *, default: float) -> float:
    series = getattr(box, name, None)
    if series is None:
        return float(default)
    try:
        return float(np.asarray(series).ravel()[-1])
    except (IndexError, ValueError, TypeError):
        return float(default)


__all__ = [
    "EmaWorkbenchUnavailable",
    "PrimBox",
    "PrimDiscoverySpec",
    "prim_discovery",
]
