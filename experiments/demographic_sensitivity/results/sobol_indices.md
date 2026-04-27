# Demographic Sensitivity (Sobol) — Results

Seed: ``20260428`` · base samples ``n = 1024`` · total evaluations ``4096``

Horizon: ``30`` years · initial cohort: uniform ``1000.0`` per single-year age, per sex

Baseline rates: TFR ``0.7`` (uniform ASFR ``0.02`` across [15, 50)); step ASMR ``0.02`` for [60, 80), ``0.05`` for [80, max].

| Variable | First-order | Total-order |
| --- | ---: | ---: |
| fertility_scale | 0.8016 | 0.1757 |
| mortality_scale | 0.7088 | 0.7931 |

Indices are estimated via Saltelli 2002 (radial design) with Jansen 1999 / Saltelli 2010 estimators.

Interpretation: ``first_order`` is the share of variance in year-30 total population explained by varying that axis alone. ``total_order`` additionally includes interaction with the other axis. A larger gap (``total_order - first_order``) indicates stronger fertility-mortality interaction.
