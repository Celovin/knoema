"""Sobol sensitivity sweep for demographic counterfactual scenarios.

This experiment extends the Sobol variance-decomposition framework already
applied to the RAT v1 convergence rule (see ``experiments/rat_sensitivity``)
to the cohort-component demographic projector in
:mod:`luvoire.demography.projector`.

Two scalar perturbations are swept jointly:

* ``fertility_scale`` — multiplicative factor applied to every age-specific
  fertility rate (ASFR) of the baseline reference rate set.
* ``mortality_scale`` — multiplicative factor applied to every age-specific
  mortality rate (ASMR), clipped to ``[0, 1]`` before being passed to
  :class:`~luvoire.demography.DemographicRates`.

The Sobol model output is the **year-30 total population** under a deterministic
projection of a uniform synthetic cohort (1000.0 per single-year age, per sex).
First-order and total-order indices quantify which axis dominates the
30-year trajectory of the aggregate population total and how much of the
variance comes from interaction between the two axes.

Outputs (committed under ``results/``):

* ``sobol_indices.json`` — first-order + total-order indices per axis.
* ``sobol_indices.md`` — human-readable summary.
* ``run_manifest.json`` — seed, n, model evaluation count, timestamp,
  estimator + module-version provenance.

Civilian Use Policy alignment
-----------------------------
The projector is run on a fully synthetic uniform cohort. No KOSIS aggregate
table, no real region label, and no individual record is read. Outputs are
counterfactual scenarios (추계), never predictions, in line with KOSTAT
저위/중위/고위 scenario practice.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from luvoire.demography.projector import (  # type: ignore[import-untyped]  # noqa: E402
    DEFAULT_MAX_AGE,
    REPRODUCTIVE_AGE_HI,
    REPRODUCTIVE_AGE_LO,
    CohortComponentProjector,
    CohortPopulation,
    DemographicRates,
)
from luvoire.sensitivity.sobol import (  # type: ignore[import-untyped]  # noqa: E402
    SobolIndices,
    saltelli_sample,
    sobol_indices,
)

VARIABLE_NAMES: tuple[str, ...] = ("fertility_scale", "mortality_scale")
BOUNDS: tuple[tuple[float, float], ...] = (
    (0.7, 1.3),
    (0.7, 1.3),
)
DEFAULT_SEED = 20260428
DEFAULT_N = 1024
HORIZON_YEARS = 30
INITIAL_COHORT_VALUE = 1000.0
REGION_LABEL = "synthetic-uniform-cohort"
INITIAL_YEAR = 2026


def _baseline_asfr() -> np.ndarray:
    """Uniform ASFR of 0.02 across the reproductive-age band [15, 50).

    The implied total fertility rate is ``0.02 * (50 - 15) = 0.7`` — well
    below replacement, in the same neighbourhood as Korea's 2024 합계출산율
    of ~0.72. ASFR is zero-padded outside the reproductive ages so the
    :class:`DemographicRates` reproductive-band guard accepts it.
    """

    asfr = np.zeros(DEFAULT_MAX_AGE + 1, dtype=float)
    asfr[REPRODUCTIVE_AGE_LO:REPRODUCTIVE_AGE_HI] = 0.02
    return asfr


def _baseline_asmr() -> np.ndarray:
    """Step age-specific mortality: 0 below 60, 0.02 in [60, 80), 0.05 in [80, max].

    Identical for males and females in this synthetic baseline. Values are
    chosen so the open-ended top class drains gradually rather than
    instantaneously, while still being well within the ``[0, 1]`` validity
    band even after multiplication by ``mortality_scale`` up to ``1.3``.
    """

    asmr = np.zeros(DEFAULT_MAX_AGE + 1, dtype=float)
    asmr[60:80] = 0.02
    asmr[80:] = 0.05
    return asmr


_BASELINE_ASFR = _baseline_asfr()
_BASELINE_ASMR = _baseline_asmr()


def _initial_population() -> CohortPopulation:
    """Uniform 1000.0 per single-year age cohort, per sex."""

    male = np.full(DEFAULT_MAX_AGE + 1, INITIAL_COHORT_VALUE, dtype=float)
    female = np.full(DEFAULT_MAX_AGE + 1, INITIAL_COHORT_VALUE, dtype=float)
    return CohortPopulation(
        year=INITIAL_YEAR,
        region_label=REGION_LABEL,
        male=male,
        female=female,
    )


def _rates_from_scales(fertility_scale: float, mortality_scale: float) -> DemographicRates:
    """Build a :class:`DemographicRates` with the two scale factors applied.

    ``mortality_scale`` is applied first and the result is clipped to
    ``[0, 1]`` so the dataclass validator accepts it. The chosen baseline
    keeps even the ``mortality_scale = 1.3`` case strictly below the upper
    bound (``0.05 * 1.3 = 0.065``), so clipping is a defensive guard rather
    than an active operation under the Sobol bounds.
    """

    asfr = _BASELINE_ASFR * fertility_scale
    asmr = np.clip(_BASELINE_ASMR * mortality_scale, 0.0, 1.0)
    return DemographicRates(
        asfr=asfr,
        asmr_male=asmr,
        asmr_female=asmr,
    )


def project_year_30_total(samples: np.ndarray) -> np.ndarray:
    """Vectorised model wrapper for :func:`luvoire.sensitivity.sobol.sobol_indices`.

    For each row ``(fertility_scale, mortality_scale)`` runs a 30-year
    cohort-component projection on the uniform synthetic cohort and returns
    the total population at year 30. Output is a 1-D array of length ``n``.
    """

    projector = CohortComponentProjector(max_age=DEFAULT_MAX_AGE)
    initial = _initial_population()
    out = np.zeros(samples.shape[0], dtype=float)
    for index, row in enumerate(samples):
        rates = _rates_from_scales(float(row[0]), float(row[1]))
        trajectory = projector.project(initial, rates, HORIZON_YEARS)
        out[index] = trajectory[-1].total
    return out


def run(*, seed: int = DEFAULT_SEED, n: int = DEFAULT_N) -> SobolIndices:
    """Build the Saltelli design and estimate Sobol indices."""

    samples = saltelli_sample(BOUNDS, n=n, seed=seed)
    return sobol_indices(samples, project_year_30_total, VARIABLE_NAMES)


def _format_markdown(indices: SobolIndices, *, seed: int, n: int) -> str:
    d = len(indices.variable_names)
    total_evals = n * (d + 2)
    lines = [
        "# Demographic Sensitivity (Sobol) — Results",
        "",
        f"Seed: ``{seed}`` · base samples ``n = {n}`` · "
        f"total evaluations ``{total_evals}``",
        "",
        f"Horizon: ``{HORIZON_YEARS}`` years · "
        f"initial cohort: uniform ``{INITIAL_COHORT_VALUE}`` per single-year age, per sex",
        "",
        "Baseline rates: TFR ``0.7`` (uniform ASFR ``0.02`` across "
        f"[{REPRODUCTIVE_AGE_LO}, {REPRODUCTIVE_AGE_HI})); "
        "step ASMR ``0.02`` for [60, 80), ``0.05`` for [80, max].",
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
    lines.append(
        "Interpretation: ``first_order`` is the share of variance in year-30 "
        "total population explained by varying that axis alone. "
        "``total_order`` additionally includes interaction with the other axis. "
        "A larger gap (``total_order - first_order``) indicates stronger "
        "fertility-mortality interaction."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    seed = DEFAULT_SEED
    n = DEFAULT_N
    indices = run(seed=seed, n=n)
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    d = len(VARIABLE_NAMES)
    total_evals = n * (d + 2)
    payload = {
        "seed": seed,
        "n": n,
        "model_evaluations": total_evals,
        "horizon_years": HORIZON_YEARS,
        "initial_cohort_value": INITIAL_COHORT_VALUE,
        "bounds": {
            name: list(BOUNDS[i]) for i, name in enumerate(VARIABLE_NAMES)
        },
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
        "experiment": "demographic_sensitivity",
        "module_version": "luvoire.demography.projector.v1",
        "estimator": "saltelli2002_jansen1999_saltelli2010",
        "seed": seed,
        "n_samples": n,
        "eval_count": total_evals,
        "variables": list(VARIABLE_NAMES),
        "bounds": {
            name: list(BOUNDS[i]) for i, name in enumerate(VARIABLE_NAMES)
        },
        "horizon_years": HORIZON_YEARS,
        "initial_cohort_value": INITIAL_COHORT_VALUE,
        "timestamp": datetime.now(UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("wrote", out_dir / "sobol_indices.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
