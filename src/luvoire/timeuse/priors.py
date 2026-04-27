"""Empirical CDF sampler over a canonical 7-class activity vocabulary.

Activity codes follow a deliberately small vocabulary that is large enough to
distinguish the dominant slabs of a 24-hour day (sleep, work/school, commute,
meals, leisure, care, other) yet small enough to allow strata-level priors to
remain interpretable in unit tests and in published parameter cards.

The sampler is implemented with numpy's :class:`numpy.random.Generator` so
that the same seed reproduces the same sequence forever, regardless of how
many independent samplers are constructed in the same process.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, get_args

import numpy as np

ActivityCode = Literal[
    "sleep",
    "work_or_school",
    "commute",
    "meals",
    "leisure",
    "care",
    "other",
]
"""Canonical seven-element activity vocabulary."""

ACTIVITY_CODES: tuple[ActivityCode, ...] = get_args(ActivityCode)
"""Tuple form of the activity vocabulary, in canonical order."""

DayType = Literal["weekday", "weekend", "holiday"]
AgeBand = Literal["youth", "adult", "senior"]
Occupation = Literal["student", "employed", "homemaker", "retired", "other"]

_DAY_TYPES: tuple[DayType, ...] = get_args(DayType)
_AGE_BANDS: tuple[AgeBand, ...] = get_args(AgeBand)
_OCCUPATIONS: tuple[Occupation, ...] = get_args(Occupation)

_WEIGHT_SUM_TOL = 1e-6


@dataclass(frozen=True, slots=True)
class StrataKey:
    """A coarse demographic stratum key for time-use priors.

    The key intentionally uses a small enumerated vocabulary on each axis so
    that strata are countable and so that synthetic priors can be authored by
    hand for tests. Real KOSTAT-derived priors keyed off the same enums live
    in a separate (offline) pipeline.
    """

    day_type: DayType
    age_band: AgeBand
    occupation: Occupation

    def __post_init__(self) -> None:
        if self.day_type not in _DAY_TYPES:
            raise ValueError(
                f"day_type must be one of {_DAY_TYPES} (got {self.day_type!r})"
            )
        if self.age_band not in _AGE_BANDS:
            raise ValueError(
                f"age_band must be one of {_AGE_BANDS} (got {self.age_band!r})"
            )
        if self.occupation not in _OCCUPATIONS:
            raise ValueError(
                f"occupation must be one of {_OCCUPATIONS} (got {self.occupation!r})"
            )


@dataclass(frozen=True, slots=True)
class ActivityPrior:
    """Strata-conditioned empirical distribution over the activity vocabulary.

    ``weights`` must contain exactly the seven canonical activity codes as
    keys, each value must lie in ``[0, 1]``, and the sum of values must equal
    ``1.0`` within ``1e-6``.
    """

    strata: StrataKey
    weights: dict[ActivityCode, float]
    source: str
    revision: str | None = None
    _ordered_weights: tuple[float, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        keys = set(self.weights.keys())
        expected = set(ACTIVITY_CODES)
        if keys != expected:
            missing = expected - keys
            extra = keys - expected
            raise ValueError(
                "weights must contain exactly the canonical activity codes "
                f"(missing={sorted(missing)}, extra={sorted(extra)})"
            )
        for code, value in self.weights.items():
            if not isinstance(value, int | float):
                raise TypeError(
                    f"weights[{code!r}] must be a real number (got {type(value).__name__})"
                )
            fvalue = float(value)
            if not np.isfinite(fvalue):
                raise ValueError(f"weights[{code!r}] must be finite (got {value!r})")
            if fvalue < 0.0 or fvalue > 1.0:
                raise ValueError(
                    f"weights[{code!r}] must be in [0, 1] (got {value!r})"
                )
        total = sum(float(self.weights[code]) for code in ACTIVITY_CODES)
        if abs(total - 1.0) > _WEIGHT_SUM_TOL:
            raise ValueError(
                f"weights must sum to 1.0 within {_WEIGHT_SUM_TOL} (got {total!r})"
            )
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a non-empty string")
        ordered = tuple(float(self.weights[code]) for code in ACTIVITY_CODES)
        # Bypass frozen=True for derived cache field.
        object.__setattr__(self, "_ordered_weights", ordered)

    @property
    def ordered_weights(self) -> tuple[float, ...]:
        """Weights in canonical :data:`ACTIVITY_CODES` order."""

        return self._ordered_weights


class EmpiricalCdfSampler:
    """Deterministic categorical sampler driven by an :class:`ActivityPrior`.

    Uses inverse-CDF sampling on uniform draws from
    :func:`numpy.random.default_rng`, so the same ``(prior, seed)`` pair yields
    the same sequence of activity codes forever.
    """

    __slots__ = ("_cdf", "_codes", "_prior", "_rng")

    def __init__(self, prior: ActivityPrior, *, seed: int) -> None:
        self._prior = prior
        self._codes: tuple[ActivityCode, ...] = ACTIVITY_CODES
        weights = np.asarray(prior.ordered_weights, dtype=np.float64)
        # Renormalise within tolerance to defend against accumulated rounding.
        cdf = np.cumsum(weights)
        cdf = cdf / cdf[-1]
        self._cdf = cdf
        self._rng = np.random.default_rng(seed)

    @property
    def prior(self) -> ActivityPrior:
        return self._prior

    def sample_one(self) -> ActivityCode:
        u = float(self._rng.random())
        idx = int(np.searchsorted(self._cdf, u, side="right"))
        if idx >= len(self._codes):
            idx = len(self._codes) - 1
        return self._codes[idx]

    def sample_many(self, n: int) -> tuple[ActivityCode, ...]:
        if n < 0:
            raise ValueError(f"n must be non-negative (got {n})")
        if n == 0:
            return ()
        draws = self._rng.random(n)
        idxs = np.searchsorted(self._cdf, draws, side="right")
        idxs = np.clip(idxs, 0, len(self._codes) - 1)
        return tuple(self._codes[int(i)] for i in idxs)


def load_priors_from_json(path: str | Path) -> tuple[ActivityPrior, ...]:
    """Load a tuple of :class:`ActivityPrior` from the synthetic JSON fixture.

    The JSON shape is::

        {
          "version": "v1",
          "priors": [
            {
              "strata": {"day_type": ..., "age_band": ..., "occupation": ...},
              "weights": {"sleep": ..., ..., "other": ...},
              "source": "...",
              "revision": "..."
            },
            ...
          ]
        }
    """

    json_path = Path(path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"prior fixture root must be an object (got {type(payload).__name__})")
    raw_priors = payload.get("priors")
    if not isinstance(raw_priors, list):
        raise ValueError("prior fixture must contain a 'priors' list")
    return tuple(_prior_from_payload(item) for item in raw_priors)


def _prior_from_payload(item: Any) -> ActivityPrior:
    if not isinstance(item, dict):
        raise ValueError("each prior entry must be an object")
    strata_payload = item.get("strata")
    if not isinstance(strata_payload, dict):
        raise ValueError("each prior entry must contain a 'strata' object")
    strata = StrataKey(
        day_type=_require_literal(strata_payload, "day_type", _DAY_TYPES),
        age_band=_require_literal(strata_payload, "age_band", _AGE_BANDS),
        occupation=_require_literal(strata_payload, "occupation", _OCCUPATIONS),
    )
    weights_payload = item.get("weights")
    if not isinstance(weights_payload, dict):
        raise ValueError("each prior entry must contain a 'weights' object")
    weights = _coerce_weights(weights_payload)
    source = item.get("source")
    if not isinstance(source, str) or not source:
        raise ValueError("each prior entry must declare a non-empty 'source'")
    revision_raw = item.get("revision")
    revision: str | None
    if revision_raw is None:
        revision = None
    elif isinstance(revision_raw, str):
        revision = revision_raw
    else:
        raise ValueError("'revision' must be a string or null")
    return ActivityPrior(strata=strata, weights=weights, source=source, revision=revision)


def _require_literal(payload: dict[str, Any], key: str, allowed: Iterable[str]) -> Any:
    if key not in payload:
        raise ValueError(f"strata is missing required key {key!r}")
    value = payload[key]
    allowed_tuple = tuple(allowed)
    if value not in allowed_tuple:
        raise ValueError(f"strata.{key} must be one of {allowed_tuple} (got {value!r})")
    return value


def _coerce_weights(payload: dict[str, Any]) -> dict[ActivityCode, float]:
    weights: dict[ActivityCode, float] = {}
    for code in ACTIVITY_CODES:
        if code not in payload:
            raise ValueError(f"weights is missing required activity code {code!r}")
        raw = payload[code]
        if not isinstance(raw, int | float):
            raise TypeError(
                f"weights[{code!r}] must be a real number (got {type(raw).__name__})"
            )
        weights[code] = float(raw)
    extras = set(payload.keys()) - set(ACTIVITY_CODES)
    if extras:
        raise ValueError(
            f"weights contains unexpected activity codes: {sorted(extras)}"
        )
    return weights
