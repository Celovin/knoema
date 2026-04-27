"""PSSDP demand-panel builder for the 30-year demographic scenario.

A separate committed entry point that consumes the same baseline /
counterfactual setup as ``run_scenario.py`` and emits a deterministic
service-demand panel JSON at ``results/demand_panel.json``. The panel
covers fire-ambulance (119), school-age, and patrol-baseline aggregate
demand across the 25-cell synthetic grid for each of the three KOSTAT-
style fertility scenarios.

The builder is independent of ``run_scenario.py``'s
``demography_summary.json`` artefact so the existing replay-equality
SHA stays intact while we add a separate panel SHA.

Civilian Use Policy alignment
-----------------------------
- Output is per-cell aggregate demand, never per-person.
- Demand coefficients are illustrative synthetic baselines (declared
  in :mod:`luvoire.demography.report`); production callers calibrate
  with their own jurisdiction-specific values.
- Output is **decision-support** for municipal planning, not a
  decision-system; ``ethics.pssdp_mode: true`` and the validator
  interlock keep configuration consistent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from luvoire.demography import (  # noqa: E402  -- after sys.path tweak
    KOSTAT_REFERENCE_TRIPLE,
    REPRODUCTIVE_AGE_HI,
    REPRODUCTIVE_AGE_LO,
    CohortComponentProjector,
    CohortPopulation,
    CounterfactualScenarioEngine,
    DemographicRates,
    ServiceDemandCoefficients,
    ServiceDemandReport,
    project_service_demand,
    render_demand_panel,
    synthesize_cell_populations,
)

DEFAULT_SEED = 20260428
HORIZON_YEARS = 30
NUM_CELLS = 25
INITIAL_REGION_LABEL = "서울특별시 강남구"
INITIAL_TOTAL_PER_AGE = 1000.0
RESULTS_DIR = Path(__file__).parent / "results"


def _build_baseline_rates() -> DemographicRates:
    asfr = np.zeros(101)
    asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] = 0.02
    asmr = np.zeros(101)
    asmr[60:80] = 0.02
    asmr[80:] = 0.05
    return DemographicRates(asfr=asfr, asmr_male=asmr, asmr_female=asmr)


def _build_initial_population(year: int = 2026) -> CohortPopulation:
    return CohortPopulation(
        year=year,
        region_label=INITIAL_REGION_LABEL,
        male=np.full(101, INITIAL_TOTAL_PER_AGE),
        female=np.full(101, INITIAL_TOTAL_PER_AGE),
    )


def build_panel(*, seed: int = DEFAULT_SEED) -> tuple[ServiceDemandReport, ...]:
    """Construct the three PSSDP scenario reports."""

    initial = _build_initial_population()
    baseline = _build_baseline_rates()
    projector = CohortComponentProjector()
    engine = CounterfactualScenarioEngine(projector)

    scenario_results = engine.run(
        initial=initial,
        baseline_rates=baseline,
        horizon_years=HORIZON_YEARS,
        scenarios=KOSTAT_REFERENCE_TRIPLE,
    )

    coef = ServiceDemandCoefficients()
    reports: list[ServiceDemandReport] = []
    for scenario_index, sr in enumerate(scenario_results):
        year_h = sr.trajectory[-1]
        cells = synthesize_cell_populations(
            year_h,
            num_cells=NUM_CELLS,
            seed=seed + scenario_index,
        )
        demands = project_service_demand(cells, year=year_h.year, coefficients=coef)
        reports.append(
            ServiceDemandReport(
                scenario_label=sr.label,
                horizon_year=year_h.year,
                region_label=year_h.region_label,
                coefficients=coef,
                cell_demands=demands,
            )
        )
    return tuple(reports)


def write_panel(reports: tuple[ServiceDemandReport, ...]) -> tuple[Path, str]:
    out_path = RESULTS_DIR / "demand_panel.json"
    digest = render_demand_panel(reports, out_path)
    return out_path, digest


def main() -> int:
    reports = build_panel()
    out_path, digest = write_panel(reports)
    print(f"wrote {out_path}")
    print(f"panel_sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
