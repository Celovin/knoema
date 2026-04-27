# 30-Year Synthetic Demographic Scenario (PSSDP demonstration)

A 30-year long-horizon counterfactual demographic projection over a Seoul-
style synthetic 5x5 grid (25 cells). Combines `luvoire.demography` cohort-
component projection, `luvoire.demography.synthesis` Beckman-style cell
allocation, and the locked `luvoire.theory.rat` v1 convergence rule.

## What this scenario demonstrates

For each of three KOSTAT-style fertility scenarios (low / medium / high),
the scenario:

1. Initialises a regional cohort population at year 2026 (synthetic
   uniform pyramid for reproducibility)
2. Projects 30 years forward via the cohort-component method using
   uniform reproductive-age ASFR (TFR 0.70 baseline) and age-stepped
   ASMR
3. Allocates the year-2056 cohort population to 25 synthetic-grid
   cells via Beckman multinomial draw with `alpha=1.0`
4. Applies RAT v1 convergence at every cell with uniform `[0, 1]^3`
   draws
5. Reports per-cell event counts plus a `summary_sha256` invariant

The output shows how aggregate cell-level RAT distributions shift under
different long-horizon fertility regimes — exactly the question the
referenced research direction asks ('how does demographic change move
public-safety service demand over decades?'). Output is **always
aggregate** at the synthetic-grid floor and **never** per-person.

## What this scenario does NOT demonstrate

- It is not a prediction of any real region's future crime, victimisation,
  or service demand. The `summary_sha256` is a deterministic fixture
  invariant, not an estimate.
- It produces **no per-person risk score** and **no real geometry**. Cell
  ids are synthetic strings; region label is an opaque administrative
  string only.
- It is **decision-support** for municipal-planning research, not a
  decision-system for law-enforcement. The DSL v2 ethics block carries
  `pssdp_mode: true` and `demographic_projection: true`; the validator
  rejects any combination that would unlock prediction or suspect
  scoring.

## Civilian Use Policy alignment

The scenario.yaml ethics block:

- `fictional: true`
- `no_real_people: true`
- `no_prediction: true`
- `no_suspect_scoring: true`
- `no_real_geometry: true`
- `demographic_projection: true`
- `pssdp_mode: true`

KOSIS Tier B references (`1B36E27`, `1B40E04`) cite KOGL Type 1 public
statistics; no microdata is bundled or loaded.

## Files

- `scenario.yaml` — DSL v2 declaration
- `run_scenario.py` — committed deterministic builder
- `results/demography_summary.json` — committed run output with
  `summary_sha256`

Same seed (default `20260428`) reproduces byte-identical summaries.
