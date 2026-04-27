# Methods (canonical, shared by KCI + SSCI drafts)

## 1. Engine surface

The simulator is the open-source Luvoire engine
(``github.com/Celovin/luvoire``, MIT-licensed). Each scenario is described
in a versioned YAML DSL whose ``schema_version`` field selects the v1 or
v2 schema; v2 scenarios additionally declare three categories of
parameters:

- **Tier A** — locked theoretical constants. Tier A entries reference an
  immutable code module by string of the form ``code:luvoire.theory.X.vN``
  and cannot redefine the underlying rule from YAML.
- **Tier B** — empirical priors. Required ``source`` metadata (data
  provenance), optional ``table_id`` / ``license`` / ``revision`` fields,
  and either a single ``value`` or a ``distribution`` reference.
- **Tier C** — exploration knobs. Required ``range`` and ``default``,
  optional ``sweep`` integer for downstream sensitivity tooling.

Routine activity theory enters the engine as Tier A. The ``opportunity_event``
function in ``luvoire.theory.rat`` accepts three components — actor
motivation, target exposure, and capable-guardian gap — and returns a
synthetic opportunity event when the multiplicative convergence
``motivation * exposure * gap`` clears the locked default threshold of
0.125 with all three components observed in the same tick and the same or
adjacent cell. The event kind is locked to the literal
``rat_v1_synthetic_opportunity`` so downstream pipelines cannot
inadvertently consume events from another theory module.

Cell adjacency is delegated to h3 v4 when ``h3-py`` is installed and
falls back to equality on a synthetic-grid label otherwise; both paths
produce identical behaviour for synthetic-grid scenarios used in this
paper.

## 2. Synthetic-only data and the Civilian Use Policy

All scenarios in this paper use a synthetic Korean-style 5x5 (or 6x6)
urban grid with synthetic cell ids of the form
``synthetic-grid-r{row}c{col}``. The DSL v2 ethics block defaults to
``no_real_geometry: true``, which rejects any environment ``epsg`` value
that does not start with ``luvoire-synthetic-``. No real GeoJSON, no
real coordinates, no real victimisation data, and no individual-level
inputs enter the pipeline. The Luvoire Civilian Use Policy v1.0
(``POLICIES/civilian_use.md``) explicitly refuses defense, predictive
policing, PSYOP, non-consenting twinning, and minors-in-synthetic-pipelines
applications.

## 3. Sobol sensitivity sweep

The methodology poster's sensitivity panel uses a deterministic radial
Saltelli design implemented in ``luvoire.sensitivity.sobol``. With
``n = 4096`` base samples (``20 480`` model evaluations) and the seed
``20260427``, first-order Sobol indices for the three RAT inputs sit
near 0.23 each and total-order indices sit near 0.54 each, indicating
roughly 30 percent of the output variance is interaction effects — the
expected property of a multiplicative convergence rule. We validate the
estimator implementation against the Ishigami benchmark (Saltelli 2002).

## 4. Reproducibility infrastructure

Each Luvoire run is identified by a deterministic SHA-256 over
``(code_tree_sha, scenario_yaml_sha, seed, python_version)``. Five
msgpack replay artifacts ship committed SHA-256 baselines that are
re-verified on every push by ``scripts/verify_replay_shas.py``. Two
scenario-level summaries (``synthetic_seoul`` and ``crimemind_compare``)
ship committed ``summary_sha256`` invariants and are re-checked by
``scripts/replay_equality_ci.py``. Same-seed runs reproduce byte-for-byte
across local and CI environments.

## 5. CrimeMind comparison harness

We re-implement the three-slot RAT-prompt structure from CrimeMind
(arXiv:2506.05981, June 2025) as a Tier C weight sweep over the locked
RAT v1 convergence rule and compare three weight regimes — equal weights,
motivation-heavy, and guardian-heavy — across a 6x6 synthetic grid. The
comparison is patterns-level only; CrimeMind's source code and dataset
are not loaded. The harness's purpose is to demonstrate that Tier C
sweeps redistribute synthetic events without touching the Tier A theory.

## 6. Pattern-Oriented Modeling validation gates

Three default macro patterns — time-of-day distribution (G1), activity
diversity (G2), and synthetic hotspot distribution (G3) — are evaluated
via discrete Kolmogorov-Smirnov distance against committed target
distributions. A scenario passes the POM gate when each gate's KS
distance is below its configured threshold; the composite POM score is
``1 - weighted_mean(KS)`` clipped to ``[0, 1]``.
