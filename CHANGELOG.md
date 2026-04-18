# Changelog

All notable changes to Knoema Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Changed
- Hardened Phase 24 SDK facades with required input validation, defensive dictionary copies, TypeScript package build configuration, and safer Godot missing-NPC responses.
- Improved Phase 25 website quality with canonical/robots/Twitter metadata, page-level SEO metadata, discoverable priority hero image loading, and dimensioned lazy benchmark figures.

## [0.1.0] - 2026-04-18

### Added
- Initial repository scaffold (Phase 0 of MVP plan).
- `pyproject.toml` with core dependencies.
- Dual-language README.
- MIT License, Copyright (c) 2026 Celovin.
- GitHub Actions CI.
- Pre-commit configuration.
- Smoke test verifying package import.
