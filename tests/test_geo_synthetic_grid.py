"""Tests for luvoire.geo.synthetic_grid — pure-numpy synthetic urban grid."""

from __future__ import annotations

import pytest

from luvoire.geo.synthetic_grid import (
    SyntheticCell,
    build_synthetic_grid,
    cell_neighbors,
    synthetic_cell_ref,
)


def test_synthetic_cell_ref_format_matches_rat_v1_fixtures() -> None:
    # The format is also asserted by tests/test_theory_rat_v1.py constants.
    assert synthetic_cell_ref(3, 4) == "synthetic-grid-r3c4"
    assert synthetic_cell_ref(0, 0) == "synthetic-grid-r0c0"


def test_synthetic_cell_ref_rejects_negative_inputs() -> None:
    with pytest.raises(ValueError):
        synthetic_cell_ref(-1, 0)
    with pytest.raises(ValueError):
        synthetic_cell_ref(0, -1)


def test_build_synthetic_grid_dimensions() -> None:
    grid = build_synthetic_grid(rows=4, cols=5)
    assert grid.rows == 4
    assert grid.cols == 5
    assert len(grid.cells) == 20


def test_build_synthetic_grid_row_major_order() -> None:
    grid = build_synthetic_grid(rows=2, cols=3)
    expected = [
        SyntheticCell(cell_id="synthetic-grid-r0c0", row=0, col=0),
        SyntheticCell(cell_id="synthetic-grid-r0c1", row=0, col=1),
        SyntheticCell(cell_id="synthetic-grid-r0c2", row=0, col=2),
        SyntheticCell(cell_id="synthetic-grid-r1c0", row=1, col=0),
        SyntheticCell(cell_id="synthetic-grid-r1c1", row=1, col=1),
        SyntheticCell(cell_id="synthetic-grid-r1c2", row=1, col=2),
    ]
    assert list(grid.cells) == expected


def test_build_synthetic_grid_is_deterministic() -> None:
    a = build_synthetic_grid(rows=3, cols=3)
    b = build_synthetic_grid(rows=3, cols=3)
    assert a == b
    assert a.cells == b.cells


def test_build_synthetic_grid_zero_rows() -> None:
    grid = build_synthetic_grid(rows=0, cols=4)
    assert grid.rows == 0
    assert grid.cols == 4
    assert grid.cells == ()


def test_build_synthetic_grid_zero_cols() -> None:
    grid = build_synthetic_grid(rows=4, cols=0)
    assert grid.rows == 4
    assert grid.cols == 0
    assert grid.cells == ()


def test_build_synthetic_grid_rejects_negative_dimensions() -> None:
    with pytest.raises(ValueError):
        build_synthetic_grid(rows=-1, cols=3)
    with pytest.raises(ValueError):
        build_synthetic_grid(rows=3, cols=-1)


def test_synthetic_grid_is_frozen() -> None:
    grid = build_synthetic_grid(rows=2, cols=2)
    with pytest.raises((AttributeError, TypeError)):
        grid.rows = 99  # type: ignore[misc]


def test_synthetic_cell_is_frozen() -> None:
    cell = SyntheticCell(cell_id="synthetic-grid-r0c0", row=0, col=0)
    with pytest.raises((AttributeError, TypeError)):
        cell.row = 99  # type: ignore[misc]


def test_cell_neighbors_interior_returns_four() -> None:
    grid = build_synthetic_grid(rows=4, cols=4)
    neighbours = cell_neighbors(grid, synthetic_cell_ref(1, 1))
    assert len(neighbours) == 4
    assert set(neighbours) == {
        synthetic_cell_ref(0, 1),
        synthetic_cell_ref(2, 1),
        synthetic_cell_ref(1, 0),
        synthetic_cell_ref(1, 2),
    }


def test_cell_neighbors_corner_returns_two() -> None:
    grid = build_synthetic_grid(rows=3, cols=3)
    top_left = cell_neighbors(grid, synthetic_cell_ref(0, 0))
    assert len(top_left) == 2
    assert set(top_left) == {
        synthetic_cell_ref(1, 0),
        synthetic_cell_ref(0, 1),
    }
    bottom_right = cell_neighbors(grid, synthetic_cell_ref(2, 2))
    assert len(bottom_right) == 2
    assert set(bottom_right) == {
        synthetic_cell_ref(1, 2),
        synthetic_cell_ref(2, 1),
    }


def test_cell_neighbors_edge_returns_three() -> None:
    grid = build_synthetic_grid(rows=3, cols=3)
    top_edge = cell_neighbors(grid, synthetic_cell_ref(0, 1))
    assert len(top_edge) == 3
    assert set(top_edge) == {
        synthetic_cell_ref(0, 0),
        synthetic_cell_ref(0, 2),
        synthetic_cell_ref(1, 1),
    }


def test_cell_neighbors_canonical_order_is_up_down_left_right() -> None:
    grid = build_synthetic_grid(rows=3, cols=3)
    interior = cell_neighbors(grid, synthetic_cell_ref(1, 1))
    assert interior == [
        synthetic_cell_ref(0, 1),
        synthetic_cell_ref(2, 1),
        synthetic_cell_ref(1, 0),
        synthetic_cell_ref(1, 2),
    ]


def test_cell_neighbors_rejects_unknown_cell_id_format() -> None:
    grid = build_synthetic_grid(rows=2, cols=2)
    with pytest.raises(ValueError):
        cell_neighbors(grid, "not-a-cell")


def test_cell_neighbors_rejects_out_of_bounds_cell() -> None:
    grid = build_synthetic_grid(rows=2, cols=2)
    with pytest.raises(ValueError):
        cell_neighbors(grid, synthetic_cell_ref(5, 5))


def test_grid_cells_are_hashable() -> None:
    grid = build_synthetic_grid(rows=2, cols=2)
    # Frozen dataclasses are hashable by default; ensure the tuple of cells
    # can live inside a set.
    assert len(set(grid.cells)) == 4
