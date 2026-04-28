"""Synthetic cell-level population allocator (Beckman-style).

This module allocates a regional age-by-sex population into a set of
synthetic-grid cells while preserving the regional marginal totals. It
is the canonical Beckman et al. (1996) synthetic population technique
narrowed to *aggregate* cell counts — we never emit synthetic individual
records, only per-cell age-by-sex tallies.

Allocation method
-----------------
For each ``(age, sex)`` cohort with regional count ``N``, we draw a
multinomial split of ``N`` across ``num_cells`` cells using a Dirichlet
prior parameterised by ``alpha`` (defaults to a flat ``1.0``). Larger
``alpha`` produces more uniform cell allocations; smaller ``alpha``
concentrates population in fewer cells. The construction-time invariant
``sum(cell_counts) == regional_count`` holds exactly per cohort because
``numpy.random.Generator.multinomial`` is exact-integer.

The allocator is **fully deterministic** given an integer seed: the same
inputs produce byte-identical cell tallies. This preserves Luvoire's
auditable replay guarantees.

Civilian Use Policy alignment
-----------------------------
- Output is **aggregate per cell** at the synthetic-grid floor, never
  individual records.
- Cell ids are synthetic strings (``synthetic-grid-r{row}c{col}``), not
  real-world coordinates; ``ethics.no_real_geometry: true`` is preserved.
- The allocator is appropriate for cell-level distribution comparison
  under counterfactual demographic scenarios — never for per-person
  prediction or operational targeting.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from luvoire.demography.projector import (
    DEFAULT_MAX_AGE,
    CohortPopulation,
)


@dataclass(frozen=True, slots=True)
class CellPopulation:
    """Aggregate age-by-sex population for one synthetic-grid cell.

    Attributes:
        cell_id: Synthetic-grid cell id (``synthetic-grid-r{row}c{col}``
            convention) — NOT a real coordinate or polygon.
        male: ``(max_age + 1,)`` non-negative integer counts.
        female: Same shape as ``male`` for females.
    """

    cell_id: str
    male: np.ndarray
    female: np.ndarray

    def __post_init__(self) -> None:
        if not isinstance(self.cell_id, str) or not self.cell_id:
            raise ValueError("cell_id must be a non-empty string")
        male = np.asarray(self.male, dtype=np.int64)
        female = np.asarray(self.female, dtype=np.int64)
        if male.ndim != 1 or female.ndim != 1:
            raise ValueError("male and female must be 1-D arrays")
        if male.shape != female.shape:
            raise ValueError(
                f"male and female arrays must have the same shape "
                f"(got {male.shape} vs {female.shape})"
            )
        if (male < 0).any() or (female < 0).any():
            raise ValueError("cell counts must be non-negative integers")
        # ``np.asarray`` may return the input array view unchanged when
        # dtype matches. We ensure both branches (view vs copy) end up
        # with their own buffer before locking, otherwise locking would
        # also freeze the caller's source array. After the copy we mark
        # the buffers read-only so the frozen-dataclass invariant holds
        # at the **buffer** level too, not just at the attribute level.
        # Round-5 audit hardening.
        male = np.array(male, copy=True)
        female = np.array(female, copy=True)
        male.setflags(write=False)
        female.setflags(write=False)
        object.__setattr__(self, "male", male)
        object.__setattr__(self, "female", female)

    @property
    def total(self) -> int:
        return int(self.male.sum() + self.female.sum())


def _stochastic_dirichlet_split(
    rng: np.random.Generator,
    *,
    counts: np.ndarray,
    num_cells: int,
    alpha: float,
) -> np.ndarray:
    """Allocate each integer count vector entry across ``num_cells``.

    Returns an ``(len(counts), num_cells)`` int64 array whose row sums
    exactly match ``counts``.
    """

    if num_cells <= 0:
        raise ValueError(f"num_cells must be positive (got {num_cells})")
    out = np.zeros((counts.shape[0], num_cells), dtype=np.int64)
    alpha_vec = np.full(num_cells, alpha, dtype=float)
    for i, n in enumerate(counts):
        n_int = int(n)
        if n_int <= 0:
            continue
        weights = rng.dirichlet(alpha_vec)
        out[i] = rng.multinomial(n_int, weights)
    return out


def synthesize_cell_populations(
    population: CohortPopulation,
    *,
    num_cells: int,
    seed: int,
    alpha: float = 1.0,
    cell_id_prefix: str = "synthetic-grid",
) -> tuple[CellPopulation, ...]:
    """Allocate ``population`` into ``num_cells`` synthetic-grid cells.

    Each ``(age, sex)`` cohort is split across cells via a Dirichlet-
    multinomial draw seeded by ``seed``. The exact aggregate invariant
    is **per-cohort**: for each ``(age, sex)`` cell the sum across all
    output cells equals ``round(population.male[age])`` (resp.
    ``population.female[age]``). The integer invariant is byte-exact
    because numpy ``multinomial`` is exact-integer, but it is taken on
    the **per-cohort rounded** values rather than on
    ``population.total`` itself: if ``population.male`` carries non-
    half-integer floats, ``sum(rint(arr))`` is **not generally equal**
    to ``rint(sum(arr))`` (e.g. ``[0.5, 1.5]`` rints to ``[0, 2]`` with
    sum 2 while ``rint(2.0) = 2`` only by coincidence). Callers who
    need exact total preservation should pass an already-integer
    population.

    Parameters
    ----------
    population:
        Regional cohort population to allocate. Float counts are
        rounded to the nearest integer before allocation (KOSTAT
        장래추계 typically rounds at output time anyway).
    num_cells:
        Number of synthetic-grid cells to allocate across. Must be
        positive.
    seed:
        Integer seed for the deterministic Dirichlet-multinomial draw.
    alpha:
        Dirichlet concentration parameter. ``1.0`` (default) gives a
        flat prior; values below ``1.0`` concentrate population in
        fewer cells; values above spread more uniformly.
    cell_id_prefix:
        Prefix for cell ids; the suffix is ``-r{row}c{col}`` with
        cells laid out on a square-ish grid.
    """

    if num_cells <= 0:
        raise ValueError(f"num_cells must be positive (got {num_cells})")
    if alpha <= 0.0:
        raise ValueError(f"alpha must be positive (got {alpha})")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be int")

    rng = np.random.default_rng(seed)

    male_int = np.rint(population.male).astype(np.int64)
    female_int = np.rint(population.female).astype(np.int64)

    male_split = _stochastic_dirichlet_split(
        rng, counts=male_int, num_cells=num_cells, alpha=alpha
    )
    female_split = _stochastic_dirichlet_split(
        rng, counts=female_int, num_cells=num_cells, alpha=alpha
    )

    rows = int(np.ceil(np.sqrt(num_cells)))
    cells: list[CellPopulation] = []
    for cell_index in range(num_cells):
        row = cell_index // rows
        col = cell_index % rows
        cell_id = f"{cell_id_prefix}-r{row}c{col}"
        cells.append(
            CellPopulation(
                cell_id=cell_id,
                male=male_split[:, cell_index],
                female=female_split[:, cell_index],
            )
        )
    return tuple(cells)


def cell_populations_total(cells: tuple[CellPopulation, ...]) -> int:
    """Sum total population across all cells."""

    return int(sum(cell.total for cell in cells))


def aggregate_cells_to_pyramid(cells: tuple[CellPopulation, ...]) -> tuple[np.ndarray, np.ndarray]:
    """Sum cell-level counts back into a regional age pyramid.

    Useful for asserting the aggregate-preservation invariant
    ``aggregate(cells) == original.male, original.female`` in tests
    and reproducibility checks.
    """

    if not cells:
        return np.zeros(DEFAULT_MAX_AGE + 1, dtype=np.int64), np.zeros(
            DEFAULT_MAX_AGE + 1, dtype=np.int64
        )
    male_total = np.zeros_like(cells[0].male)
    female_total = np.zeros_like(cells[0].female)
    for cell in cells:
        male_total += cell.male
        female_total += cell.female
    return male_total, female_total


__all__ = [
    "CellPopulation",
    "aggregate_cells_to_pyramid",
    "cell_populations_total",
    "synthesize_cell_populations",
]
