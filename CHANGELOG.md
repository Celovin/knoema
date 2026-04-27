# Changelog

All notable changes to Knoema Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
