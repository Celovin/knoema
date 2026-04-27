"""Pattern definitions for Pattern-Oriented Modeling (POM) validation.

A :class:`Pattern` captures a target binned probability distribution against
which a simulated empirical distribution can be compared. The default
patterns from the realism roadmap section 7.3 are:

* G1: time-of-day distribution (hour-of-day or finer bin),
* G2: activity-diversity distribution (Simpson / count-bin shape),
* G3: synthetic hotspot distribution (structural pattern only; never real
  human mobility data).

The factories below are intentionally thin: callers pass a numpy array
representing the *target* normalised histogram (or raw samples that the
caller has already aggregated). All canonical reference factories stamp the
appropriate ``pattern_id`` and description so downstream gates can look up
the right comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class Pattern:
    """A binned target distribution for a single POM gate.

    Attributes
    ----------
    pattern_id:
        Stable identifier (e.g. ``"G1_time_of_day"``).
    description:
        Human-readable summary used in logs and audit artifacts.
    target_distribution:
        Tuple of non-negative bin probabilities summing to ``1.0`` within
        :data:`_TOLERANCE`.
    bins:
        Number of histogram bins. Must equal ``len(target_distribution)``.
    """

    pattern_id: str
    description: str
    target_distribution: tuple[float, ...]
    bins: int

    def __post_init__(self) -> None:
        if not self.pattern_id:
            raise ValueError("pattern_id must be a non-empty string")
        if self.bins <= 0:
            raise ValueError(f"bins must be positive (got {self.bins})")
        if len(self.target_distribution) != self.bins:
            raise ValueError(
                f"target_distribution length {len(self.target_distribution)} "
                f"does not match bins {self.bins}"
            )
        arr = np.asarray(self.target_distribution, dtype=float)
        if np.any(arr < 0.0):
            raise ValueError("target_distribution entries must be non-negative")
        total = float(arr.sum())
        if not np.isfinite(total):
            raise ValueError("target_distribution must contain finite values")
        if abs(total - 1.0) > _TOLERANCE:
            raise ValueError(
                f"target_distribution must sum to 1.0 within {_TOLERANCE} "
                f"(got {total})"
            )

    def target_array(self) -> np.ndarray:
        """Return the target distribution as a 1-D float array."""

        return np.asarray(self.target_distribution, dtype=float)


def pattern_from_samples(
    pattern_id: str,
    samples: np.ndarray,
    *,
    bins: int,
    description: str,
) -> Pattern:
    """Build a :class:`Pattern` by binning ``samples`` into a normalised histogram.

    The histogram uses ``bins`` equal-width bins spanning
    ``[samples.min(), samples.max()]``. Empty inputs raise ``ValueError``.
    The resulting distribution is renormalised to sum exactly to 1.0 so that
    the :class:`Pattern` invariant is satisfied even after floating-point
    summation drift.
    """

    if bins <= 0:
        raise ValueError(f"bins must be positive (got {bins})")
    arr = np.asarray(samples, dtype=float)
    if arr.size == 0:
        raise ValueError("samples must contain at least one value")
    if not np.all(np.isfinite(arr)):
        raise ValueError("samples must contain finite values")
    lo = float(arr.min())
    hi = float(arr.max())
    if lo == hi:
        # All identical values collapse into a single full-mass bin. We
        # respect the requested bin count by placing all mass in the first
        # bin; this keeps the Pattern shape consistent across callers.
        hist = np.zeros(bins, dtype=float)
        hist[0] = 1.0
    else:
        counts, _ = np.histogram(arr, bins=bins, range=(lo, hi))
        total = counts.sum()
        if total == 0:
            raise ValueError("histogram contains zero counts")
        hist = counts.astype(float) / float(total)
    # Renormalise to absorb any sub-tolerance drift.
    hist = hist / hist.sum()
    return Pattern(
        pattern_id=pattern_id,
        description=description,
        target_distribution=tuple(float(x) for x in hist),
        bins=bins,
    )


def time_of_day_pattern(target: np.ndarray) -> Pattern:
    """G1: time-of-day distribution.

    ``target`` must already be a normalised histogram (e.g. 24 hourly bins).
    Use :func:`pattern_from_samples` if you only have raw timestamps.
    """

    arr = np.asarray(target, dtype=float)
    return Pattern(
        pattern_id="G1_time_of_day",
        description="Time-of-day activity distribution (binned histogram).",
        target_distribution=tuple(float(x) for x in arr),
        bins=int(arr.size),
    )


def activity_diversity_pattern(target: np.ndarray) -> Pattern:
    """G2: activity-diversity distribution.

    ``target`` is the reference histogram of distinct-activity counts (or any
    ordinal diversity measure) per agent/day. The shape is what matters; the
    POM gate only compares CDFs.
    """

    arr = np.asarray(target, dtype=float)
    return Pattern(
        pattern_id="G2_activity_diversity",
        description="Activity-diversity distribution (binned histogram).",
        target_distribution=tuple(float(x) for x in arr),
        bins=int(arr.size),
    )


def hotspot_distribution_pattern(target: np.ndarray) -> Pattern:
    """G3: synthetic hotspot distribution.

    The hotspot pattern is a *structural* reference (e.g. a synthetic
    power-law or Zipf-like shape) and must never be derived from real human
    mobility traces. The POM gate validates that the simulator reproduces
    the expected concentration of activity onto a small number of cells.
    """

    arr = np.asarray(target, dtype=float)
    return Pattern(
        pattern_id="G3_hotspot_distribution",
        description="Synthetic hotspot distribution (structural reference only).",
        target_distribution=tuple(float(x) for x in arr),
        bins=int(arr.size),
    )


__all__ = [
    "Pattern",
    "activity_diversity_pattern",
    "hotspot_distribution_pattern",
    "pattern_from_samples",
    "time_of_day_pattern",
]
