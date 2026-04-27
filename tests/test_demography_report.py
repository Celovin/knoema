"""Tests for luvoire.demography.report — PSSDP service-demand projector."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from luvoire.demography.report import (
    DEFAULT_FIRE_PER_1000_ELDERLY,
    DEFAULT_PATROL_PER_1000_TOTAL,
    DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE,
    ELDERLY_AGE_FLOOR,
    SCHOOL_AGE_HI,
    SCHOOL_AGE_LO,
    ServiceDemandCoefficients,
    ServiceDemandProjection,
    ServiceDemandReport,
    project_service_demand,
    render_demand_panel,
)
from luvoire.demography.synthesis import CellPopulation


def _flat_cell(*, cell_id: str = "synthetic-grid-r0c0", count: int = 100) -> CellPopulation:
    return CellPopulation(
        cell_id=cell_id,
        male=np.full(101, count, dtype=np.int64),
        female=np.full(101, count, dtype=np.int64),
    )


# --- ServiceDemandCoefficients ------------------------------------------


def test_coefficients_default_constants_are_finite_positive() -> None:
    coef = ServiceDemandCoefficients()
    assert coef.fire_per_1000_elderly == DEFAULT_FIRE_PER_1000_ELDERLY
    assert coef.school_per_1000_school_age == DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE
    assert coef.patrol_per_1000_total == DEFAULT_PATROL_PER_1000_TOTAL


def test_coefficients_reject_negative_value() -> None:
    with pytest.raises(ValueError, match="fire_per_1000_elderly"):
        ServiceDemandCoefficients(fire_per_1000_elderly=-1.0)


def test_coefficients_reject_non_numeric() -> None:
    with pytest.raises(TypeError, match="patrol_per_1000_total"):
        ServiceDemandCoefficients(patrol_per_1000_total="2")  # type: ignore[arg-type]


def test_coefficients_is_frozen() -> None:
    coef = ServiceDemandCoefficients()
    with pytest.raises(AttributeError):
        coef.fire_per_1000_elderly = 99.0  # type: ignore[misc]


# --- ServiceDemandProjection --------------------------------------------


def test_projection_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        ServiceDemandProjection(
            cell_id="x",
            year=2026,
            elderly_population=-1.0,
            school_age_population=0.0,
            total_population=10.0,
            fire_ambulance_demand=0.0,
            school_age_demand=0.0,
            patrol_baseline_demand=0.0,
        )


def test_projection_rejects_empty_cell_id() -> None:
    with pytest.raises(ValueError, match="cell_id"):
        ServiceDemandProjection(
            cell_id="",
            year=2026,
            elderly_population=0.0,
            school_age_population=0.0,
            total_population=0.0,
            fire_ambulance_demand=0.0,
            school_age_demand=0.0,
            patrol_baseline_demand=0.0,
        )


def test_projection_to_dict_returns_floats() -> None:
    proj = ServiceDemandProjection(
        cell_id="x",
        year=2026,
        elderly_population=10.0,
        school_age_population=20.0,
        total_population=100.0,
        fire_ambulance_demand=0.35,
        school_age_demand=1.5,
        patrol_baseline_demand=0.2,
    )
    payload = proj.to_dict()
    assert payload["cell_id"] == "x"
    assert payload["year"] == 2026
    assert isinstance(payload["fire_ambulance_demand"], float)


# --- project_service_demand --------------------------------------------


def test_project_service_demand_uses_default_coefficients() -> None:
    cell = _flat_cell(count=100)  # 101 ages * 100 each * 2 sexes = 20200
    projections = project_service_demand((cell,), year=2026)
    assert len(projections) == 1
    p = projections[0]
    expected_elderly = float(2 * 100 * (101 - ELDERLY_AGE_FLOOR))
    expected_school = float(2 * 100 * (SCHOOL_AGE_HI - SCHOOL_AGE_LO))
    expected_total = expected_elderly  # not the proxy — total is full sum
    expected_total = float(2 * 100 * 101)
    assert p.elderly_population == expected_elderly
    assert p.school_age_population == expected_school
    assert p.total_population == expected_total
    assert p.fire_ambulance_demand == pytest.approx(
        expected_elderly * DEFAULT_FIRE_PER_1000_ELDERLY / 1000.0
    )
    assert p.school_age_demand == pytest.approx(
        expected_school * DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE / 1000.0
    )
    assert p.patrol_baseline_demand == pytest.approx(
        expected_total * DEFAULT_PATROL_PER_1000_TOTAL / 1000.0
    )


def test_project_service_demand_zero_population_returns_zero_demand() -> None:
    cell = CellPopulation(
        cell_id="empty",
        male=np.zeros(101, dtype=np.int64),
        female=np.zeros(101, dtype=np.int64),
    )
    projections = project_service_demand((cell,), year=2026)
    p = projections[0]
    assert p.fire_ambulance_demand == 0.0
    assert p.school_age_demand == 0.0
    assert p.patrol_baseline_demand == 0.0


def test_project_service_demand_custom_coefficients_apply() -> None:
    cell = _flat_cell(count=10)
    custom = ServiceDemandCoefficients(
        fire_per_1000_elderly=100.0,
        school_per_1000_school_age=0.0,
        patrol_per_1000_total=0.0,
    )
    projections = project_service_demand((cell,), year=2026, coefficients=custom)
    p = projections[0]
    assert p.fire_ambulance_demand > 0
    assert p.school_age_demand == 0.0
    assert p.patrol_baseline_demand == 0.0


def test_project_service_demand_rejects_non_int_year() -> None:
    cell = _flat_cell()
    with pytest.raises(TypeError, match="year"):
        project_service_demand((cell,), year="2026")  # type: ignore[arg-type]


def test_project_service_demand_preserves_cell_order() -> None:
    cells = (
        _flat_cell(cell_id="synthetic-grid-r0c0", count=5),
        _flat_cell(cell_id="synthetic-grid-r0c1", count=10),
        _flat_cell(cell_id="synthetic-grid-r0c2", count=15),
    )
    projections = project_service_demand(cells, year=2026)
    assert tuple(p.cell_id for p in projections) == tuple(c.cell_id for c in cells)


# --- ServiceDemandReport / render_demand_panel ---------------------------


def _make_report(label: str = "medium_fertility", count: int = 100) -> ServiceDemandReport:
    cells = (
        _flat_cell(cell_id="synthetic-grid-r0c0", count=count),
        _flat_cell(cell_id="synthetic-grid-r0c1", count=count + 10),
    )
    projections = project_service_demand(cells, year=2056)
    return ServiceDemandReport(
        scenario_label=label,
        horizon_year=2056,
        region_label="서울특별시 강남구",
        coefficients=ServiceDemandCoefficients(),
        cell_demands=projections,
    )


def test_report_aggregate_demand_sums_cells() -> None:
    report = _make_report()
    totals = report.aggregate_demand()
    assert (
        totals["fire_ambulance_demand"]
        == sum(p.fire_ambulance_demand for p in report.cell_demands)
    )
    assert (
        totals["school_age_demand"]
        == sum(p.school_age_demand for p in report.cell_demands)
    )
    assert (
        totals["patrol_baseline_demand"]
        == sum(p.patrol_baseline_demand for p in report.cell_demands)
    )


def test_report_to_dict_round_trips_via_json() -> None:
    report = _make_report()
    payload = report.to_dict()
    re_serialised = json.loads(json.dumps(payload, ensure_ascii=False))
    assert re_serialised["scenario_label"] == "medium_fertility"
    assert re_serialised["region_label"] == "서울특별시 강남구"
    assert len(re_serialised["cell_demands"]) == 2


def test_render_demand_panel_writes_deterministic_json(tmp_path: Path) -> None:
    reports = (_make_report("low_fertility", 80), _make_report("medium_fertility", 100))
    out = tmp_path / "panel.json"
    digest_a = render_demand_panel(reports, out)
    digest_b = render_demand_panel(reports, out)
    assert digest_a == digest_b
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["panel_sha256"] == digest_a
    assert "scenarios" in payload
    assert "aggregate_totals_per_scenario" in payload


def test_render_demand_panel_diverges_on_different_inputs(tmp_path: Path) -> None:
    out = tmp_path / "panel.json"
    a = render_demand_panel((_make_report(count=50),), out)
    b = render_demand_panel((_make_report(count=150),), out)
    assert a != b
