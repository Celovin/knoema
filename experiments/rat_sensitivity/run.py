"""Sobol sensitivity sweep for the RAT v1 convergence rule.

Outputs deterministic JSON and Markdown summaries to ``results/`` so the ASC
2026 methodology Method panel and the run manifest can be committed and
re-derived from a clean checkout. No SALib dependency.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from luvoire.sensitivity.sobol import (  # noqa: E402  -- after sys.path tweak
    SobolIndices,
    saltelli_sample,
    sobol_indices,
)
from luvoire.theory.rat import (  # noqa: E402
    DEFAULT_CONVERGENCE_THRESHOLD,
    ActorState,
    GuardianshipGap,
    TargetExposure,
    opportunity_event,
)

VARIABLE_NAMES: tuple[str, ...] = ("motivation", "exposure", "gap")
BOUNDS: tuple[tuple[float, float], ...] = (
    (0.0, 1.0),
    (0.0, 1.0),
    (0.0, 1.0),
)
DEFAULT_SEED = 20260427
DEFAULT_N = 4096
CELL = "synthetic-grid-r0c0"
TICK = 0


def opportunity_rate(samples: np.ndarray) -> np.ndarray:
    """Vectorised wrapper that runs ``opportunity_event`` per row.

    Returns an array of 0/1 (event emitted? per the locked threshold) so the
    Sobol estimator can integrate the indicator function. We do not vary the
    threshold here — that is the Tier C parameter sweep, separately.
    """

    out = np.zeros(samples.shape[0], dtype=float)
    for index, row in enumerate(samples):
        actor = ActorState(
            actor_id="a", motivation=float(row[0]), cell=CELL, tick=TICK
        )
        target = TargetExposure(
            target_id="t", exposure=float(row[1]), cell=CELL, tick=TICK
        )
        guardian = GuardianshipGap(
            place_id="p", gap=float(row[2]), cell=CELL, tick=TICK
        )
        event = opportunity_event(actor, target, guardian, tick=TICK, cell=CELL)
        out[index] = 0.0 if event is None else 1.0
    return out


def run(*, seed: int = DEFAULT_SEED, n: int = DEFAULT_N) -> SobolIndices:
    samples = saltelli_sample(BOUNDS, n=n, seed=seed)
    return sobol_indices(samples, opportunity_rate, VARIABLE_NAMES)


def _format_markdown(indices: SobolIndices, *, seed: int, n: int) -> str:
    lines = [
        "# RAT Sensitivity (Sobol) — Results",
        "",
        f"Seed: ``{seed}`` · base samples ``n = {n}`` · "
        f"total evaluations ``{n * 5}``",
        "",
        f"Convergence threshold (locked): ``{DEFAULT_CONVERGENCE_THRESHOLD}``",
        "",
        "| Variable | First-order | Total-order |",
        "| --- | ---: | ---: |",
    ]
    for name in indices.variable_names:
        entry = indices.as_dict()[name]
        lines.append(
            f"| {name} | {entry['first_order']:.4f} | "
            f"{entry['total_order']:.4f} |"
        )
    lines.append("")
    lines.append(
        "Indices are estimated via Saltelli 2002 (radial design) "
        "with Jansen 1999 / Saltelli 2010 estimators."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    seed = DEFAULT_SEED
    n = DEFAULT_N
    indices = run(seed=seed, n=n)
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "seed": seed,
        "n": n,
        "model_evaluations": n * 5,
        "threshold": DEFAULT_CONVERGENCE_THRESHOLD,
        "variables": indices.as_dict(),
    }
    (out_dir / "sobol_indices.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "sobol_indices.md").write_text(
        _format_markdown(indices, seed=seed, n=n),
        encoding="utf-8",
    )
    manifest = {
        "experiment": "rat_sensitivity",
        "module_version": "luvoire.theory.rat.v1",
        "estimator": "saltelli2002_jansen1999_saltelli2010",
        "seed": seed,
        "n": n,
        "model_evaluations": n * 5,
        "variables": list(VARIABLE_NAMES),
        "threshold": DEFAULT_CONVERGENCE_THRESHOLD,
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("wrote", out_dir / "sobol_indices.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
