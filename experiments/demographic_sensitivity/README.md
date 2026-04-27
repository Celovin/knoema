# Demographic Sensitivity (Sobol)

Sobol first-order and total-order sensitivity analysis over the two scalar
counterfactual axes of the cohort-component projector
(:mod:`luvoire.demography.projector`):

- ``fertility_scale`` — multiplicative factor on the baseline age-specific
  fertility rate (ASFR), bounded ``[0.7, 1.3]``.
- ``mortality_scale`` — multiplicative factor on the baseline age-specific
  mortality rate (ASMR), bounded ``[0.7, 1.3]`` and clipped to ``[0, 1]``
  before being passed to :class:`~luvoire.demography.DemographicRates`.

The Sobol model output is the **year-30 total population** under a
deterministic projection of a uniform synthetic cohort (1000.0 per
single-year age, per sex). The decomposition quantifies which axis
dominates the 30-year aggregate-population trajectory and how much of the
variance comes from the fertility×mortality interaction.

This complements ``experiments/rat_sensitivity`` (which decomposes the RAT
v1 convergence rule) by extending the same Sobol/Saltelli machinery to
demographic counterfactual scenarios (KOSTAT 저위/중위/고위 style).

## Run

```bash
python experiments/demographic_sensitivity/run_experiment.py
```

Outputs (committed under ``results/``):

- `results/sobol_indices.json` — first-order and total-order indices per axis.
- `results/sobol_indices.md` — human-readable summary table.
- `results/run_manifest.json` — seed, ``n_samples``, ``eval_count``,
  ``timestamp``, estimator, module-version provenance.

## Determinism

Every result is keyed by ``(seed, n, module_version)``. The default
``seed=20260428``, ``n=1024``, gives ``1024 * (2 + 2) = 4096`` model
evaluations and runs in well under a minute on a laptop. The Sobol
estimator is the Saltelli 2002 / Jansen 1999 / Saltelli 2010 radial form
implemented in :mod:`luvoire.sensitivity.sobol` (no SALib dependency).

For a fixed seed, ``sobol_indices.json`` is byte-identical across runs;
this is asserted by ``tests/test_demographic_sensitivity_experiment.py``.

## Interpretation

- ``first_order``: variance in year-30 total population explained by
  varying that axis alone (with the other axis averaged out).
- ``total_order``: additionally includes interaction with the other axis.
- ``total_order > first_order`` for both axes is expected because cohort
  attrition and birth flows interact non-linearly over a 30-year horizon
  (the survivors of today's reproductive cohort under a perturbed mortality
  schedule are themselves the parents of the year-30 cohort).
- The relative magnitude of ``first_order`` between the two axes ranks the
  policy levers: the larger one is the axis to perturb first when
  exploring a counterfactual scenario portfolio.

## Synthetic-only guarantees

The projector is run on a fully synthetic uniform cohort. No KOSIS aggregate
table, no real region label, and no individual record is read. Outputs are
counterfactual scenarios (추계), never predictions, in line with KOSTAT
저위/중위/고위 scenario practice and the Civilian Use Policy
``no_real_geometry: true`` guardrail.
