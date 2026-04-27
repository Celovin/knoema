"""Lazy adapter for the optional ``sbi`` simulation-based-inference package.

The intent is to keep ``sbi`` (and its torch dependency) strictly optional: the
engine installs and runs without it. Calls into :func:`infer_posterior` import
``sbi`` at call time and raise :class:`SbiUnavailable` if the package is not
present in the environment.

The wrapper exposes a tiny :class:`PosteriorHandle` rather than leaking the
upstream posterior object. Tests can substitute a mock posterior with the same
``sample(n)`` contract without taking a real ``sbi`` dependency.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np


class SbiUnavailable(RuntimeError):  # noqa: N818
    """Raised when :mod:`sbi` is requested but not importable."""


@dataclass(frozen=True, slots=True)
class SbiPosteriorSpec:
    """Configuration for an SNPE-style posterior inference run."""

    bounds: tuple[tuple[float, float], ...]
    num_simulations: int
    seed: int


@dataclass(frozen=True, slots=True)
class PosteriorHandle:
    """Opaque wrapper around an upstream ``sbi`` posterior object.

    The only contract callers should rely on is :meth:`sample`, which returns a
    ``(n, d)`` numpy array. The underlying object is kept on ``_posterior`` so
    advanced users can introspect it, but it is intentionally not part of the
    public API.
    """

    _posterior: Any
    dimension: int

    def sample(self, n: int) -> np.ndarray:
        """Draw ``n`` samples and return them as a ``(n, d)`` numpy array."""

        if n <= 0:
            raise ValueError(f"n must be positive (got {n})")
        raw = self._posterior.sample((n,))
        arr = _to_numpy(raw)
        if arr.ndim == 1:
            arr = arr.reshape(n, -1)
        if arr.shape[0] != n:
            raise RuntimeError(
                f"posterior returned {arr.shape[0]} samples (expected {n})"
            )
        return arr


def infer_posterior(
    simulator: Callable[[np.ndarray], np.ndarray],
    spec: SbiPosteriorSpec,
) -> PosteriorHandle:
    """Train an SNPE posterior and return a :class:`PosteriorHandle`.

    Parameters
    ----------
    simulator:
        Callable taking a 1-D parameter vector and returning a 1-D output
        array. ``sbi`` will batch this internally; the adapter wraps it to
        accept a ``torch.Tensor`` row batch.
    spec:
        Frozen configuration. ``num_simulations`` must be positive and each
        bound must satisfy ``lo < hi``.

    Raises
    ------
    SbiUnavailable
        If ``sbi`` is not importable in the current environment.
    """

    if spec.num_simulations <= 0:
        raise ValueError(
            f"num_simulations must be positive (got {spec.num_simulations})"
        )
    if len(spec.bounds) == 0:
        raise ValueError("at least one bound is required")
    for i, (lo, hi) in enumerate(spec.bounds):
        if not lo < hi:
            raise ValueError(
                f"bounds[{i}] must satisfy lo < hi (got {lo}, {hi})"
            )

    sbi_inference = _load_sbi_inference()
    sbi_utils = _load_sbi_utils()
    torch = _load_torch()

    torch.manual_seed(spec.seed)
    np.random.seed(spec.seed)

    low = torch.tensor([lo for lo, _ in spec.bounds], dtype=torch.float32)
    high = torch.tensor([hi for _, hi in spec.bounds], dtype=torch.float32)
    prior = sbi_utils.BoxUniform(low=low, high=high)

    def torch_simulator(theta_batch: Any) -> Any:
        theta_np = theta_batch.detach().cpu().numpy()
        rows = [
            np.asarray(simulator(theta_np[i]), dtype=float)
            for i in range(theta_np.shape[0])
        ]
        out = np.stack(rows, axis=0)
        return torch.tensor(out, dtype=torch.float32)

    inference = sbi_inference.SNPE(prior=prior)
    theta = prior.sample((spec.num_simulations,))
    x = torch_simulator(theta)
    inference.append_simulations(theta, x)
    inference.train()
    posterior = inference.build_posterior()
    return PosteriorHandle(_posterior=posterior, dimension=len(spec.bounds))


def _load_sbi_inference() -> Any:
    try:
        from sbi import inference as sbi_inference  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - import-path guard
        raise SbiUnavailable(
            "sbi is not installed; install with `pip install sbi` to use "
            "infer_posterior"
        ) from exc
    return sbi_inference


def _load_sbi_utils() -> Any:
    try:
        from sbi import utils as sbi_utils
    except ModuleNotFoundError as exc:  # pragma: no cover - import-path guard
        raise SbiUnavailable(
            "sbi is not installed; install with `pip install sbi` to use "
            "infer_posterior"
        ) from exc
    return sbi_utils


def _load_torch() -> Any:
    try:
        import torch
    except ModuleNotFoundError as exc:  # pragma: no cover - import-path guard
        raise SbiUnavailable(
            "torch is not installed; install with `pip install torch` to use "
            "infer_posterior"
        ) from exc
    return torch


def _to_numpy(obj: Any) -> np.ndarray:
    if isinstance(obj, np.ndarray):
        return obj.astype(float, copy=False)
    detach = getattr(obj, "detach", None)
    if callable(detach):
        obj = detach()
    cpu = getattr(obj, "cpu", None)
    if callable(cpu):
        obj = cpu()
    numpy_fn = getattr(obj, "numpy", None)
    if callable(numpy_fn):
        return np.asarray(numpy_fn(), dtype=float)
    return np.asarray(obj, dtype=float)


__all__ = [
    "PosteriorHandle",
    "SbiPosteriorSpec",
    "SbiUnavailable",
    "infer_posterior",
]
