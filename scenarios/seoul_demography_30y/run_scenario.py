"""Deterministic builder for the 30-year synthetic demographic scenario.

Runs three counterfactual fertility scenarios (low / medium / high) for
30 years over a Seoul-style synthetic 5x5 grid (25 cells). For each
scenario, the year-30 cohort population is allocated to cells via the
Beckman-style multinomial allocator, then the locked luvoire.theory.rat
v1 convergence rule is applied at every cell to count synthetic
opportunity events under uniform `[0, 1]^3` (motivation, exposure, gap)
draws. Output is per-scenario per-cell event counts plus a SHA-256 of
the deterministic summary.

This builder is **fully deterministic** given the same seed. It loads
no real microdata and emits no per-person output — every cell value
is an aggregate count. The scenario.yaml ethics block carries
``demographic_projection: true`` and ``pssdp_mode: true`` to label
the use case as Public Safety Service Demand Projection (decision-
support for municipal planning), not a decision-system.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

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
    synthesize_cell_populations,
)
from luvoire.theory.rat import (  # noqa: E402
    ActorState,
    GuardianshipGap,
    TargetExposure,
    opportunity_event,
)

DEFAULT_SEED = 20260428
HORIZON_YEARS = 30
NUM_CELLS = 25  # 5x5 grid
INITIAL_REGION_LABEL = "서울특별시 강남구"
INITIAL_TOTAL_PER_AGE = 1000.0  # uniform initial pyramid for reproducibility
RESULTS_DIR = Path(__file__).parent / "results"


def _build_baseline_rates() -> DemographicRates:
    """Construct a flat reproducible baseline rate set.

    ASFR is uniform across reproductive ages (TFR 0.7 in line with
    Korea 2024 reference); ASMR is age-stepped (low <60, mid 60-79,
    high 80+); migration is zero. Real KOSIS rates would replace
    these in a production scenario; here we keep the curve simple
    so the byte-stable summary is easy to re-derive.
    """

    asfr = np.zeros(101)
    asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] = 0.02  # TFR 0.70
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


def _count_cell_events(
    cells: tuple,  # tuple[CellPopulation, ...] — typed as tuple to avoid runtime cycle
    *,
    seed: int,
) -> dict[str, int]:
    """Apply RAT v1 convergence at each cell with uniform [0, 1]^3 draws.

    The cell's aggregate population is used as the seed perturbation
    only — we draw one (motivation, exposure, gap) triplet per cell
    and check the locked convergence threshold. This produces a per-
    cell event count of 0 or 1 per scenario.
    """

    rng = np.random.default_rng(seed)
    counts: dict[str, int] = {}
    tick = 0
    for index, cell in enumerate(cells):
        motivation = float(rng.uniform(0.0, 1.0))
        exposure = float(rng.uniform(0.0, 1.0))
        gap = float(rng.uniform(0.0, 1.0))
        actor = ActorState(
            actor_id=f"actor-{index}",
            motivation=motivation,
            cell=cell.cell_id,
            tick=tick,
        )
        target = TargetExposure(
            target_id=f"target-{index}",
            exposure=exposure,
            cell=cell.cell_id,
            tick=tick,
        )
        guardian = GuardianshipGap(
            place_id=f"place-{index}",
            gap=gap,
            cell=cell.cell_id,
            tick=tick,
        )
        event = opportunity_event(
            actor_state=actor,
            target=target,
            guardianship=guardian,
            tick=tick,
            cell=cell.cell_id,
        )
        counts[cell.cell_id] = 1 if event is not None else 0
    return counts


def run(*, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    """Execute the 30-year three-fertility-scenario comparison.

    The function is deterministic. Returns a JSON-serialisable summary
    dict with per-scenario cell-level event counts and a stable
    ``summary_sha256``.
    """

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

    per_scenario: dict[str, Any] = {}
    for scenario_index, sr in enumerate(scenario_results):
        year_h = sr.trajectory[-1]
        # Allocate year-30 cohort to NUM_CELLS via Beckman multinomial.
        cells = synthesize_cell_populations(
            year_h,
            num_cells=NUM_CELLS,
            seed=seed + scenario_index,
        )
        events = _count_cell_events(cells, seed=seed + 1000 + scenario_index)
        per_scenario[sr.label] = {
            "year": year_h.year,
            "region_label": year_h.region_label,
            "year_h_total": round(year_h.total),
            "fertility_scale": sr.perturbation.fertility_scale,
            "cells_with_events": sum(events.values()),
            "per_cell_events": events,
        }

    summary: dict[str, Any] = {
        "scenario_id": "seoul_demography_30y",
        "seed": seed,
        "horizon_years": HORIZON_YEARS,
        "num_cells": NUM_CELLS,
        "baseline_tfr": float(baseline.total_fertility_rate),
        "scenarios": per_scenario,
    }
    payload = json.dumps(summary, sort_keys=True, ensure_ascii=False).encode("utf-8")
    summary["summary_sha256"] = hashlib.sha256(payload).hexdigest()
    return summary


def write_results(summary: dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "demography_summary.json"
    out_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path


def main() -> int:
    summary = run()
    out_path = write_results(summary)
    print(f"wrote {out_path}")
    print(f"summary_sha256: {summary['summary_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
