"""Public Safety Service Demand Projection (PSSDP) report generator.

Translates aggregate cell-level demographic projections into aggregate
projections of municipal-planning service demand: fire / ambulance (119)
calls, school-age population, and patrol-shift baseline. The output is
**always aggregate per cell** and is intended as **decision-support for
municipal planning**, not as a decision-system or per-person prediction.

Demand proxies
--------------
The demand coefficients are linear ratios over single-year age cohorts.
Defaults are illustrative (chosen to produce sensible orders of
magnitude on synthetic input) and are **not** calibrated to any real
Korean municipal dataset. Production callers are expected to supply
their own coefficients via the :class:`ServiceDemandCoefficients`
dataclass and are responsible for the interpretation.

- Fire / ambulance (119) demand: scales primarily with the 65+
  population (consistent with KOSTAT / NEMA aggregate trend reports
  that elderly residents drive ambulance call volume).
- School-age demand: scales with the 6-18 cohort (Korean compulsory
  + secondary education window).
- Patrol baseline demand: scales with total population (a planning
  rule of thumb at the municipal level).

Civilian Use Policy alignment
-----------------------------
- All output is per-cell aggregate; per-person ranking is forbidden by
  module construction (we operate on :class:`CellPopulation` not on
  individuals).
- This module is **decision-support** for planning, not a
  decision-system; it is **not** an LE deployment tool. The
  Scenario DSL v2 ``pssdp_mode: true`` flag and the validator
  interlock (``no_prediction``, ``no_suspect_scoring``) keep
  configuration consistent.
- Demand proxies are projections (추계), not predictions (예측). Use
  multiple counterfactual fertility / mortality scenarios to compare
  trajectories rather than single-point forecasts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from luvoire.demography.synthesis import CellPopulation

DEFAULT_FIRE_PER_1000_ELDERLY: float = 35.0
"""Synthetic illustrative baseline: 35 ambulance calls per 1000
residents aged 65+ per year. Not calibrated to any real Korean
municipal dataset."""

DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE: float = 75.0
"""Synthetic illustrative baseline: 75 'school capacity units' per
1000 school-age (6-18) residents per year. Not calibrated."""

DEFAULT_PATROL_PER_1000_TOTAL: float = 2.0
"""Synthetic illustrative baseline: 2 patrol shifts per 1000 total
residents per year. Not calibrated."""

ELDERLY_AGE_FLOOR: int = 65
SCHOOL_AGE_LO: int = 6
SCHOOL_AGE_HI: int = 19  # exclusive upper bound; ages 6..18 inclusive


@dataclass(frozen=True, slots=True)
class ServiceDemandCoefficients:
    """Per-1000 demand coefficients for the three service categories.

    Defaults are illustrative synthetic baselines; production callers
    should supply calibrated values per their own jurisdiction.
    """

    fire_per_1000_elderly: float = DEFAULT_FIRE_PER_1000_ELDERLY
    school_per_1000_school_age: float = DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE
    patrol_per_1000_total: float = DEFAULT_PATROL_PER_1000_TOTAL

    def __post_init__(self) -> None:
        for name in (
            "fire_per_1000_elderly",
            "school_per_1000_school_age",
            "patrol_per_1000_total",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a real number")
            if value < 0:
                raise ValueError(f"{name} must be non-negative (got {value})")


@dataclass(frozen=True, slots=True)
class ServiceDemandProjection:
    """Aggregate service-demand projection for one cell at one year."""

    cell_id: str
    year: int
    elderly_population: float
    school_age_population: float
    total_population: float
    fire_ambulance_demand: float
    school_age_demand: float
    patrol_baseline_demand: float

    def __post_init__(self) -> None:
        if not isinstance(self.cell_id, str) or not self.cell_id:
            raise ValueError("cell_id must be a non-empty string")
        for name in (
            "elderly_population",
            "school_age_population",
            "total_population",
            "fire_ambulance_demand",
            "school_age_demand",
            "patrol_baseline_demand",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a real number")
            if value < 0:
                raise ValueError(f"{name} must be non-negative (got {value})")

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "year": self.year,
            "elderly_population": float(self.elderly_population),
            "school_age_population": float(self.school_age_population),
            "total_population": float(self.total_population),
            "fire_ambulance_demand": float(self.fire_ambulance_demand),
            "school_age_demand": float(self.school_age_demand),
            "patrol_baseline_demand": float(self.patrol_baseline_demand),
        }


@dataclass(frozen=True, slots=True)
class ServiceDemandReport:
    """Per-scenario, per-year, per-cell service-demand projection."""

    scenario_label: str
    horizon_year: int
    region_label: str
    coefficients: ServiceDemandCoefficients
    cell_demands: tuple[ServiceDemandProjection, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_label": self.scenario_label,
            "horizon_year": self.horizon_year,
            "region_label": self.region_label,
            "coefficients": {
                "fire_per_1000_elderly": self.coefficients.fire_per_1000_elderly,
                "school_per_1000_school_age": self.coefficients.school_per_1000_school_age,
                "patrol_per_1000_total": self.coefficients.patrol_per_1000_total,
            },
            "cell_demands": [d.to_dict() for d in self.cell_demands],
        }

    def aggregate_demand(self) -> dict[str, float]:
        """Sum each demand category across all cells."""

        totals = {
            "fire_ambulance_demand": 0.0,
            "school_age_demand": 0.0,
            "patrol_baseline_demand": 0.0,
        }
        for d in self.cell_demands:
            totals["fire_ambulance_demand"] += d.fire_ambulance_demand
            totals["school_age_demand"] += d.school_age_demand
            totals["patrol_baseline_demand"] += d.patrol_baseline_demand
        return totals


def _require_supports_age(cell: CellPopulation, *, age: int) -> None:
    """Raise ValueError if ``cell`` cannot represent the requested age.

    The PSSDP coefficients are calibrated against age 65+ and 6-18 ranges;
    a cell whose age vector is shorter would silently slice to zero and
    misreport demand as zero. We surface the shape mismatch instead so
    callers can see why a coefficient regression test would fail.
    """

    length = int(cell.male.shape[0])
    if length <= age:
        raise ValueError(
            f"cell {cell.cell_id!r} age vector length {length} cannot index "
            f"age {age}; PSSDP demand coefficients require length > {age}"
        )


def _elderly_count(cell: CellPopulation) -> float:
    _require_supports_age(cell, age=ELDERLY_AGE_FLOOR)
    return float(cell.male[ELDERLY_AGE_FLOOR:].sum() + cell.female[ELDERLY_AGE_FLOOR:].sum())


def _school_age_count(cell: CellPopulation) -> float:
    _require_supports_age(cell, age=SCHOOL_AGE_HI - 1)
    return float(
        cell.male[SCHOOL_AGE_LO:SCHOOL_AGE_HI].sum()
        + cell.female[SCHOOL_AGE_LO:SCHOOL_AGE_HI].sum()
    )


def project_service_demand(
    cells: tuple[CellPopulation, ...],
    *,
    year: int,
    coefficients: ServiceDemandCoefficients | None = None,
) -> tuple[ServiceDemandProjection, ...]:
    """Convert per-cell aggregate populations into per-cell service demand.

    The function is purely arithmetic; no randomness, no LLM, no
    external calls. Callers can swap ``coefficients`` for their own
    calibrated values.
    """

    if not isinstance(year, int) or isinstance(year, bool):
        raise TypeError("year must be int")
    coef = coefficients or ServiceDemandCoefficients()
    out: list[ServiceDemandProjection] = []
    for cell in cells:
        elderly = _elderly_count(cell)
        school_age = _school_age_count(cell)
        total = float(cell.total)
        fire = elderly * coef.fire_per_1000_elderly / 1000.0
        school = school_age * coef.school_per_1000_school_age / 1000.0
        patrol = total * coef.patrol_per_1000_total / 1000.0
        out.append(
            ServiceDemandProjection(
                cell_id=cell.cell_id,
                year=year,
                elderly_population=elderly,
                school_age_population=school_age,
                total_population=total,
                fire_ambulance_demand=fire,
                school_age_demand=school,
                patrol_baseline_demand=patrol,
            )
        )
    return tuple(out)


def render_demand_panel(
    reports: tuple[ServiceDemandReport, ...],
    output_path: Path,
) -> str:
    """Write a deterministic JSON panel and return its SHA-256 hex digest.

    The panel is a JSON object with one entry per scenario, each
    carrying the per-cell demand projections plus an aggregate-totals
    block. The function is fully deterministic given the same inputs;
    the hash digest is stable across runs.
    """

    panel = {
        "scenarios": [report.to_dict() for report in reports],
        "aggregate_totals_per_scenario": {
            report.scenario_label: report.aggregate_demand() for report in reports
        },
    }
    payload = json.dumps(panel, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    panel["panel_sha256"] = digest

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(panel, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return digest


__all__ = [
    "DEFAULT_FIRE_PER_1000_ELDERLY",
    "DEFAULT_PATROL_PER_1000_TOTAL",
    "DEFAULT_SCHOOL_PER_1000_SCHOOL_AGE",
    "ELDERLY_AGE_FLOOR",
    "SCHOOL_AGE_HI",
    "SCHOOL_AGE_LO",
    "ServiceDemandCoefficients",
    "ServiceDemandProjection",
    "ServiceDemandReport",
    "project_service_demand",
    "render_demand_panel",
]
