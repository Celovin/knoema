# Proposal-to-Implementation Mapping

This document maps the R&D plan in `planning/본문1_연구개발계획서_초안.md` to the concrete sub-tasks, repository files, and regression tests that now carry the implementation. It is meant for evaluator audit, not for marketing.

## Audit Rules

- Proposal baseline: `planning/본문1_연구개발계획서_초안.md`
- Sub-task source of truth: `planning/codex_task_playground_layout.md`
- Execution trace: `planning/codex_execution_state.md`
- Code evidence must point to committed repository files.
- Verification evidence must reference runnable tests or benchmark artifacts already in the repo.

## Mapping Table

| Proposal element | Proposal intent | Linked sub-tasks | Primary repository evidence | Verification evidence |
| --- | --- | --- | --- | --- |
| Core engine runtime | Deliver a typed multi-agent runtime with persona, memory, emotion, relationships, and decision flow. | 4, 5, 16, 17, 19, 30, 41, 55, 59 | `src/knoema/types.py`, `src/knoema/memory/store.py`, `src/knoema/planning/hierarchical.py`, `src/knoema/llm/cache.py`, `src/knoema/memory/multi_layer.py` | `tests/test_phase1_types.py`, `tests/test_phase2_memory.py`, `tests/test_playground_htn.py`, `tests/test_playground_trait_correlation.py` |
| Scenario and environment modeling | Support reproducible fictional environments, curated scenarios, and culture-sensitive priors. | 4, 13, 14, 26, 39, 60 | `playground/environments.yaml`, `playground/scenarios/`, `playground/cultural_priors.yaml`, `playground/app.py` | `tests/test_playground_environment_presets.py`, `tests/test_playground_hints.py`, `tests/test_playground_cultural_priors.py`, `tests/test_playground_advanced_research_gate.py` |
| Multi-agent control surface | Let users configure multiple agents, tune traits, and steer runs without editing YAML. | 2, 5, 6, 7, 15, 25, 57 | `playground/app.py`, `playground/persona_presets.yaml`, `playground/player_input_parser.py` | `tests/test_playground_agent_count.py`, `tests/test_playground_extended_personality.py`, `tests/test_playground_multi_agent_tabs.py`, `tests/test_playground_mirofish_lab.py` |
| Observability and explanation UI | Make simulated behavior inspectable through charts, graph views, memory panes, and exports. | 1, 8, 9, 10, 11, 12, 20, 21, 22, 23, 24, 27, 29, 37, 38, 49, 50, 51, 58 | `playground/app.py`, `src/knoema/research/preregistration.py`, `src/knoema/research/replication_package.py`, `src/knoema/research/deposit.py` | `tests/test_playground_layout.py`, `tests/test_playground_accessibility.py`, `tests/test_playground_statistics_panel.py`, `tests/test_playground_reviewer_mode.py`, `tests/test_playground_replication_package.py`, `tests/test_playground_zenodo_deposit.py` |
| Application A: synthetic public-safety research | Keep public-safety work inside fictional, auditable, non-operational boundaries while preserving replay and evaluator inspection. | 14, 24, 35, 38, 39, 40, 43, 44, 54, 60 | `playground/scenarios/night_convenience_fictional.yaml`, `docs/research/proposal_mapping.md`, `benchmarks/`, `paper/main.tex` | `tests/red_team/test_scenario_abuse.py`, `tests/test_playground_advanced_research_gate.py`, `tests/test_phase43_theory_of_mind.py` |
| Application B: game NPC tooling | Provide game-oriented actions, routines, player loop support, voice IO, and engine adapters. | 31, 32, 33, 34, 46, 47, 48 | `src/knoema/game/`, `adapters/godot/`, `adapters/unity/`, `playground/voice.py` | `tests/test_playground_game_actions.py`, `tests/test_playground_routines.py`, `tests/test_playground_player_mode.py`, `tests/test_phase34_game_demos.py` |
| Application C: academic SaaS and reproducibility | Provide statistics, preregistration, export, peer review mode, and archival packaging. | 24, 25, 27, 35, 36, 37, 38, 50, 51, 58 | `src/knoema/research/`, `docs/research/papers_with_code_submission.md`, `CITATION.cff`, `.zenodo.json` | `tests/test_playground_statistics_panel.py`, `tests/test_playground_preregistration.py`, `tests/test_playground_mixed_effects.py`, `tests/test_phase31_academic_indexing.py` |
| Benchmarks and validation | Quantify throughput, memory retrieval quality, theory-of-mind behavior, and planning depth scaling. | 18, 30, 41, 43, 44, 45, 54, 56, 59 | `benchmarks/`, `experiments/`, `src/knoema/theory_of_mind.py`, `src/knoema/planning/hierarchical.py` | `tests/test_api_server.py`, `tests/test_phase20_formal_benchmark.py`, `tests/test_phase43_theory_of_mind.py` |
| Safety, accessibility, and compliance | Preserve reviewer anonymization, accessibility, IRB-style gating, and cross-cultural caveats. | 38, 39, 53, 60 | `playground/reviewer_mode.py`, `playground/app.py`, `docs/research/proposal_mapping.md` | `tests/test_playground_reviewer_mode.py`, `tests/test_playground_accessibility.py`, `tests/red_team/test_harmful_content.py` |

## Phase Coverage

| Proposal phase | What the phase promised | Current sub-task coverage | Representative files |
| --- | --- | --- | --- |
| Phase 1: core engine | Persona, memory, relationship, environment, decision core | 4, 5, 16, 17, 18, 19, 30, 41, 55, 59 | `src/knoema/`, `playground/simulation.py` |
| Phase 2: three adapters | Game, synthetic replay research, and academic SaaS adapters | 24, 31, 32, 33, 34, 35, 36, 37, 38, 46, 47, 48, 50, 51, 58 | `adapters/`, `src/knoema/research/`, `playground/app.py` |
| Phase 3: validation and deployment readiness | Evaluator-facing benchmarks, explainability, and reproducible packaging | 12, 24, 27, 29, 37, 40, 42, 43, 44, 45, 54, 56, 57, 60 | `docs/research/`, `benchmarks/`, `paper/`, `planning/` |

## Evaluator Notes

1. Proposal claims that depend on external partnership, budget execution, or future field deployment are not treated here as shipped implementation. This document maps only repository-backed deliverables.
2. Public-safety references remain synthetic and fictional. Repository evidence should be read together with the red-team tests and the DSL guardrails.
3. Where a proposal item spans multiple sub-tasks, the linked row points to the smallest set of files and tests that make the dependency auditable without duplicating the whole repo tree.
