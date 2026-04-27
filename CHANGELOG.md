# Changelog

All notable changes to Knoema Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `scenarios/seoul_demography_30y/` — committed deterministic 30-year demographic projection scenario over a Seoul-style synthetic 5x5 grid (25 cells). Combines `luvoire.demography` cohort-component projection, `luvoire.demography.synthesis` Beckman-style cell allocation, and the locked `luvoire.theory.rat` v1 convergence rule. Three KOSTAT-style fertility scenarios (low / medium / high) produce parallel year-2056 trajectories; cell-level RAT distributions are compared. `scenario.yaml` carries `demographic_projection: true` + `pssdp_mode: true`. `run_scenario.py` produces a deterministic `results/demography_summary.json` with `summary_sha256` invariant. The `scripts/replay_equality_ci.py` gate now verifies 3 scenarios. 16 new tests cover DSL v2 load, ethics flags, KOSIS Tier B references, determinism, summary stability, output-shape policy invariants (no per-person key, integer cell counts, region-label-as-string).
- `luvoire.demography.synthesis` — Beckman-style multinomial cell-level population allocator. `CellPopulation` (synthetic cell id + age × sex aggregate counts) with regression test asserting no coordinate / polygon / EPSG / geometry attribute is exposed. `synthesize_cell_populations()` allocates a regional `CohortPopulation` across N synthetic-grid cells via Dirichlet-multinomial draws seeded for byte-identity. The aggregate-preservation invariant `aggregate(cells) == original.male, original.female` holds exactly (integer arithmetic). `cell_populations_total()` and `aggregate_cells_to_pyramid()` helpers round-trip cell tallies back to regional pyramids. Output is per-cell aggregate at the synthetic-grid floor — never individual records. 18 new tests pass.
- `luvoire.demography` subpackage — cohort-component demographic projector following the KOSTAT 장래인구추계 / UN World Population Prospects standard. Pure-numpy and fully deterministic. `CohortPopulation` (year × region-string × age × sex), `DemographicRates` (ASFR / ASMR / net migration / sex ratio at birth, with reproductive-age guard), and `CohortComponentProjector` (single-step + horizon projection with open-ended top class). `CounterfactualScenarioEngine` runs labelled `RatePerturbation` sets (`KOSTAT_REFERENCE_TRIPLE` low / medium / high fertility) for policy what-if comparison. `luvoire.demography.kosis` registers KOSIS aggregate-only metadata (출생/사망/이동/인구피라미드/장래추계, all KOGL Type 1, `시군구` aggregation floor enforced). `luvoire.demography.region` is a 시군구 **string-only** label registry — admin code + sido + sigungu, with a regression test asserting no coordinate / polygon / EPSG / geometry field is exposed; `ethics.no_real_geometry: true` remains intact. Output is **always aggregate** at registered region labels — no per-person, no sub-시군구 geometry, no individual prediction. Output trajectories are counterfactual scenarios (추계), not predictions (예측). 61 new tests pass.
- Scenario DSL v2 `EthicsSpecV2` gains two opt-in flags. `demographic_projection: bool = False` declares that the scenario uses `luvoire.demography` cohort-component projection over registered 시군구 string labels. `pssdp_mode: bool = False` declares Public Safety Service Demand Projection mode (학교 / 119 / 파출소 인프라 수요), positioning the scenario as decision-support rather than a decision-system. Validator interlocks: activating either flag while disabling `no_prediction` is rejected with a configuration-mistake error; activating `pssdp_mode` while disabling `no_suspect_scoring` is also rejected. The flags do **not** unlock prediction or suspect scoring — they only label aggregate demographic projection. 6 new ethics validator tests + 1 new schema test.

### Changed
- `luvoire.calibration.sbi_adapter.PosteriorHandle.sample` now validates that the upstream posterior returns a 2-D ``(n, dimension)`` array and raises `RuntimeError` with the offending shape on mismatch (was a silent reshape on 1-D output and no dimension check). Hardens the boundary against malformed mock or upstream posteriors.
- `luvoire.shock.catalog.Catalog` gains opt-in `duplicate_ids()` and `has_unique_ids()` query helpers. Existing `add()` semantics are unchanged: the catalogue still does not enforce uniqueness, but callers can now detect duplicates without iterating manually.

### Added
- `luvoire.scaling.city_scale` extended with an `aggregate` trace mode for large-N runs. `CityScaleTraceMode` literal, `CityScaleTickAggregate` frozen dataclass, and `sample_agent_count` config field let callers retain only per-tick aggregates plus a deterministic sample of full per-agent frames. New `city_scale_aggregate_output_hash`, `CityScaleResult.aggregates`, `frame_count_total`, `event_count_total`, `write_aggregate_jsonl`, and `write_aggregate_parquet` helpers expose the compact stream. `benchmarks/city_scale_100k.py` plus a committed `benchmarks/city_scale_100k_report.md` demonstrate a 100 000-agent × 100-tick aggregate proof on a 200×200 grid (single-shard, deterministic, no live LLM calls). 2 new scaling tests cover aggregate determinism and parquet export.
- `paper/rat_methodology/` — RAT methodology paper drafts. `kci_draft.md` is a Korean-language draft targeting KCI venues (target submission 2027-09); `ssci_draft.md` is an English-language draft targeting SSCI venues or arXiv preprint (target submission 2027-12); `methodology_section.md` is the canonical shared methods text reused by both. All three documents include explicit Civilian Use Policy alignment and disclaim prediction, per-person risk scoring, and operational deployment. 6 smoke tests verify keyword presence, citation set, and policy disclaimers.
- `scripts/run_id.py` and `scripts/replay_equality_ci.py` reproducibility infrastructure. `run_id.py` computes a deterministic SHA-256 over `(code_tree_sha, scenario_yaml_sha, seed, python_version, optional pip_freeze)` and exposes a CLI for embedding the run id into reports. `replay_equality_ci.py` re-runs the synthetic_seoul and crimemind_compare scenarios and asserts each `summary_sha256` matches the committed value, complementing the existing `verify_replay_shas.py` byte-level msgpack invariant. 10 tests cover code-tree determinism, env-hash canonicalisation, run-id divergence under seed/env changes, missing-source handling, and the CI smoke.
- `scenarios/crimemind_compare/` — patterns-level comparison harness for the CrimeMind (arXiv 2506.05981, June 2025) RAT-prompt agent design. Re-implements the three-slot prompt structure (motivation / exposure / guardian-gap) by rescaling RAT v1 inputs with three Tier C weights; runs three regimes (`equal_weights`, `motivation_heavy`, `guardian_heavy`) over a 6×6 synthetic grid. `compare.py` produces a deterministic `comparison_summary.json` with `summary_sha256` invariant. 8 tests cover DSL v2 load, Tier A/C invariants, determinism, committed-summary stability, regime ordering, threshold lock, and grid dimensions. No CrimeMind code or data is loaded; methodological reference only.
- `luvoire.memory.actr_weight` — ACT-R-inspired base-level activation helper (Anderson 2007). `base_level_activation()` computes `B_i = ln(Σ (t - t_j)^(-d))` over past use ages with `MINIMUM_AGE_SECONDS` floor; `actr_retention_weight()` squashes the activation through a logistic to fit Luvoire's existing `[0, 1]` decay-score expectations. Standalone helper — does not modify the locked `SharedDecayScheduler` or replay artifacts. 14 tests pass covering monotonicity, decay-exponent sensitivity, multi-use summation, age-floor singularity, and dataclass freezing.
- `luvoire.cognition` middleware extension — three new pure-deterministic helpers stacked on top of the existing Monologue + SocialLearner surface. `dual_process.route_decision` selects between Sys-1 habit and Sys-2 reflection based on weighted trigger signals. `attention.allocate_attention` performs salience-weighted seeded sampling under a per-tick budget so crowded scenes drop items deterministically. `bias.render_bias_prefix` composes a canonical-ordered bias-prefix string for 8 biases (availability, confirmation, anchoring, framing, hyperbolic discounting, loss aversion, status quo, representativeness) and emits a SHA-256 fingerprint for audit. None of the helpers invoke an LLM directly; callers compose them around their own LLM gateway. 26 new tests pass.
- `luvoire.pom` subpackage — Grimm Pattern-Oriented Modeling 3-gate validation. `Pattern` frozen dataclass with binned target distribution + sum-to-1.0 invariant. Three canonical reference factories: `time_of_day_pattern` (G1), `activity_diversity_pattern` (G2), `hotspot_distribution_pattern` (G3, structural only — never real). `evaluate_gate` and `evaluate_three_gates` compute discrete KS distance against the pattern's target CDF; threshold-based pass/fail. `score_pom` produces a weighted composite score in [0, 1] (higher better). Pure numpy + stdlib (no scipy dep). 35 tests pass.
- `luvoire.calibration` subpackage — simulation-based-inference + sweep + scenario-discovery adapters with **lazy-imported optional deps** (`sbi`, `optuna`, `ema_workbench`). Each adapter raises a typed `*Unavailable(RuntimeError)` when the optional package is absent so the engine installs without them. `RejectionAbcSpec` + `rejection_abc` ship a pure-numpy fallback ABC sampler that is byte-deterministic per seed. Frozen dataclasses with `slots=True` mirror the `luvoire.sensitivity.sobol` style. 36 tests pass + 3 skip (importorskip for real-package smokes).
- `luvoire.shock` subpackage — exogenous synthetic-shock catalogue overlaying time-and-space modifiers on the synthetic urban grid. Five `ShockKind` literals: festival / protest / policy_change / weather_event / infrastructure_change. `Catalog` is immutable (`add()` returns a new tuple-backed instance); `active_at(tick)` and `affecting(cell_id, tick=None)` filter by inclusive window and cell membership. `ShockScheduler` applies catalog effects to RAT v1 inputs: `apply_to_target` and `apply_to_guardianship` clamp to [0, 1]. CPTED helpers ship synthetic-only `cpted_lighting_install`, `cpted_cctv_install`, `cpted_natural_surveillance` factories; module docstring explicitly disclaims operational deployment and per-place risk scores. 41 tests pass.
- `luvoire.netlayers` subpackage — 5-layer relationship graph (family / coworker / classmate / neighbor / online) wrapping the existing single-layer `RelationshipGraph` without breaking it. Pure stdlib + numpy (py3plex/NDlib are optional). `MultilayerRelationshipGraph` exposes `add_edge`, `neighbors`, `weight`, `layer_density`, `aggregate_weight`, `flatten` (collapse to legacy graph), and `to_dict`. `DeGrootPropagator` runs deterministic opinion-dynamics propagation with seeded jitter. `AffectiveContagion` runs Bosse-style emotional contagion with per-tick decay + susceptibility. 30 tests pass + 2 skip (importorskip for py3plex/NDlib smoke).
- `scenarios/synthetic_seoul/` — committed Seoul-style 5×5 synthetic-grid scenario combining `luvoire.geo.synthetic_grid`, `luvoire.timeuse.EmpiricalCdfSampler`, the locked `luvoire.theory.rat` v1 convergence rule, and Scenario DSL v2 Tier A/B/C parameters. `scenario.yaml` is loadable via `load_scenario_v2`; `run_scenario.py` produces a deterministic `results/synthetic_seoul_summary.json` with per-cell event counts and a SHA-256 of the summary. Default seed 20260427 yields 7 cells with at least one event out of 25. 10 tests lock determinism per seed, divergence across seeds, committed-summary stability, and DSL v2 ethics + tier invariants.
- `luvoire.timeuse` subpackage — pure-numpy time-use prior sampler for the synthetic urban grid. `EmpiricalCdfSampler` draws activity codes from a strata-conditioned empirical distribution; `MarkovActivitySampler` walks a 7×7 row-stochastic transition matrix. Seven canonical activity codes: `sleep`, `work_or_school`, `commute`, `meals`, `leisure`, `care`, `other`. `StrataKey` is a frozen dataclass over `day_type × age_band × occupation`. `KostatTable` registry holds *metadata only* (T-08, T-12, T-15 under KOGL Type 1) — the engine never bundles or loads microdata. `tests/fixtures/timeuse/synthetic_priors_v1.json` ships a 2-strata synthetic JSON fixture used by tests. 43 tests pass; same-seed sequences are byte-identical via inverse-CDF sampling on a `1.0`-clamped CDF.
- `luvoire.routing` subpackage — deterministic OSRM HTTP routing client with optional-runtime semantics. `OsrmClient` consumes OSRM via httpx (already a core dep); `RouteRequest`/`RouteResponse` are frozen `@dataclass(slots=True)`; `cache_key()` produces a SHA-256 over canonical JSON for content-keyed caching. `LruCache` provides a deterministic in-memory bounded cache with hits/misses stats. `RoutingUnavailable` is raised on any transport or parse failure — never silent zero-duration substitution. Lat/lon ranges, hour bucket 0–23, and mode literal validated at construction time. Optional `[routing]` extra (`routingpy>=1.3`). 28 tests pass via `httpx.MockTransport` — no real network access.
- `luvoire.geo` subpackage — GIS readiness for synthetic urban grids. Three modules with optional-runtime fallbacks: `h3_index` (h3-py v4 thin wrapper, equality-only fallback consistent with `luvoire.theory.rat._same_or_adjacent_cell`), `synthetic_grid` (pure-numpy lattice generator emitting `synthetic-grid-r{row}c{col}` ids), `synthetic_polygon` (Shapely-backed polygon helpers with 4-corner-tuple fallback). New optional `[geo]` extras (`h3>=4.0`, `shapely>=2.1`, `geopandas>=1.0`, `libpysal>=4.10`, `osmnx>=2.0`). 38 tests pass + 5 skip (h3/shapely import-skip branches).
- `paper/asc2026_poster/abstract_en.md`, `abstract_ko.md`, and `ethics_footer.md` ship the EN/KO ASC 2026 methodology poster abstracts and the canonical ethics footer text used on the poster, slide deck, and submission portal notes field. 5 smoke tests in `tests/test_asc2026_abstract_present.py` verify keyword presence and policy alignment.
- `.zenodo.json` keyword set extended with ``routine activity theory``, ``auditable replay``, ``sensitivity analysis``; release notes summarise the realism-roadmap T1 unreleased additions on top of v0.3.0.
- `paper/asc2026_poster/` — four committed methodology panels (Method 3-tier, Theory RAT convergence, Sensitivity Sobol bars, Replay-hash invariants table) generated deterministically by `paper/asc2026_poster/build_panels.py`. PDFs and SVGs both committed for arXiv/LaTeX consumption. The Sensitivity panel reads `experiments/rat_sensitivity/results/sobol_indices.json` so live regeneration always reflects the latest committed indices. The Replay panel reads `scripts/verify_replay_shas.py` baselines so the 5-artifact invariant table is single-sourced. 4 smoke tests in `tests/test_asc2026_poster_panels.py`.
- `luvoire.sensitivity.sobol` — deterministic Saltelli/Sobol sensitivity helpers (radial design, Jansen 1999 first-order, Saltelli 2010 total-order). Pure numpy; no SALib runtime dependency.
- `experiments/rat_sensitivity/` — committed Sobol sweep over the three RAT inputs with `results/sobol_indices.json`, `sobol_indices.md`, and `run_manifest.json`. Default seed 20260427, n=4096, 20480 evaluations. Indices are near-symmetric across motivation/exposure/gap (multiplicative model) and total-order ≈ 0.5 vs first-order ≈ 0.23 confirms strong interaction effects.
- `tests/test_sensitivity_sobol.py` (13 tests) and `tests/test_rat_sensitivity_experiment.py` (6 tests) lock determinism, manifest invariants, near-symmetric indices, and total > first inequality.
- `luvoire.theory.rat` v1 — locked routine activity theory convergence rule (`ActorState`, `TargetExposure`, `GuardianshipGap`, `OpportunityEvent`, `opportunity_event`). Tier A scenario references of the form `code:luvoire.theory.rat.v1` now resolve to a real module. Multiplicative convergence formula, tick-equality, cell-adjacency, and the `rat_v1_synthetic_opportunity` event kind are locked; threshold and input distributions remain Tier B/C YAML parameters.
- `tests/test_theory_rat_v1.py` adds 13 unit tests covering convergence above/below threshold, tick mismatches, cell adjacency, synthetic-grid behaviour, threshold override, immutability, and h3-py-optional adjacency.
- `docs/theory/rat-v1-design-spec.md` and `docs/theory/rat-v1-reference.md` document the module and its locked vs adjustable surface.
- Scenario DSL v2 (`luvoire.dsl.v2`) with variable 3-tier parameter system (Tier A theoretical constants, Tier B empirical priors with required source metadata, Tier C exploration knobs with required range plus default), optional GIS-readiness fields (`environment.h3_cell`, `environment.epsg`), and `ethics.no_real_geometry` guardrail. v1 scenarios continue to load via `load_scenario_v2` with a one-release-window deprecation warning.
- `schemas/scenario_v2.json` exported via `luvoire.dsl.v2.scenario_v2_json_schema()`.
- `scripts/lint_dsl_v2.py` enforces Tier A/B/C consistency for v2 YAML files with `--strict` exit-code mode.
- `tests/fixtures/scenarios/v2_rat_baseline.yaml` and `v1_legacy.yaml` golden fixtures plus 42 new pytest cases across schema export, parameter validation, ethics guardrails, parser deprecation, and lint regression.
- `luvoire.personas.lpi` defines Luvoire Persona Interface v1, a harmonized cross-country persona dataclass plus JSON schema.
- `luvoire.personas.loaders` adds CC-BY-4.0 Nemotron-Personas loaders for USA, Japan, India, Brazil, Singapore, France, and Korea behind the `luvoire[personas]` extra.
- `python -m luvoire.cli personas {list,sample,schema}` for country metadata, deterministic LPI sampling, and schema export.
- `POLICIES/civilian_use.md` and `.ko.md` publicly refuse defense, predictive policing, PSYOP, non-consenting twinning, and minors-in-synthetic-pipelines use categories.
- `luvoire.adapters.mesa` provides plain Mesa 3 integration behind the `luvoire[mesa]` extra.
- `luvoire.export.odd` adds a Grimm 2020 ODD protocol markdown exporter via `python -m luvoire.cli export odd`.
- `luvoire.core.replay_cache` with record/replay modes for deterministic LLM side effects.
- `LUVOIRE_REPLAY_CACHE_PATH` and `LUVOIRE_REPLAY_CACHE_MODE` env-var controls; path unset preserves current behavior.

## [0.3.0] - 2026-04-22

### Added
- Luvoire rebrand release surface with the renamed Python package, CLI entry points, project metadata, and one-release compatibility shim for legacy imports and environment variables.
- Brand package, landing deployment notes, and landing bundle tracking for the Luvoire launch surface.

### Changed
- Active code, documentation, distribution metadata, adapters, and playground surfaces now use the Luvoire name while preserving historical reports and pre-v7 changelog entries verbatim.
- Release metadata now targets `v0.3.0` and the `Celovin/luvoire` repository namespace.

### Security
- Replay artifact SHA-256 invariants remain unchanged across the rebrand, including the Nemotron 10K replay artifact.

### Added
- Static status page generator with Hugging Face Space, GitHub Actions, replay artifact badges, and a 15-minute update workflow.
- Public pricing page with Free, Pro, Team, and Enterprise tiers plus a self-contained static HTML mirror.
- Payment seller onboarding references for Toss Payments and Paddle plus a safe environment status checker.
- Deterministic attribution and SBOM artifacts with CI drift checks for downstream package compliance.
- Draft commercial legal package covering terms, privacy, DPA, attribution, SLA, security posture, and refund policies.
- Tiered billing primitives for BYO-key, metered pass-through, and enterprise LLM usage, including webhooks, tenant API keys, and billing documentation.
- Full CAT-28 tier 5 personality taxonomy with 22 single archetypes, 6 composite overlays, manifest coverage, and replay viewer grouping.
- Optional Nemotron-Personas-Korea persona seeding for the local 10K Gangnam replay, with an offline fixture, deterministic loader tests, license record, and docs.
- City-scale 1K deterministic runner with multiprocessing shards, offline msgpack replay artifacts, Canvas viewer, and Tier 1/Tier 2 pedagogical archetype overlays.
- Unity SDK preview package with FastAPI tick, memory, and action endpoints plus Python-side contract tests.
- OpenAI TTS voice playback for Playground timeline `speak` actions, with per-agent voice pickers, cache-backed WAV synthesis, and a silent offline fallback.
- Playground deploy warmup tooling with verified fresh-install pins and optional factory reboot when dependency metadata changes.
- Bilingual Didimdol one-pager generator that emits deterministic Korean and English PDF handouts from committed benchmark sources.

## [0.2.0] - 2026-04-19

### Added
- Phase 41 live Ollama five-agent demo notebook with deterministic seeded fallback and recording cue sheet.
- Phase 42 deterministic 500-agent metropolis experiment with 20 seeds, JSONL evidence, summary JSON, and latency/memory SVG artifacts.
- Phase 43 persona opt-in Theory of Mind module with deterministic Sally-Anne false-belief benchmark evidence.
- Phase 44 FastAPI server for REST simulation management, agent inspection, event injection, and live WebSocket streaming.
- Phase 44 API authentication and in-memory token-bucket rate limiting for demo-safe deployments.
- Phase 44 Docker Compose bundle for the API server, Streamlit dashboard, and research SaaS dashboard.
- Phase 44 API usage notebook plus REST and WebSocket reference documentation.
- Phase 45 classic ABM reproductions for Schelling segregation and Axelrod-style iterated prisoner's dilemma tournaments.
- Phase 45 reproduction docs, committed JSONL summaries, and SVG artifacts for both classic experiment tracks.
- Phase 46 Persona Consistency Score and Relationship Coherence Score utilities with a `knoema score` CLI surface.
- Phase 46 scoring benchmark bundle with committed JSON and SVG artifacts for the 50-agent village and 500-agent metropolis logs.
- Phase 47 Unreal Engine 5 plugin scaffold with a REST API client, tick-based NPC component, placeholder Blueprint asset, and adapter documentation.
- Phase 48 scenario marketplace library with 50 fictional Scenario DSL examples across school, workplace, family, community, and social-experiment categories.
- `knoema validate` CLI command for Scenario DSL file or directory validation.
- Phase 49 web scenario editor with drag-and-drop agent placement, timeline editing, live YAML preview, and Playwright e2e coverage.
- Phase 50 arXiv v2 paper finalization with 500-agent, Theory of Mind, classic reproduction, PCS/RCS, reproducibility, and scenario-library sections.
- Phase 50 Papers with Code submission packet with machine-readable JSON metadata and result rows.
- Phase 50 technical report PDF regenerated as a 30+ page preview.
- Phase 51 hierarchical task-network planner with persona opt-in goal decomposition and planning-depth evidence.
- Phase 52 distributed 1000-agent city experiment with Ray-compatible fallback, location sharding, SVG evidence, and formal report integration.
- Phase 54 browser-side TypeScript static runtime with 2-agent, 5-agent, and Sally-Anne demos plus Playwright smoke coverage.
- Phase 55 social learning module with opt-in observational imitation and deterministic cascade evidence.
- Phase 56 VS Code Scenario DSL extension with syntax highlighting, schema validation, commands, and VSIX packaging support.
- Phase 57 cross-framework comparison benchmark against AutoGen, CrewAI, LangGraph, Mesa, and NetLogo with Docker-reproducible reporting artifacts.
- Phase 58 human evaluation framework with survey templates, a static rater UI, pilot sample data, and Cohen/Fleiss reliability metrics.
- Phase 59 cloud deployment templates for AWS, GCP, and Azure with static validation and cost comparison documentation.
- Phase 60 mobile SDK scaffolds for iOS Swift Package Manager and Android Kotlin clients with REST, WebSocket, cache, and offline surfaces.
- Phase 61 interactive 5-chapter tutorial website with embedded code editing, chapter quizzes, local progress, and Playwright coverage.

### Changed
- Updated repository release metadata, README current-version sections, CI dry-run targets, academic indexing notes, and the paper version marker to `0.2.0`.
- Expanded the formal evidence layer from MVP scaffolding into cognitive, distributed, safety, SDK, deployment, benchmark, evaluation, and tutorial surfaces.

### Deprecated
- None.

### Removed
- None.

### Fixed
- Synchronized API, package, adapter, Release Please, Citation File Format, and Zenodo metadata versions for the `v0.2.0` release.

### Security
- Phase 53 red-team safety suite with opt-in content filtering, PII checks, scenario-abuse rejection, JSONL audit logging, and safety policy docs.

## [0.1.1] - 2026-04-18

### Added
- Core engine modules for personas, memory, relationships, environment, emotion, LLM gateway, decisions, events, and simulation.
- Three executable Jupyter examples: dormitory simulation, fictional scenario replay, and game NPC persistent memory.
- Godot 4 adapter scaffold with HTTP/local fallback client and demo scene.
- Streamlit dashboard MVP for JSONL simulation logs, agent summaries, relationship edges, and conversation inspection.
- Architecture and research positioning documentation.
- Phase 12 technical report draft with LaTeX source, BibTeX references, and a generated PDF preview.
- Phase 13 release preparation: Dockerfile, release workflow, release playbook, and local package artifact checks.
- Phase 14 ten-agent village simulation notebook with deterministic local decisions and JSONL export checks.
- Phase 14 benchmark script for deterministic Knoema throughput reports with Concordia and Mesa comparison slots.
- Phase 14 multilingual prompt templates for English, Korean, Japanese, and Chinese runs.
- Phase 14 `knoema run` CLI for YAML-driven deterministic local simulations.
- Phase 14 semantic-temporal memory reranking with scored retrieval diagnostics and batch inserts.
- Phase 14 Streamlit dashboard realtime playback with live-tail and auto-refresh controls.
- Phase 14 publish-ready tutorial blog draft for Medium and velog cross-posting.
- Phase 14 Discord community launch kit with channel layout, rules, announcement copy, and moderation checklist.
- Phase 15 Hugging Face Playground with three scenarios, replay-only mode, optional user-supplied LLM keys, timeline, relationship graph, and JSONL download.
- Phase 16 Unity 2022 LTS adapter scaffold with UPM package metadata, runtime HTTP/fallback client, NPCAgent component, Basic NPC sample, and Editor test scaffold.
- Phase 17 competitor matrix comparing Knoema with academic generative-agent systems, agent orchestration frameworks, game NPC platforms, and traditional ABM tools.
- Phase 18 demo video scripts for 30-second, 3-minute, and 10-minute walkthroughs plus a shared recording shot list.
- Phase 19 deterministic 50-agent village experiment with committed JSONL results, metrics, trace sample, and a 10-page benchmark PDF report.
- Phase 20 formal benchmark report bundle with 24 deterministic runs, baseline discipline notes, SVG figures, summary statistics, and a 20-page PDF report.
- Phase 21 reproducibility test suite covering same-seed determinism, seed propagation, config serialization, JSONL replay summaries, and a public reproducibility report.
- Phase 22 Scenario DSL v1 with Pydantic schema, YAML parser, ethics validator, serializer, JSON Schema, three sample scenarios, and DSL documentation.
- Phase 23 Research SaaS dashboard scaffold with six Streamlit pages, A/B comparison services, memory and relationship inspectors, cost budget, and citation export helpers.
- Phase 24 Game NPC SDK API facades for Python, TypeScript, and Godot GDScript with examples and integration documentation.
- Phase 25 Next.js website scaffold with application tracks, SDK code demo, research report links, benchmark figures, and public launch routes.
- Phase 26 Korean technical blog drafts covering indie game NPCs, memory design, Godot integration, research reproducibility, and synthetic replay guardrails with thumbnail assets.
- Phase 27 YouTube tutorial scripts for getting started, first NPC integration, and reproducible research experiments with recording guidance and descriptions.
- Phase 29 MkDocs documentation site with getting-started guides, API reference pages, game and research workflows, CLI reference, and community docs.
- Phase 30 arXiv-oriented technical report v2 with expanded LaTeX structure, appendix, figure/table sources, benchmark evidence, 50-agent experiment summary, and 50+ BibTeX references.
- Phase 31 academic indexing packet with citation metadata, Zenodo release metadata, Papers with Code submission guidance, and pending-state README badges.
- Phase 33 quality gate with property, integration, fuzzing, and adapter contract tests plus an explicit 90% coverage threshold.
- Phase 34 security audit package with Bandit, pip-audit, Safety, npm audit, Dependabot config, disclosure policy, and CycloneDX SBOM evidence.
- Phase 35 CI and release automation with cached quality gates, cross-platform compatibility smoke matrix, Release Please configuration, PyPI Trusted Publishing, and a `v0.1.1` dry-run script.
- Phase 36 local LLM fallback adapters for Ollama, llama.cpp, and vLLM plus an Ollama tutorial notebook and local-vs-cloud benchmark notes.
- Phase 37 scenario marketplace beta with repository-backed submission docs, curated seed scenarios, a scenario validator workflow, and a scenario submission PR template.
- Phase 38 multilingual README pack for English, Korean, Japanese, Simplified Chinese, Traditional Chinese, German, French, and Spanish navigation.
- Phase 39 anonymous opt-in telemetry for CLI usage, privacy documentation, and safe event-delivery tests.
- Phase 40 public case-study pack for KNOT integration, a Korean university pilot, and indie studio adoption planning.
- External activation status script for reporting remaining Hugging Face, Vercel, GitHub Actions, and release blockers in one JSON snapshot.
- Combined pre-release checker that runs activation status and local release dry run in one step.
- Suggested remediation actions in the external activation status report for remaining operator-side blockers.
- Vercel local project link files are now git-ignored, and activation status detection recognizes the current Vercel auth file layout.
- Hugging Face Playground deployment helper that validates the `celovin` namespace before creating and uploading the Space.

### Changed
- Hardened Phase 24 SDK facades with required input validation, defensive dictionary copies, TypeScript package build configuration, and safer Godot missing-NPC responses.
- Improved Phase 25 website quality with canonical/robots/Twitter metadata, page-level SEO metadata, discoverable priority hero image loading, and dimensioned lazy benchmark figures.
- Tuned SQLite-backed memory storage for more stable hosted-runner write performance.
- Expanded MkDocs navigation so all public Markdown docs are surfaced in the published documentation site.

## [0.1.0] - 2026-04-18

### Added
- Initial repository scaffold (Phase 0 of MVP plan).
- `pyproject.toml` with core dependencies.
- Dual-language README.
- MIT License, Copyright (c) 2026 Celovin.
- GitHub Actions CI.
- Pre-commit configuration.
- Smoke test verifying package import.
