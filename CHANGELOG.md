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

## [0.1.0] - 2026-04-18

### Added
- Initial repository scaffold (Phase 0 of MVP plan).
- `pyproject.toml` with core dependencies.
- Dual-language README.
- MIT License, Copyright (c) 2026 Celovin.
- GitHub Actions CI.
- Pre-commit configuration.
- Smoke test verifying package import.
