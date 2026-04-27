"""Lazy adapter for the optional ``optuna`` hyperparameter sweep package.

``optuna`` is treated as an optional dependency: the adapter imports it on
first call and raises :class:`OptunaUnavailable` if absent. The result is
flattened into a tiny frozen dataclass so callers do not need to handle
``optuna.Study`` objects directly.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal


class OptunaUnavailable(RuntimeError):  # noqa: N818
    """Raised when :mod:`optuna` is requested but not importable."""


@dataclass(frozen=True, slots=True)
class OptunaSweepSpec:
    """Configuration for an Optuna parameter sweep."""

    param_ranges: dict[str, tuple[float, float]]
    n_trials: int
    seed: int
    direction: Literal["minimize", "maximize"]


@dataclass(frozen=True, slots=True)
class OptunaResult:
    """Result of an Optuna sweep."""

    best_params: dict[str, float]
    best_value: float
    trial_count: int


def run_optuna_sweep(
    objective: Callable[[dict[str, float]], float],
    spec: OptunaSweepSpec,
) -> OptunaResult:
    """Run a deterministic Optuna sweep over ``param_ranges``.

    The user-supplied ``objective`` receives a ``dict[str, float]`` of trial
    parameters and must return a scalar. The adapter wires Optuna's
    ``trial.suggest_float`` for each parameter and uses the TPE sampler seeded
    with ``spec.seed`` so the sweep is reproducible.

    Raises
    ------
    OptunaUnavailable
        If ``optuna`` is not importable in the current environment.
    """

    if spec.n_trials <= 0:
        raise ValueError(f"n_trials must be positive (got {spec.n_trials})")
    if spec.direction not in ("minimize", "maximize"):
        raise ValueError(
            f"direction must be 'minimize' or 'maximize' (got {spec.direction!r})"
        )
    if not spec.param_ranges:
        raise ValueError("param_ranges must contain at least one parameter")
    for name, (lo, hi) in spec.param_ranges.items():
        if not lo < hi:
            raise ValueError(
                f"param_ranges[{name!r}] must satisfy lo < hi (got {lo}, {hi})"
            )

    optuna = _load_optuna()
    sampler = optuna.samplers.TPESampler(seed=spec.seed)
    study = optuna.create_study(direction=spec.direction, sampler=sampler)

    def trial_fn(trial: Any) -> float:
        params = {
            name: float(trial.suggest_float(name, lo, hi))
            for name, (lo, hi) in spec.param_ranges.items()
        }
        return float(objective(params))

    study.optimize(trial_fn, n_trials=spec.n_trials)
    best_params = {str(k): float(v) for k, v in study.best_params.items()}
    return OptunaResult(
        best_params=best_params,
        best_value=float(study.best_value),
        trial_count=int(spec.n_trials),
    )


def _load_optuna() -> Any:
    try:
        import optuna  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - import-path guard
        raise OptunaUnavailable(
            "optuna is not installed; install with `pip install optuna` to use "
            "run_optuna_sweep"
        ) from exc
    return optuna


__all__ = [
    "OptunaResult",
    "OptunaSweepSpec",
    "OptunaUnavailable",
    "run_optuna_sweep",
]
