"""Deterministic Markov-chain sampler over the canonical activity vocabulary.

The transition matrix is row-stochastic and indexed by
:data:`luvoire.timeuse.priors.ACTIVITY_CODES` in canonical order. The sampler
uses a seeded :class:`numpy.random.Generator` so identical ``(matrix, seed)``
pairs reproduce the same walk forever.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from luvoire.timeuse.priors import ACTIVITY_CODES, ActivityCode

_ROW_SUM_TOL = 1e-6
"""Per-row sum tolerance for ``TransitionMatrix`` validation.

``1e-6`` allows a few ulps of accumulated rounding when callers normalise
each row by hand from a histogram with up to ~10 entries (i.e. the seven
canonical activity codes leave plenty of headroom). Inputs that drift
further than this are likely the result of a missing renormalisation step
on the caller's side, not floating-point error, so we reject them
explicitly rather than silently re-renormalise. Callers normalising from
a much larger bin count should renormalise once before constructing the
matrix.
"""
_N_ACTIVITIES = len(ACTIVITY_CODES)


@dataclass(frozen=True, slots=True)
class TransitionMatrix:
    """A 7x7 row-stochastic transition matrix.

    Rows are indexed by the *current* activity, columns by the *next*. Each
    row must sum to 1.0 within ``_ROW_SUM_TOL`` (=1e-6) and all entries must
    lie in ``[0, 1]``. The matrix is stored as a tuple-of-tuples of floats
    so the structure stays hashable and trivially serialisable.
    """

    matrix: tuple[tuple[float, ...], ...]
    _array: np.ndarray = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if len(self.matrix) != _N_ACTIVITIES:
            raise ValueError(
                f"matrix must have {_N_ACTIVITIES} rows (got {len(self.matrix)})"
            )
        normalized_rows: list[tuple[float, ...]] = []
        for row_idx, row in enumerate(self.matrix):
            if len(row) != _N_ACTIVITIES:
                raise ValueError(
                    f"row {row_idx} must have {_N_ACTIVITIES} columns (got {len(row)})"
                )
            row_floats: list[float] = []
            for col_idx, value in enumerate(row):
                if not isinstance(value, int | float):
                    raise TypeError(
                        f"matrix[{row_idx}][{col_idx}] must be a real number "
                        f"(got {type(value).__name__})"
                    )
                fvalue = float(value)
                if not np.isfinite(fvalue):
                    raise ValueError(
                        f"matrix[{row_idx}][{col_idx}] must be finite (got {value!r})"
                    )
                if fvalue < 0.0 or fvalue > 1.0:
                    raise ValueError(
                        f"matrix[{row_idx}][{col_idx}] must be in [0, 1] (got {value!r})"
                    )
                row_floats.append(fvalue)
            row_sum = sum(row_floats)
            if abs(row_sum - 1.0) > _ROW_SUM_TOL:
                raise ValueError(
                    f"row {row_idx} must sum to 1.0 within {_ROW_SUM_TOL} (got {row_sum!r})"
                )
            normalized_rows.append(tuple(row_floats))
        normalized_matrix = tuple(normalized_rows)
        # Re-freeze the canonicalised tuple form so equality is stable.
        object.__setattr__(self, "matrix", normalized_matrix)
        array = np.asarray(normalized_matrix, dtype=np.float64)
        # Pre-compute row CDFs for fast inverse-CDF sampling.
        cdf = np.cumsum(array, axis=1)
        cdf[:, -1] = 1.0
        object.__setattr__(self, "_array", cdf)

    @property
    def cdf(self) -> np.ndarray:
        """Row-wise cumulative distribution function used by the sampler."""

        return self._array


class MarkovActivitySampler:
    """Deterministic Markov-chain walker over :data:`ACTIVITY_CODES`.

    The walker exposes :meth:`step` for single-step advancement and
    :meth:`walk` for batched advancement. ``step`` advances internal state, so
    consecutive calls produce a chain that respects the transition matrix.
    """

    __slots__ = ("_codes", "_matrix", "_rng", "_state_idx")

    def __init__(
        self,
        initial: ActivityCode,
        transitions: TransitionMatrix,
        *,
        seed: int,
    ) -> None:
        self._codes: tuple[ActivityCode, ...] = ACTIVITY_CODES
        if initial not in self._codes:
            raise ValueError(
                f"initial must be one of {self._codes} (got {initial!r})"
            )
        self._matrix = transitions
        self._state_idx = self._codes.index(initial)
        self._rng = np.random.default_rng(seed)

    @property
    def current(self) -> ActivityCode:
        return self._codes[self._state_idx]

    def step(self) -> ActivityCode:
        cdf_row = self._matrix.cdf[self._state_idx]
        u = float(self._rng.random())
        idx = int(np.searchsorted(cdf_row, u, side="right"))
        if idx >= len(self._codes):
            idx = len(self._codes) - 1
        self._state_idx = idx
        return self._codes[idx]

    def walk(self, steps: int) -> tuple[ActivityCode, ...]:
        if steps < 0:
            raise ValueError(f"steps must be non-negative (got {steps})")
        if steps == 0:
            return ()
        out: list[ActivityCode] = []
        for _ in range(steps):
            out.append(self.step())
        return tuple(out)


def transition_from_dict(payload: dict[str, dict[str, float]]) -> TransitionMatrix:
    """Build a :class:`TransitionMatrix` from a nested mapping.

    The outer mapping keys are *current* activity codes and inner mapping
    keys are *next* activity codes. Both must cover the canonical seven-code
    vocabulary exactly. Missing or extra keys raise :class:`ValueError`.
    """

    if not isinstance(payload, dict):
        raise TypeError(f"payload must be a dict (got {type(payload).__name__})")
    outer_keys = set(payload.keys())
    expected = set(ACTIVITY_CODES)
    if outer_keys != expected:
        missing = expected - outer_keys
        extra = outer_keys - expected
        raise ValueError(
            "payload outer keys must cover the canonical activity codes "
            f"(missing={sorted(missing)}, extra={sorted(extra)})"
        )
    rows: list[tuple[float, ...]] = []
    for code in ACTIVITY_CODES:
        inner: Any = payload[code]
        if not isinstance(inner, dict):
            raise TypeError(
                f"payload[{code!r}] must be a dict (got {type(inner).__name__})"
            )
        inner_keys = set(inner.keys())
        if inner_keys != expected:
            missing = expected - inner_keys
            extra = inner_keys - expected
            raise ValueError(
                f"payload[{code!r}] keys must cover the canonical activity codes "
                f"(missing={sorted(missing)}, extra={sorted(extra)})"
            )
        row: list[float] = []
        for next_code in ACTIVITY_CODES:
            value = inner[next_code]
            if not isinstance(value, int | float):
                raise TypeError(
                    f"payload[{code!r}][{next_code!r}] must be a real number "
                    f"(got {type(value).__name__})"
                )
            row.append(float(value))
        rows.append(tuple(row))
    return TransitionMatrix(matrix=tuple(rows))
