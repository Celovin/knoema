# RAT Sensitivity (Sobol)

Sobol first-order and total-order sensitivity analysis over the three RAT
inputs of :func:`luvoire.theory.rat.opportunity_event` — actor motivation,
target exposure, and guardianship gap — measuring their relative contribution
to the synthetic opportunity-event rate.

This experiment is part of the ASC 2026 methodology poster (T1 #3) and feeds
the Method panel showing variable-importance heatmaps.

## Run

```bash
python experiments/rat_sensitivity/run.py
```

Outputs (committed):

- `results/sobol_indices.json` — first-order and total-order indices per variable
- `results/sobol_indices.md` — human-readable summary table
- `results/run_manifest.json` — seed, sample count, model evaluation count, version

## Determinism

Every result is keyed by ``(seed, n, model_version)``. The default
``seed=20260427``, ``n=4096``, gives ``4096 * 5 = 20480`` model evaluations and
takes well under one second on a laptop. The sobol estimator is the Saltelli
2002 / Jansen 1999 / Saltelli 2010 radial form (matching SALib defaults) and is
implemented in :mod:`luvoire.sensitivity.sobol` without a SALib dependency.

## Synthetic-only guarantees

This experiment uses no real-world data. The opportunity-event rate it reports
is the average rate at which the locked RAT convergence condition fires when
the three input scalars are sampled uniformly over the unit cube. It is not a
victimisation rate, not a crime rate, and not a place-level risk score.
