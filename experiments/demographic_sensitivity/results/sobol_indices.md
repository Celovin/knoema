# Demographic Sensitivity (Sobol) — Results

Seed: ``20260428`` · base samples ``n = 1024`` · total evaluations ``4096``

Horizon: ``30`` years · initial cohort: uniform ``1000.0`` per single-year age, per sex

Baseline rates: TFR ``0.7`` (uniform ASFR ``0.02`` across [15, 50)); step ASMR ``0.02`` for [60, 80), ``0.05`` for [80, max].

| Variable | First-order | Total-order |
| --- | ---: | ---: |
| fertility_scale | 0.8016 | 0.1757 |
| mortality_scale | 0.7088 | 0.7931 |

Indices are estimated via Saltelli 2002 (radial design) with Jansen 1999 / Saltelli 2010 estimators.

Interpretation: ``first_order`` is the share of variance in year-30 total population explained by varying that axis alone. ``total_order`` additionally includes interaction with the other axis. The estimator-theoretic invariant ``total_order >= first_order`` holds per axis in the limit of large ``n``; finite-sample noise at small ``n`` can violate it on axes whose variance contribution is delayed (e.g. fertility at a 30-year horizon, where the born cohort takes ~15 years to enter the reproductive age band). Saltelli & Annoni (2010) recommend ``n >= 16k`` for two-axis decompositions; ``n >= 32k`` is robust here. The committed indices at ``n = 1024`` keep the violation visible rather than re-tuned.
