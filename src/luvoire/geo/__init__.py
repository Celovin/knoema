"""Luvoire geo subpackage — GIS readiness for synthetic urban grids.

This subpackage provides three small, optional-runtime helpers used by the
spatial layers of Luvoire:

* :mod:`luvoire.geo.h3_index` — h3-py v4 thin wrapper with a fallback that
  matches the equality-only adjacency rule used in
  :func:`luvoire.theory.rat._same_or_adjacent_cell`.
* :mod:`luvoire.geo.synthetic_grid` — pure-numpy synthetic urban grid
  generator emitting cell ids in the ``synthetic-grid-r{row}c{col}`` format
  already adopted by ``tests/test_theory_rat_v1.py``.
* :mod:`luvoire.geo.synthetic_polygon` — optional Shapely-backed polygon
  helpers with a tuple-of-corners fallback when shapely is not installed.

All three modules degrade gracefully when their optional third-party
dependency is absent. The ``H3Unavailable`` exception is raised by functions
that strictly require ``h3``; ``ShapelyUnavailable`` is defined for symmetry
but is reserved for future strict-shapely helpers.
"""

from __future__ import annotations

from luvoire.geo.h3_index import (
    H3Unavailable,
    cell_to_centroid_latlon,
    is_h3_v4_string,
    same_or_adjacent,
)
from luvoire.geo.h3_index import cell_neighbors as h3_cell_neighbors
from luvoire.geo.synthetic_grid import (
    SyntheticCell,
    SyntheticGrid,
    build_synthetic_grid,
    synthetic_cell_ref,
)
from luvoire.geo.synthetic_grid import cell_neighbors as synthetic_cell_neighbors
from luvoire.geo.synthetic_polygon import (
    ShapelyUnavailable,
    cell_polygon,
    polygon_centroid,
)

__all__ = [
    "H3Unavailable",
    "ShapelyUnavailable",
    "SyntheticCell",
    "SyntheticGrid",
    "build_synthetic_grid",
    "cell_polygon",
    "cell_to_centroid_latlon",
    "h3_cell_neighbors",
    "is_h3_v4_string",
    "polygon_centroid",
    "same_or_adjacent",
    "synthetic_cell_neighbors",
    "synthetic_cell_ref",
]
