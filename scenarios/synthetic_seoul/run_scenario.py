"""Deterministic builder for the synthetic Seoul-style 5x5 scenario.

Combines :mod:`luvoire.geo.synthetic_grid`, :mod:`luvoire.timeuse`, and
:mod:`luvoire.theory.rat` into a single committed run that emits a
JSON summary to ``results/synthetic_seoul_summary.json``.

This is a methodology demo, not a prediction system. The run sweeps the locked
RAT v1 convergence rule across every cell of a 5x5 synthetic grid using a
seeded numpy RNG. No real-world data is loaded.
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

from luvoire.geo.synthetic_grid import (  # noqa: E402  -- after sys.path tweak
    build_synthetic_grid,
)
from luvoire.theory.rat import (  # noqa: E402
    DEFAULT_CONVERGENCE_THRESHOLD,
    ActorState,
    GuardianshipGap,
    TargetExposure,
    opportunity_event,
)
from luvoire.timeuse.priors import EmpiricalCdfSampler, load_priors_from_json  # noqa: E402

DEFAULT_SEED = 20260427
GRID_ROWS = 5
GRID_COLS = 5
PRIOR_FIXTURE = ROOT / "tests" / "fixtures" / "timeuse" / "synthetic_priors_v1.json"
RESULTS_DIR = Path(__file__).parent / "results"


def _sample_inputs(rng: np.random.Generator) -> tuple[float, float, float]:
    """Sample (motivation, exposure, gap) uniformly on [0, 1]^3."""

    motivation = float(rng.uniform(0.0, 1.0))
    exposure = float(rng.uniform(0.0, 1.0))
    gap = float(rng.uniform(0.0, 1.0))
    return motivation, exposure, gap


def run(*, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    grid = build_synthetic_grid(GRID_ROWS, GRID_COLS)
    rng = np.random.default_rng(seed)
    priors = load_priors_from_json(PRIOR_FIXTURE)
    activity_sampler = EmpiricalCdfSampler(priors[0], seed=seed)
    activity_samples = activity_sampler.sample_many(len(grid.cells))

    cell_event_counts: dict[str, int] = {cell.cell_id: 0 for cell in grid.cells}
    total_events = 0
    tick = 0

    for index, cell in enumerate(grid.cells):
        motivation, exposure, gap = _sample_inputs(rng)
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
            actor,
            target,
            guardian,
            tick=tick,
            cell=cell.cell_id,
            threshold=DEFAULT_CONVERGENCE_THRESHOLD,
        )
        if event is not None:
            cell_event_counts[cell.cell_id] += 1
            total_events += 1

    summary = {
        "scenario_id": "synthetic_seoul_5x5",
        "seed": seed,
        "grid_rows": GRID_ROWS,
        "grid_cols": GRID_COLS,
        "threshold": DEFAULT_CONVERGENCE_THRESHOLD,
        "prior_strata": {
            "day_type": priors[0].strata.day_type,
            "age_band": priors[0].strata.age_band,
            "occupation": priors[0].strata.occupation,
        },
        "activity_sample": list(activity_samples[:5]),
        "total_opportunity_events": total_events,
        "cells_with_events": sum(1 for n in cell_event_counts.values() if n > 0),
        "per_cell_events": cell_event_counts,
    }
    summary["summary_sha256"] = hashlib.sha256(
        json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return summary


def main() -> int:
    summary = run()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "synthetic_seoul_summary.json"
    out_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
