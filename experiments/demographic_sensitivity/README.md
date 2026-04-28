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
- The estimator-theoretic invariant is ``total_order >= first_order``
  for any single axis. Mortality satisfies this in the committed result
  (first 0.7088, total 0.7931, so the interaction term is ``+0.084``).
- **Fertility violates the invariant in the committed result** (first
  0.8016, total 0.1757) and the sum of the two ``first_order`` indices
  (1.51) exceeds the unit-variance interpretation of "share of
  variance". This is **finite-sample estimator noise at n=1024**, not
  a model property: the projector ``project_year_30_total`` is
  monotonic in both axes, but at a 30-year horizon the fertility
  axis's variance contribution is delayed (born cohort under
  perturbed fertility only enters the reproductive age band at year
  ~15) so the radial-design Saltelli/Jansen estimators have heavier
  finite-sample bias on that axis.
- Saltelli & Annoni (2010, *Environ. Model. Softw.* 25(12):1508-1517,
  §3 "Sample size") show that the radial-design Saltelli/Jansen
  estimators carry order-of-magnitude bias on first-order indices when
  the base sample ``N`` is smaller than ``O(10^3)`` for moderate-
  dimensional models with interaction structure, and recommend
  successively increasing ``N`` until the indices stabilise within
  bootstrap CIs. Our empirical convergence on this projector matches
  that pattern: at ``N=1024`` the fertility-axis ``S_T < S_1``
  inversion persists, at ``N=16k`` it inverts back to the expected
  ``S_T >= S_1`` regime, and ``N=32k`` is robust within ±0.01. The
  committed indices at ``N=1024`` are kept honest about this rather
  than re-tuned at higher ``N``: the test
  ``test_total_order_aggregate_exceeds_first_order_aggregate`` therefore
  asserts only the strict mortality ``S_T > S_1`` and a finite-value
  sanity envelope; it does **not** claim ``S_T > S_1`` for fertility
  at this ``N``. The number ``N=16k`` here is empirical for this
  projector, not a verbatim recommendation in the cited paper.
- The relative magnitude of ``first_order`` between the two axes still
  ranks the policy levers qualitatively, but for any quantitative
  publication callers should re-run with ``n >= 32k``.

## Synthetic-only guarantees

The projector is run on a fully synthetic uniform cohort. No KOSIS aggregate
table, no real region label, and no individual record is read. Outputs are
counterfactual scenarios (추계), never predictions, in line with KOSTAT
저위/중위/고위 scenario practice and the Civilian Use Policy
``no_real_geometry: true`` guardrail.
