"""Tiny h3-py v4 wrapper with optional-import fallback.

The Luvoire spatial layer treats h3-py as an optional dependency. Functions
that strictly require the runtime raise :class:`H3Unavailable` when ``h3`` is
not importable; functions that have a meaningful equality-only fallback (such
as :func:`same_or_adjacent`) mirror the behaviour already used in
:func:`luvoire.theory.rat._same_or_adjacent_cell` so spatial reasoning stays
consistent across the codebase regardless of installation state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import-time only
    pass


class H3Unavailable(RuntimeError):  # noqa: N818 — public exception name pinned by spec
    """Raised when an h3-only operation is requested but ``h3`` is missing.

    The exception inherits from :class:`RuntimeError` so callers that already
    catch ``RuntimeError`` for environment problems will continue to handle
    the missing-runtime case without code changes.
    """


def is_h3_v4_string(value: str) -> bool:
    """Return ``True`` if *value* looks like an h3 v4 cell index.

    h3 v4 cell indices are 15-character lowercase hexadecimal strings. This
    helper performs a syntactic check only; it does not require ``h3`` to be
    importable. The check mirrors
    :func:`luvoire.theory.rat._is_h3_v4_string` so behaviour is consistent
    across modules.
    """

    if len(value) != 15:
        return False
    return all(ch in "0123456789abcdef" for ch in value)


def cell_neighbors(cell: str, k: int = 1) -> list[str]:
    """Return the ``k``-ring of cells around *cell* (excluding *cell* itself).

    Requires ``h3`` to be installed. Raises :class:`H3Unavailable` otherwise.

    Args:
        cell: An h3 v4 cell string.
        k: Ring radius. ``k=1`` returns the six immediate neighbours.

    Raises:
        H3Unavailable: When the ``h3`` runtime is not importable.
        ValueError: When *cell* is not a valid-looking h3 v4 string or when
            ``k`` is negative.
    """

    if k < 0:
        raise ValueError("k must be non-negative")
    if not is_h3_v4_string(cell):
        raise ValueError(f"not an h3 v4 cell string: {cell!r}")
    try:
        import h3  # type: ignore[import-not-found,import-untyped,unused-ignore]
    except ModuleNotFoundError as exc:
        raise H3Unavailable(
            "h3 is required for cell_neighbors; install with `pip install h3`"
        ) from exc
    disk = list(h3.grid_disk(cell, k))
    return [c for c in disk if c != cell]


def same_or_adjacent(a: str, b: str) -> bool:
    """Return ``True`` if *a* and *b* are equal or h3-adjacent.

    When ``h3`` is not installed this collapses to plain equality, mirroring
    :func:`luvoire.theory.rat._same_or_adjacent_cell` so the convergence rule
    in the theory module behaves identically whether or not the optional
    runtime is present.
    """

    if a == b:
        return True
    if not is_h3_v4_string(a) or not is_h3_v4_string(b):
        return False
    try:
        import h3  # type: ignore[import-not-found,import-untyped,unused-ignore]
    except ModuleNotFoundError:
        return False
    return bool(h3.are_neighbor_cells(a, b))


def cell_to_centroid_latlon(cell: str) -> tuple[float, float]:
    """Return the ``(lat, lon)`` centroid of *cell*.

    Requires ``h3`` to be installed. Raises :class:`H3Unavailable` otherwise.

    Raises:
        H3Unavailable: When the ``h3`` runtime is not importable.
        ValueError: When *cell* is not a valid-looking h3 v4 string.
    """

    if not is_h3_v4_string(cell):
        raise ValueError(f"not an h3 v4 cell string: {cell!r}")
    try:
        import h3  # type: ignore[import-not-found,import-untyped,unused-ignore]
    except ModuleNotFoundError as exc:
        raise H3Unavailable(
            "h3 is required for cell_to_centroid_latlon; install with `pip install h3`"
        ) from exc
    lat, lon = h3.cell_to_latlng(cell)
    return float(lat), float(lon)


__all__ = [
    "H3Unavailable",
    "cell_neighbors",
    "cell_to_centroid_latlon",
    "is_h3_v4_string",
    "same_or_adjacent",
]
