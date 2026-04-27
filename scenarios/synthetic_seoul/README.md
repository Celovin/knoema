# Synthetic Seoul-style Scenario (T2.4)

A small, fictional, synthetic urban grid scenario combining the realism-roadmap
T2 building blocks:

- :mod:`luvoire.geo.synthetic_grid` — the 5×5 cell lattice
- :mod:`luvoire.timeuse` — a single empirical prior over the seven activity
  codes (loaded from ``tests/fixtures/timeuse/synthetic_priors_v1.json``)
- :mod:`luvoire.theory.rat` — the locked RAT v1 convergence rule
- Scenario DSL v2 — Tier A/B/C parameter exposure plus the ``no_real_geometry``
  guardrail

This scenario is deliberately **not** a Seoul map. The cell ids are
``synthetic-grid-r{row}c{col}`` and the EPSG label is the synthetic
``luvoire-synthetic-v1``; no real coordinates, no real address resolution, no
real building footprints.

## Files

- ``scenario.yaml`` — the DSL v2 scenario file. Loadable via
  ``luvoire.dsl.v2.load_scenario_v2``.
- ``run_scenario.py`` — committed deterministic builder that materialises the
  5×5 grid + activity samples + an opportunity-event sweep over the cells, and
  writes a JSON summary into ``results/``.
- ``results/synthetic_seoul_summary.json`` — committed run output (seed
  20260427). Same seed reproduces the same byte-identical summary.

## Determinism

Every run is identified by ``(seed, scenario YAML, code tree)``. The summary
records: prior strata, total opportunity events emitted, per-cell event count,
and a SHA-256 over the JSONified result. The replay-equality test compares the
recorded summary to a freshly re-run summary.

## Civilian Use Policy alignment

``ethics.no_real_geometry: true``. Tier A reference is locked
(``code:luvoire.theory.rat.v1``). Tier B prior cites the synthetic Luvoire
fixture, not real KOSTAT microdata. Tier C exploration knob (``threshold``) has
range and default. The scenario does not produce per-person risk scores and is
declared non-predictive.
