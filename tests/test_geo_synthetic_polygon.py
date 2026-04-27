"""Tests for luvoire.geo.synthetic_polygon — Shapely-optional polygon helpers."""

from __future__ import annotations

import pytest

from luvoire.geo.synthetic_polygon import (
    ShapelyUnavailable,
    cell_polygon,
    polygon_centroid,
)


def test_shapely_unavailable_inherits_runtime_error() -> None:
    assert issubclass(ShapelyUnavailable, RuntimeError)


def test_cell_polygon_fallback_returns_four_corner_tuple_when_shapely_missing() -> None:
    try:
        import shapely  # type: ignore[import-not-found]  # noqa: F401
    except ModuleNotFoundError:
        polygon = cell_polygon(0, 0, side=1.0)
        assert isinstance(polygon, tuple)
        assert len(polygon) == 4
        for pt in polygon:
            assert isinstance(pt, tuple)
            assert len(pt) == 2
    else:
        pytest.skip("shapely is installed; fallback path not exercised here")


def test_cell_polygon_fallback_corner_coordinates() -> None:
    try:
        import shapely  # type: ignore[import-not-found]  # noqa: F401
    except ModuleNotFoundError:
        polygon = cell_polygon(0, 0, side=1.0)
        # Lower-left, lower-right, upper-right, upper-left (CCW in screen space).
        assert polygon == ((0.0, -1.0), (1.0, -1.0), (1.0, 0.0), (0.0, 0.0))
    else:
        pytest.skip("shapely is installed; fallback path not exercised here")


def test_cell_polygon_fallback_offset_by_row_and_col() -> None:
    try:
        import shapely  # type: ignore[import-not-found]  # noqa: F401
    except ModuleNotFoundError:
        polygon = cell_polygon(2, 3, side=2.0)
        # x0 = 3 * 2.0 = 6.0, y0 = -2 * 2.0 = -4.0, x1 = 8.0, y1 = -6.0
        assert polygon == ((6.0, -6.0), (8.0, -6.0), (8.0, -4.0), (6.0, -4.0))
    else:
        pytest.skip("shapely is installed; fallback path not exercised here")


def test_cell_polygon_rejects_non_positive_side() -> None:
    with pytest.raises(ValueError):
        cell_polygon(0, 0, side=0.0)
    with pytest.raises(ValueError):
        cell_polygon(0, 0, side=-1.0)


def test_cell_polygon_rejects_negative_row_or_col() -> None:
    with pytest.raises(ValueError):
        cell_polygon(-1, 0)
    with pytest.raises(ValueError):
        cell_polygon(0, -1)


def test_polygon_centroid_fallback_for_unit_square_at_origin() -> None:
    polygon = cell_polygon(0, 0, side=1.0)
    cx, cy = polygon_centroid(polygon)
    # Pure-fallback path: centroid is mean of the four corners.
    # For the unit square at row=0, col=0: centroid is (0.5, -0.5).
    assert cx == pytest.approx(0.5)
    assert cy == pytest.approx(-0.5)


def test_polygon_centroid_fallback_for_offset_square() -> None:
    polygon = cell_polygon(2, 3, side=2.0)
    cx, cy = polygon_centroid(polygon)
    # x range [6, 8], y range [-6, -4]; centroid is (7, -5).
    assert cx == pytest.approx(7.0)
    assert cy == pytest.approx(-5.0)


def test_polygon_centroid_rejects_garbage() -> None:
    with pytest.raises(TypeError):
        polygon_centroid("not a polygon")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        polygon_centroid(((0.0, 0.0), (1.0, 0.0)))  # type: ignore[arg-type]


def test_cell_polygon_returns_shapely_polygon_when_installed() -> None:
    pytest.importorskip("shapely")
    from shapely.geometry import Polygon

    polygon = cell_polygon(0, 0, side=1.0)
    assert isinstance(polygon, Polygon)


def test_polygon_centroid_accepts_shapely_polygon() -> None:
    pytest.importorskip("shapely")
    polygon = cell_polygon(0, 0, side=1.0)
    cx, cy = polygon_centroid(polygon)
    assert cx == pytest.approx(0.5)
    assert cy == pytest.approx(-0.5)
