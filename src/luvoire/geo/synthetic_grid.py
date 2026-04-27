"""Pure-numpy synthetic urban grid generator.

The synthetic grid emits cell ids in the ``synthetic-grid-r{row}c{col}``
format already used by ``tests/test_theory_rat_v1.py`` so RAT v1 fixtures and
new spatial fixtures share the same cell vocabulary.

The grid is a deterministic 2-D rectangular lattice; ``cell_neighbors`` uses
4-connectivity (von Neumann) which is the right default for spatial
convergence on a regular street grid. Diagonal (Moore) neighbourhoods are
intentionally not exposed — the theory module treats a target reached only
via a corner as non-adjacent, matching crime-pattern theory practice.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SyntheticCell:
    """A single cell in a :class:`SyntheticGrid`.

    Attributes:
        cell_id: Stable string id of the form ``synthetic-grid-r{row}c{col}``.
        row: Row index (``0`` is the top row).
        col: Column index (``0`` is the leftmost column).
    """

    cell_id: str
    row: int
    col: int


@dataclass(frozen=True, slots=True)
class SyntheticGrid:
    """A rectangular synthetic urban grid.

    Attributes:
        rows: Number of rows (non-negative).
        cols: Number of columns (non-negative).
        cells: Tuple of :class:`SyntheticCell`, in row-major order.
    """

    rows: int
    cols: int
    cells: tuple[SyntheticCell, ...]


def synthetic_cell_ref(row: int, col: int) -> str:
    """Return the canonical cell-id string for ``(row, col)``.

    The format ``synthetic-grid-r{row}c{col}`` is fixed and matches
    ``tests/test_theory_rat_v1.py``.

    Raises:
        ValueError: When ``row`` or ``col`` is negative.
    """

    if row < 0 or col < 0:
        raise ValueError(f"row and col must be non-negative, got row={row}, col={col}")
    return f"synthetic-grid-r{row}c{col}"


def build_synthetic_grid(rows: int, cols: int) -> SyntheticGrid:
    """Build a :class:`SyntheticGrid` of the given dimensions.

    Identical inputs produce identical outputs (deterministic). ``rows=0`` or
    ``cols=0`` yield an empty cell tuple, which is a valid degenerate grid.

    Raises:
        ValueError: When ``rows`` or ``cols`` is negative.
    """

    if rows < 0 or cols < 0:
        raise ValueError(
            f"rows and cols must be non-negative, got rows={rows}, cols={cols}"
        )
    # numpy is used to materialise the index lattice deterministically.
    if rows == 0 or cols == 0:
        return SyntheticGrid(rows=rows, cols=cols, cells=())
    row_idx, col_idx = np.indices((rows, cols))
    flat_rows = row_idx.reshape(-1)
    flat_cols = col_idx.reshape(-1)
    cells = tuple(
        SyntheticCell(
            cell_id=synthetic_cell_ref(int(r), int(c)),
            row=int(r),
            col=int(c),
        )
        for r, c in zip(flat_rows, flat_cols, strict=True)
    )
    return SyntheticGrid(rows=rows, cols=cols, cells=cells)


def _parse_cell_id(cell_id: str) -> tuple[int, int]:
    prefix = "synthetic-grid-r"
    if not cell_id.startswith(prefix) or "c" not in cell_id[len(prefix) :]:
        raise ValueError(f"not a synthetic-grid cell id: {cell_id!r}")
    body = cell_id[len(prefix) :]
    row_str, _, col_str = body.partition("c")
    try:
        return int(row_str), int(col_str)
    except ValueError as exc:
        raise ValueError(f"not a synthetic-grid cell id: {cell_id!r}") from exc


def cell_neighbors(grid: SyntheticGrid, cell_id: str) -> list[str]:
    """Return the 4-neighbourhood of *cell_id* on *grid*.

    Returns the up-to-four orthogonal neighbours of the cell, in canonical
    order: up, down, left, right. Cells outside the grid bounds are dropped,
    so corner cells return 2 neighbours, edge cells return 3, and interior
    cells return 4.

    Raises:
        ValueError: When *cell_id* is not a valid synthetic-grid id or is not
            within the grid bounds.
    """

    row, col = _parse_cell_id(cell_id)
    if not (0 <= row < grid.rows and 0 <= col < grid.cols):
        raise ValueError(
            f"cell {cell_id!r} is outside grid bounds rows={grid.rows} cols={grid.cols}"
        )
    candidates = (
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    )
    return [
        synthetic_cell_ref(r, c)
        for r, c in candidates
        if 0 <= r < grid.rows and 0 <= c < grid.cols
    ]


__all__ = [
    "SyntheticCell",
    "SyntheticGrid",
    "build_synthetic_grid",
    "cell_neighbors",
    "synthetic_cell_ref",
]
