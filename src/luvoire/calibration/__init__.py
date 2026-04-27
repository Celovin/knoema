"""Calibration adapters: SBI, Optuna, EMA-Workbench, and reference ABC.

Three of the four submodules are thin lazy wrappers around optional
third-party packages (``sbi``, ``optuna``, ``ema_workbench``). The engine does
not depend on any of them at install time; importing this package never
imports the optional dependencies. Calls into the wrapper functions trigger
the import on first use and raise a typed ``*Unavailable`` exception if the
underlying package is missing.

The :mod:`abc` submodule is a pure-numpy rejection-ABC sampler that always
works and can be used as a deterministic baseline calibrator.
"""

from luvoire.calibration.abc import (
    AbcResult,
    RejectionAbcSpec,
    rejection_abc,
)
from luvoire.calibration.ema_adapter import (
    EmaWorkbenchUnavailable,
    PrimBox,
    PrimDiscoverySpec,
    prim_discovery,
)
from luvoire.calibration.optuna_adapter import (
    OptunaResult,
    OptunaSweepSpec,
    OptunaUnavailable,
    run_optuna_sweep,
)
from luvoire.calibration.sbi_adapter import (
    PosteriorHandle,
    SbiPosteriorSpec,
    SbiUnavailable,
    infer_posterior,
)

__all__ = [
    "AbcResult",
    "EmaWorkbenchUnavailable",
    "OptunaResult",
    "OptunaSweepSpec",
    "OptunaUnavailable",
    "PosteriorHandle",
    "PrimBox",
    "PrimDiscoverySpec",
    "RejectionAbcSpec",
    "SbiPosteriorSpec",
    "SbiUnavailable",
    "infer_posterior",
    "prim_discovery",
    "rejection_abc",
    "run_optuna_sweep",
]
