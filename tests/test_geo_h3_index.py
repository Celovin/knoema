"""Tests for luvoire.geo.h3_index — h3 wrapper with optional-import fallback."""

from __future__ import annotations

import pytest

from luvoire.geo.h3_index import (
    H3Unavailable,
    cell_neighbors,
    cell_to_centroid_latlon,
    is_h3_v4_string,
    same_or_adjacent,
)

H3_CELL = "8830e1ad81fffff"


def test_is_h3_v4_string_accepts_15_char_lowercase_hex() -> None:
    assert is_h3_v4_string(H3_CELL) is True


def test_is_h3_v4_string_rejects_wrong_length() -> None:
    assert is_h3_v4_string("8830e1ad81fffffx") is False
    assert is_h3_v4_string("8830e1ad81fffff0") is False
    assert is_h3_v4_string("") is False


def test_is_h3_v4_string_rejects_non_hex() -> None:
    # 15 chars but a non-hex character.
    assert is_h3_v4_string("8830e1ad81fffzz") is False


def test_is_h3_v4_string_rejects_uppercase() -> None:
    # h3 v4 indices are lowercase hex; uppercase must be rejected.
    assert is_h3_v4_string(H3_CELL.upper()) is False


def test_same_or_adjacent_equality_fallback_unconditional() -> None:
    # Equality branch never needs h3.
    assert same_or_adjacent("synthetic-grid-r0c0", "synthetic-grid-r0c0") is True


def test_same_or_adjacent_distinct_synthetic_returns_false() -> None:
    # Non-h3 distinct strings are never adjacent under the fallback.
    assert same_or_adjacent("synthetic-grid-r0c0", "synthetic-grid-r0c1") is False


def test_same_or_adjacent_invalid_h3_returns_false() -> None:
    assert same_or_adjacent("not-a-cell", "also-not-a-cell") is False


def test_cell_neighbors_raises_on_invalid_cell_string() -> None:
    with pytest.raises(ValueError):
        cell_neighbors("not-a-cell")


def test_cell_neighbors_raises_on_negative_k() -> None:
    with pytest.raises(ValueError):
        cell_neighbors(H3_CELL, k=-1)


def test_h3_unavailable_inherits_runtime_error() -> None:
    assert issubclass(H3Unavailable, RuntimeError)


def test_cell_neighbors_raises_h3_unavailable_when_h3_missing() -> None:
    try:
        import h3  # type: ignore[import-not-found]  # noqa: F401
    except ModuleNotFoundError:
        with pytest.raises(H3Unavailable):
            cell_neighbors(H3_CELL)
    else:
        pytest.skip("h3 is installed; missing-runtime path not exercised here")


def test_cell_to_centroid_latlon_raises_h3_unavailable_when_h3_missing() -> None:
    try:
        import h3  # type: ignore[import-not-found]  # noqa: F401
    except ModuleNotFoundError:
        with pytest.raises(H3Unavailable):
            cell_to_centroid_latlon(H3_CELL)
    else:
        pytest.skip("h3 is installed; missing-runtime path not exercised here")


def test_cell_neighbors_returns_six_when_h3_installed() -> None:
    pytest.importorskip("h3")
    neighbours = cell_neighbors(H3_CELL, k=1)
    assert len(neighbours) == 6
    assert H3_CELL not in neighbours
    assert all(is_h3_v4_string(c) for c in neighbours)


def test_same_or_adjacent_h3_neighbour_pair_when_h3_installed() -> None:
    h3 = pytest.importorskip("h3")
    disk = list(h3.grid_disk(H3_CELL, 1))
    other = next(c for c in disk if c != H3_CELL)
    assert same_or_adjacent(H3_CELL, other) is True


def test_cell_to_centroid_latlon_returns_floats_when_h3_installed() -> None:
    pytest.importorskip("h3")
    lat, lon = cell_to_centroid_latlon(H3_CELL)
    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert -90.0 <= lat <= 90.0
    assert -180.0 <= lon <= 180.0
