# CrimeMind RAT-prompt Comparison PoC (T3.4)

A self-implemented re-construction of the CrimeMind (arXiv 2506.05981, June
2025) RAT-prompt agent design as a Luvoire scenario, plus a side-by-side
patterns-level comparison harness against `luvoire.theory.rat` v1.

This scenario is a **methodology comparison**, not a CrimeMind reproduction.
The CrimeMind paper is referenced for its RAT-prompt schema (offender +
suitable target + capable guardian decomposed into per-component prompt
slots) and for its multi-modal urban-context idea, both of which we re-
implement here using only the synthetic Luvoire grid. We do not load any
CrimeMind source code or any real-world dataset.

## What this directory ships

- `scenario.yaml` — DSL v2 scenario carrying a Tier A reference to
  `code:luvoire.theory.rat.v1` plus three Tier C exploration knobs over
  the per-component RAT prompt weights.
- `compare.py` — committed deterministic builder. Given the same seed,
  generates the same per-cell event count summary using the locked RAT
  v1 convergence rule under three weight regimes (equal-weight baseline,
  motivation-heavy, guardian-heavy) so reviewers can see how Tier C
  weight sweeps redistribute synthetic events without changing the
  Tier A theory.
- `results/comparison_summary.json` — committed run output with a
  `summary_sha256` invariant.

## Civilian Use Policy alignment

`ethics.no_real_geometry: true`, `ethics.no_prediction: true`, and
`ethics.no_suspect_scoring: true`. The scenario produces no per-person
risk scores, no real coordinates, and no real-event reconstruction.
The CrimeMind paper is cited as a methodological reference only.
