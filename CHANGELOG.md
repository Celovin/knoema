# Changelog

All notable changes to Knoema Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/Celovin/knoema/compare/knoema-engine-v0.1.0...knoema-engine-v0.2.0) (2026-04-18)


### Features

* add 50-agent village benchmark ([f93ccea](https://github.com/Celovin/knoema/commit/f93cceaa5dd9600cda40030b517a06a3908cf591))
* add deterministic benchmark script ([7cf6d0a](https://github.com/Celovin/knoema/commit/7cf6d0a7631e4bcc0f4f330d10151d51c7e8d2cf))
* add formal benchmark report ([a4312d4](https://github.com/Celovin/knoema/commit/a4312d4481c5cf653238ff8e5ddbefced8f7138b))
* add game SDK API facades ([db0ed0b](https://github.com/Celovin/knoema/commit/db0ed0be67a8f7e02303855cce5d16cce63411c3))
* add Hugging Face playground ([ef36781](https://github.com/Celovin/knoema/commit/ef367815a06cad896f8adeda7a84b134ba5251f1))
* add hybrid memory reranking ([fbfca7e](https://github.com/Celovin/knoema/commit/fbfca7e41aea373d5d76e1f24f92f3c2e592762e))
* add multilingual prompt templates ([d4727c6](https://github.com/Celovin/knoema/commit/d4727c67c629aff1f23ea200650e1c4bbc79cf34))
* add Next.js project website ([b527a64](https://github.com/Celovin/knoema/commit/b527a64c56f2e8cf58d47125d8f4f05f1efe02dd))
* add realtime dashboard playback ([afd7bc4](https://github.com/Celovin/knoema/commit/afd7bc4c09ac6638a5101ceb8e614fbc5422000b))
* add research SaaS dashboard scaffold ([36c37bf](https://github.com/Celovin/knoema/commit/36c37bf52d460df429ec912542356de6f0eeaf90))
* add scenario DSL v1 ([55452f0](https://github.com/Celovin/knoema/commit/55452f044215640055e69ea8760d648c24f2f73d))
* add ten-agent village notebook ([7a56671](https://github.com/Celovin/knoema/commit/7a56671a886589d072cbac21d22084a87606f57b))
* add Unity adapter scaffold ([ed9ccda](https://github.com/Celovin/knoema/commit/ed9ccda639a77769d2b4b47fbeaaf27a0c136efc))
* add yaml-driven simulation CLI ([bcba324](https://github.com/Celovin/knoema/commit/bcba32451d856baded0b9fccc4091ea15f38619d))
* implement Knoema MVP engine and demos ([c822fbb](https://github.com/Celovin/knoema/commit/c822fbb318582669d58f4a562fe63bbf22085038))


### Documentation

* add academic indexing metadata ([6086d97](https://github.com/Celovin/knoema/commit/6086d9738a268358bbf3f821d233ee6814016e27))
* add competitor matrix ([3afaf19](https://github.com/Celovin/knoema/commit/3afaf1995c3652818f8cb205a7ddc1726ed52c94))
* add demo video scripts ([8939a04](https://github.com/Celovin/knoema/commit/8939a04e7e8501f88196417b6c9b3b61fd8b27a0))
* add Discord community launch kit ([95793a9](https://github.com/Celovin/knoema/commit/95793a933d1bdda5615ce882b56e27ef59fee244))
* add Knoema technical report draft ([4758a2f](https://github.com/Celovin/knoema/commit/4758a2f5e5e2b3a777b7bdbb7e2ee851b249fd5e))
* add Knoema tutorial blog draft ([58c82d4](https://github.com/Celovin/knoema/commit/58c82d445144aceb9ebc80c7b94080b39fe7e522))
* add Korean technical blog drafts ([c796dc9](https://github.com/Celovin/knoema/commit/c796dc91245f86ede95628dadfb507ccb4e8f932))
* add MkDocs API reference site ([9906e33](https://github.com/Celovin/knoema/commit/9906e337ab1e5d2979b4b25b665e85346b5b6bce))
* add YouTube tutorial scripts ([5fcc2d9](https://github.com/Celovin/knoema/commit/5fcc2d9c58e14e522f8cda99caf5c082ce6df952))
* expand arXiv technical report ([d1a52e0](https://github.com/Celovin/knoema/commit/d1a52e05de626876abcd91cdaf58eaf9c5fc5a21))
* update report public release wording ([7a3202b](https://github.com/Celovin/knoema/commit/7a3202b458f3556442219d6981511934856a7f88))

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
