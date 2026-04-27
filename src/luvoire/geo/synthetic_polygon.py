"""Optional Shapely-backed polygon helpers with a pure-Python fallback.

These helpers let downstream code reason about cell geometry without forcing
Shapely as a hard dependency. When Shapely is installed
:func:`cell_polygon` returns a :class:`shapely.geometry.Polygon`; otherwise
it returns a 4-tuple of ``(x, y)`` corner coordinates in counter-clockwise
order. :func:`polygon_centroid` accepts either representation.

The :class:`ShapelyUnavailable` exception is defined for symmetry with
:class:`luvoire.geo.h3_index.H3Unavailable` and is reserved for future
strict-Shapely helpers (e.g. union, buffer). None of the functions in this
module raise it, so existing callers do not need a try/except guard.
"""

from __future__ import annotations

from typing import Any

CornerTuple = tuple[
    tuple[float, float],
    tuple[float, float],
    tuple[float, float],
    tuple[float, float],
]
"""4-tuple of ``(x, y)`` corner coordinates, counter-clockwise from origin."""

PolygonLike = CornerTuple | Any
"""Either a :class:`CornerTuple` or a :class:`shapely.geometry.Polygon`."""


class ShapelyUnavailable(RuntimeError):  # noqa: N818 — public exception name pinned by spec
    """Raised when a strict-Shapely operation is requested but unavailable.

    Reserved for future helpers that cannot meaningfully degrade (e.g.
    boolean polygon operations). Functions defined in this module never raise
    it — they fall back to the corner-tuple representation instead.
    """


def _try_import_shapely() -> Any | None:
    try:
        from shapely.geometry import (  # type: ignore[import-not-found,import-untyped,unused-ignore]
            Polygon,
        )
    except ModuleNotFoundError:
        return None
    return Polygon


def cell_polygon(row: int, col: int, *, side: float = 1.0) -> PolygonLike:
    """Return the square polygon for cell ``(row, col)``.

    The polygon is axis-aligned with side length ``side`` and its lower-left
    corner anchored at ``(col * side, -row * side)`` so that increasing
    ``row`` moves the polygon downward in screen coordinates (matching the
    row-major orientation of :class:`luvoire.geo.synthetic_grid.SyntheticGrid`).

    When Shapely is installed a :class:`shapely.geometry.Polygon` is
    returned; otherwise a :class:`CornerTuple` of four ``(x, y)`` corners in
    counter-clockwise order. This function never raises on missing Shapely.

    Raises:
        ValueError: When ``row`` or ``col`` is negative or ``side`` is not
            strictly positive.
    """

    if row < 0 or col < 0:
        raise ValueError(f"row and col must be non-negative, got row={row}, col={col}")
    if side <= 0:
        raise ValueError(f"side must be > 0, got {side}")

    x0 = float(col) * float(side)
    y0 = -float(row) * float(side)
    x1 = x0 + float(side)
    y1 = y0 - float(side)

    # Counter-clockwise from lower-left in screen space (y grows downward).
    corners: CornerTuple = (
        (x0, y1),  # lower-left
        (x1, y1),  # lower-right
        (x1, y0),  # upper-right
        (x0, y0),  # upper-left
    )

    polygon_cls = _try_import_shapely()
    if polygon_cls is None:
        return corners
    return polygon_cls(corners)


def polygon_centroid(polygon: PolygonLike) -> tuple[float, float]:
    """Return the ``(cx, cy)`` centroid of *polygon*.

    Accepts either a :class:`shapely.geometry.Polygon` (when Shapely is
    available and the caller passed one) or a :class:`CornerTuple` from the
    fallback path. The centroid for the corner-tuple branch is computed as
    the arithmetic mean of the four corners — exact for convex quadrilaterals
    such as the axis-aligned squares produced by :func:`cell_polygon`.

    Raises:
        TypeError: When *polygon* is neither a Shapely Polygon nor a 4-tuple
            of 2-tuples of floats.
    """

    polygon_cls = _try_import_shapely()
    if polygon_cls is not None and isinstance(polygon, polygon_cls):
        centroid = polygon.centroid
        return float(centroid.x), float(centroid.y)

    if (
        isinstance(polygon, tuple)
        and len(polygon) == 4
        and all(isinstance(pt, tuple) and len(pt) == 2 for pt in polygon)
    ):
        xs = [float(pt[0]) for pt in polygon]
        ys = [float(pt[1]) for pt in polygon]
        return sum(xs) / 4.0, sum(ys) / 4.0

    raise TypeError(
        "polygon must be a shapely Polygon or a 4-tuple of (x, y) corners"
    )


__all__ = [
    "CornerTuple",
    "PolygonLike",
    "ShapelyUnavailable",
    "cell_polygon",
    "polygon_centroid",
]
