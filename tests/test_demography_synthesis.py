"""Tests for luvoire.demography.synthesis — synthetic cell-level allocator."""

from __future__ import annotations

import numpy as np
import pytest

from luvoire.demography.projector import (
    DEFAULT_MAX_AGE,
    CohortPopulation,
)
from luvoire.demography.synthesis import (
    CellPopulation,
    aggregate_cells_to_pyramid,
    cell_populations_total,
    synthesize_cell_populations,
)


def _baseline_population(*, count_per_age: float = 100.0) -> CohortPopulation:
    return CohortPopulation(
        year=2026,
        region_label="서울특별시 강남구",
        male=np.full(DEFAULT_MAX_AGE + 1, count_per_age),
        female=np.full(DEFAULT_MAX_AGE + 1, count_per_age),
    )


def test_cell_population_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        CellPopulation(
            cell_id="synthetic-grid-r0c0",
            male=np.array([-1, 1]),
            female=np.array([1, 1]),
        )


def test_cell_population_rejects_empty_cell_id() -> None:
    with pytest.raises(ValueError, match="cell_id"):
        CellPopulation(
            cell_id="",
            male=np.zeros(10, dtype=np.int64),
            female=np.zeros(10, dtype=np.int64),
        )


def test_cell_population_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError, match="same shape"):
        CellPopulation(
            cell_id="synthetic-grid-r0c0",
            male=np.zeros(5, dtype=np.int64),
            female=np.zeros(10, dtype=np.int64),
        )


def test_cell_population_total_sums_both_sexes() -> None:
    cell = CellPopulation(
        cell_id="synthetic-grid-r0c0",
        male=np.array([10, 20], dtype=np.int64),
        female=np.array([15, 25], dtype=np.int64),
    )
    assert cell.total == 70


def test_cell_population_dataclass_has_no_coordinate_fields() -> None:
    """Regression — CellPopulation must NEVER expose coordinate /
    polygon / EPSG / geometry fields. ethics.no_real_geometry: true is
    the whole point of using string cell ids.
    """

    cell = CellPopulation(
        cell_id="synthetic-grid-r0c0",
        male=np.zeros(10, dtype=np.int64),
        female=np.zeros(10, dtype=np.int64),
    )
    forbidden = {
        "lat", "lon", "latitude", "longitude",
        "x", "y",
        "epsg", "geometry", "polygon", "centroid",
        "bbox", "geojson", "wkt", "wkb",
    }
    for attr in forbidden:
        assert not hasattr(cell, attr), (
            f"CellPopulation must not expose coordinate field {attr!r}"
        )


# --- synthesize_cell_populations -----------------------------------------


def test_synthesize_preserves_aggregate_invariant() -> None:
    pop = _baseline_population(count_per_age=100.0)
    cells = synthesize_cell_populations(pop, num_cells=16, seed=42)
    expected_total = round(pop.total)
    assert cell_populations_total(cells) == expected_total


def test_synthesize_preserves_per_cohort_invariant() -> None:
    """sum(cells) over each (age, sex) cohort exactly matches input."""

    pop = _baseline_population(count_per_age=100.0)
    cells = synthesize_cell_populations(pop, num_cells=16, seed=42)
    male_agg, female_agg = aggregate_cells_to_pyramid(cells)
    np.testing.assert_array_equal(
        male_agg, np.rint(pop.male).astype(np.int64)
    )
    np.testing.assert_array_equal(
        female_agg, np.rint(pop.female).astype(np.int64)
    )


def test_synthesize_returns_correct_number_of_cells() -> None:
    pop = _baseline_population()
    cells = synthesize_cell_populations(pop, num_cells=25, seed=7)
    assert len(cells) == 25


def test_synthesize_cell_ids_use_synthetic_grid_prefix() -> None:
    pop = _baseline_population()
    cells = synthesize_cell_populations(pop, num_cells=4, seed=11)
    for cell in cells:
        assert cell.cell_id.startswith("synthetic-grid-r")
        assert "c" in cell.cell_id


def test_synthesize_is_deterministic_under_same_seed() -> None:
    pop = _baseline_population()
    cells_a = synthesize_cell_populations(pop, num_cells=9, seed=42)
    cells_b = synthesize_cell_populations(pop, num_cells=9, seed=42)
    for ca, cb in zip(cells_a, cells_b, strict=True):
        np.testing.assert_array_equal(ca.male, cb.male)
        np.testing.assert_array_equal(ca.female, cb.female)
        assert ca.cell_id == cb.cell_id


def test_synthesize_diverges_under_different_seeds() -> None:
    pop = _baseline_population(count_per_age=100.0)
    cells_a = synthesize_cell_populations(pop, num_cells=16, seed=1)
    cells_b = synthesize_cell_populations(pop, num_cells=16, seed=2)
    male_a = np.array([c.male for c in cells_a])
    male_b = np.array([c.male for c in cells_b])
    assert not np.array_equal(male_a, male_b)


def test_synthesize_low_alpha_increases_cell_variance() -> None:
    """Low alpha → higher variance across cell totals than high alpha.

    Each (age, sex) cohort independently draws Dirichlet weights, so
    spike cells differ per cohort and totals smooth somewhat. We still
    expect alpha=0.01 to produce visibly larger variance across cell
    totals than alpha=100.0 for the same regional population and seed.
    """

    pop = _baseline_population(count_per_age=100.0)
    low = synthesize_cell_populations(pop, num_cells=16, seed=42, alpha=0.01)
    high = synthesize_cell_populations(pop, num_cells=16, seed=42, alpha=100.0)
    var_low = float(np.var([c.total for c in low]))
    var_high = float(np.var([c.total for c in high]))
    assert var_low > var_high


def test_synthesize_rejects_zero_num_cells() -> None:
    pop = _baseline_population()
    with pytest.raises(ValueError, match="num_cells must be positive"):
        synthesize_cell_populations(pop, num_cells=0, seed=1)


def test_synthesize_rejects_non_positive_alpha() -> None:
    pop = _baseline_population()
    with pytest.raises(ValueError, match="alpha must be positive"):
        synthesize_cell_populations(pop, num_cells=4, seed=1, alpha=0.0)


def test_synthesize_rejects_non_int_seed() -> None:
    pop = _baseline_population()
    with pytest.raises(TypeError, match="seed"):
        synthesize_cell_populations(pop, num_cells=4, seed="42")  # type: ignore[arg-type]


def test_synthesize_zero_population_returns_zero_cells() -> None:
    pop = CohortPopulation(
        year=2026,
        region_label="서울특별시 강남구",
        male=np.zeros(DEFAULT_MAX_AGE + 1),
        female=np.zeros(DEFAULT_MAX_AGE + 1),
    )
    cells = synthesize_cell_populations(pop, num_cells=4, seed=1)
    for cell in cells:
        assert cell.total == 0


def test_aggregate_cells_to_pyramid_handles_empty_input() -> None:
    male, female = aggregate_cells_to_pyramid(())
    assert male.sum() == 0
    assert female.sum() == 0


def test_cell_id_prefix_overridable() -> None:
    pop = _baseline_population(count_per_age=10.0)
    cells = synthesize_cell_populations(
        pop, num_cells=4, seed=1, cell_id_prefix="custom-test"
    )
    for cell in cells:
        assert cell.cell_id.startswith("custom-test-r")
