"""Patterns-level comparison harness for the CrimeMind RAT-prompt design.

The harness mirrors CrimeMind's three-slot prompt structure (motivation /
exposure / guardian-gap) by rescaling the three RAT v1 inputs with per-
component Tier C weights, then runs the locked convergence rule across a
6x6 synthetic grid. Output is a JSON summary recording the event count
under each weight regime plus a SHA-256 of the summary.
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

from luvoire.geo.synthetic_grid import build_synthetic_grid  # noqa: E402
from luvoire.theory.rat import (  # noqa: E402
    DEFAULT_CONVERGENCE_THRESHOLD,
    ActorState,
    GuardianshipGap,
    TargetExposure,
    opportunity_event,
)

DEFAULT_SEED = 20260427
GRID_ROWS = 6
GRID_COLS = 6
RESULTS_DIR = Path(__file__).parent / "results"


REGIMES: tuple[tuple[str, float, float, float], ...] = (
    ("equal_weights", 1.0, 1.0, 1.0),
    ("motivation_heavy", 1.0, 0.5, 0.5),
    ("guardian_heavy", 0.5, 0.5, 1.0),
)


def _events_under(
    rng: np.random.Generator,
    motivation_w: float,
    exposure_w: float,
    gap_w: float,
) -> int:
    grid = build_synthetic_grid(GRID_ROWS, GRID_COLS)
    count = 0
    for index, cell in enumerate(grid.cells):
        m = float(rng.uniform(0.0, 1.0)) * motivation_w
        e = float(rng.uniform(0.0, 1.0)) * exposure_w
        g = float(rng.uniform(0.0, 1.0)) * gap_w
        actor = ActorState(actor_id=f"a{index}", motivation=m, cell=cell.cell_id, tick=0)
        target = TargetExposure(target_id=f"t{index}", exposure=e, cell=cell.cell_id, tick=0)
        guardian = GuardianshipGap(place_id=f"p{index}", gap=g, cell=cell.cell_id, tick=0)
        event = opportunity_event(
            actor,
            target,
            guardian,
            tick=0,
            cell=cell.cell_id,
            threshold=DEFAULT_CONVERGENCE_THRESHOLD,
        )
        if event is not None:
            count += 1
    return count


def run(*, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "scenario_id": "crimemind_compare_v1",
        "seed": seed,
        "grid_rows": GRID_ROWS,
        "grid_cols": GRID_COLS,
        "threshold": DEFAULT_CONVERGENCE_THRESHOLD,
        "regimes": [],
    }
    for name, mw, ew, gw in REGIMES:
        rng = np.random.default_rng(seed)  # reset per regime for fair compare
        count = _events_under(rng, mw, ew, gw)
        summary["regimes"].append(
            {
                "name": name,
                "motivation_weight": mw,
                "exposure_weight": ew,
                "guardian_gap_weight": gw,
                "events": count,
            }
        )
    summary["summary_sha256"] = hashlib.sha256(
        json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return summary


def main() -> int:
    summary = run()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "comparison_summary.json"
    out_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
