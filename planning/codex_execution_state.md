# Knoema Codex Execution State

**Last updated**: 2026-04-19 23:38 UTC by Codex

**Source document**: `planning/codex_task_playground_layout.md` (60 sub-tasks)

**Legend**: `[ ]` not started, `[/]` in progress, `[x]` done, `[~]` blocked (see `planning/codex_blockers.md`)

**Execution target**: complete every sub-task from 1 through 60 in numeric order unless a group is partially done, in which case finish that group first.

---

## Group 1 — 기반·UI (1-3h)

- [x] 1. Relationship graph widened to 620px, timeline stacked below (scrollable) - 2026-04-19 13:53 UTC, commit a4331e9
- [x] 2. Agent count slider (1-30) + `_resize_agent_pool` - 2026-04-19 14:07 UTC, commit 51e1558
- [x] 3. Big Five slider `info=` hints; Korean "정서 불안정성" rename - 2026-04-19 14:10 UTC, commit f81429f
- [x] 13. Scenario-specific guidance hints above Run button - 2026-04-19 14:15 UTC, commit a9e57f0
- [x] 28. Built-in 8-step tutorial walkthrough - 2026-04-19 14:22 UTC, commit 048947c

## Group 2 — 콘텐츠 확장 (4-6h)

- [x] 4. 25 environment presets (`playground/environments.yaml`) - 2026-04-19 14:30 UTC, commit 8dd1fcd
- [x] 6. 25 persona archetypes (`playground/persona_presets.yaml`) - 2026-04-19 14:37 UTC, commit d918766
- [x] 14. 30 Replay scenarios (27 new YAMLs added to reach 30 total) - 2026-04-19 14:45 UTC, commit 68ceee5
- [x] 26. Cultural context modules (Confucian/Western/Islamic/Latin/Nordic) - 2026-04-19 15:16 UTC, commit 2214682

## Group 3 — 성격 모델 + ablation (4-6h)

- [x] 5. 30 Personality traits across 7 tiers (schema + UI accordions) - 2026-04-19 15:09 UTC, commit ab5b672
- [x] 17. Inner monologue layer - 2026-04-19 15:23 UTC, commit e72efca
- [x] 19. HTN hierarchical planning hookup - 2026-04-19 15:31 UTC, commit e04ed1d
- [x] 41. Trait correlation matrix + ablation study - 2026-04-19 15:40 UTC, commit 4681e8f

## Group 4 — 멀티 에이전트·액션 (4-5h)

- [x] 7. 3-tab multi-agent personality customization - 2026-04-19 15:51 UTC, commit 677952c
- [x] 16. 20 social action verbs - 2026-04-19 16:05 UTC, commit 6e9f115
- [x] 25. Batch run mode (N=10/30/100) - 2026-04-19 16:19 UTC, commit 64bd0c5
- [x] 31. 15 game-domain action verbs (combat/inventory/quest/faction) - 2026-04-19 16:35 UTC, commit dbf768c

## Group 5 — 시각화 (6-7h)

- [x] 8. Action type breakdown chart (stacked bar) - 2026-04-19 16:46 UTC, commit 2310239
- [x] 9. Tick scrubber + per-tick highlight panel - 2026-04-19 16:53 UTC, commit a148bd1
- [x] 10. Memory inspector (short-term + long-term + monologue) - 2026-04-19 17:10 UTC, commit 66b99a9
- [x] 11. Consistent agent color coding across 4 surfaces - 2026-04-19 17:17 UTC, commit 6fb7a4b
- [x] 20. Conversation thread view - 2026-04-19 17:26 UTC, commit 17199fd
- [x] 21. Per-agent emotion timeline (PAD over ticks) - 2026-04-19 17:36 UTC, commit 8d1929d
- [x] 22. Spatial heatmap (treemap) - 2026-04-19 17:43 UTC, commit 0ff0747
- [x] 23. Sankey action-flow diagram - 2026-04-19 17:49 UTC, commit 0b3e442
- [x] 49. 2D mini-map - 2026-04-19 17:55 UTC, commit 5a5dcc5

## Group 6 — Application B (Game depth) (6-9h)

- [x] 32. NPC daily routine + schedule system - 2026-04-19 18:16 UTC, commit 9d863fc
- [x] 33. Player-as-agent mode (hybrid loop) - 2026-04-19 18:39 UTC, commit 7227841
- [x] 34. Godot + Unity tavern_demo samples + WebGL exports - 2026-04-19 18:50 UTC, commit 25b9c26
- [x] 46. Procedural quest generation - 2026-04-19 19:06 UTC, commit e850c47
- [x] 47. NPC schedule conflicts + coordination - 2026-04-19 19:15 UTC, commit 6358f51
- [x] 48. Voice conversation mode (TTS/STT) - 2026-04-19 19:27 UTC, commit 2cfbd15

## Group 7 — Application C (Academic depth) (8-10h)

- [x] 24. Statistical analysis panel (chi-square + Mann-Whitney baseline) - 2026-04-19 20:47 UTC, commit cca3ca6
- [x] 27. CSV + LaTeX export - 2026-04-19 20:55 UTC, commit 0fa8944
- [x] 29. Competitive comparison cards - 2026-04-19 21:03 UTC, commit ea97f3f
- [x] 35. OSF Preregistration generator (generic template) - 2026-04-19 21:15 UTC, commit 6a2305e
- [x] 36. Mixed effects models + Bayesian posterior (statsmodels + PyMC) - 2026-04-19 21:28 UTC, commit e298683
- [x] 37. DUX-standard replication package bundler - 2026-04-19 21:35 UTC, commit f656833
- [x] 38. Reviewer-mode UI (blind peer review path) - 2026-04-19 21:55 UTC, commit ef0e95d
- [x] 50. Power analysis + sample size calculator - 2026-04-19 22:14 UTC, commit 5661bdd
- [x] 51. arXiv / Zenodo auto-deposit - 2026-04-19 22:23 UTC, commit 05cbfdc
- [x] 58. OSF Simulation Studies Template (replaces Sub-task 35 default) - 2026-04-19 22:32 UTC, commit 5c1c86c

## Group 8 — 성능·UX·접근성 (4-5h)

- [x] 12. Export run as HTML report - 2026-04-19 19:35 UTC, commit 361368c
- [x] 18. WebSocket live tick streaming - 2026-04-19 20:03 UTC, commit e15fdda
- [x] 30. LLM cache + async parallel I/O - 2026-04-19 20:18 UTC, commit 6fdcbd7
- [x] 52. Dark mode + theme system - 2026-04-19 20:29 UTC, commit 04d22b2
- [x] 53. WCAG 2.1 AA accessibility sweep - 2026-04-19 20:37 UTC, commit 0aacf45

## Group 9 — Engine depth + 심사 mitigation (6-8h)

- [x] 39. Dark Tetrad IRB consent gate - 2026-04-19 22:46 UTC, commit 995aef4
- [x] 40. 본문1 ↔ Sub-task mapping document - 2026-04-19 22:52 UTC, commit 7ded3f9
- [x] 42. 인건비 / effort allocation document - 2026-04-19 22:56 UTC, commit 230d0e8
- [x] 43. Memory retrieval recall@k benchmark - 2026-04-19 23:01 UTC, commit fe3128e
- [x] 44. ToM Sally-Anne ablation across personality tiers - 2026-04-19 23:04 UTC, commit 67d6b99
- [x] 45. HTN depth scaling experiment (depth 2→5) - 2026-04-19 23:08 UTC, commit f9eb25f
- [x] 54. LoCoMo + MemoryAgentBench + MemoryArena benchmark integration - 2026-04-19 23:14 UTC, commit 1a00f7a
- [x] 55. Selective forgetting mechanism (4th competency) - 2026-04-19 23:21 UTC, commit b05f350
- [x] 56. NVIDIA ACE / Inworld latency comparison - 2026-04-19 23:38 UTC, commit 547e9de
- [ ] 59. MLMF multi-layer memory framework
- [ ] 60. Honesty-Humility cross-cultural caveat banner

## Group 10 — IPIP-HEXACO-60 validated input (2-3h)

- [ ] 57. IPIP-HEXACO-60 questionnaire mode (60 Likert items → derived HEXACO vector)

## Group 11 — MiroFish 채용 (3-4h)

- [x] 15. MiroFish-inspired capability additions (15.1 seed-to-personas, 15.2 event injection, 15.3 ReportAgent Q&A, 15.4 A/B compare, 15.5 initial relationships, 15.6 agent interview) - 2026-04-19 19:54 UTC, commit bb347f4

---

## Blocker log pointer

If any sub-task becomes blocked, log it in `planning/codex_blockers.md` (human-readable) AND mark the item here with `[~]`.

## Completion summary (filled by Codex at end)

- Completed: __ / 60
- Blocked: __
- Final commit: ____
- HF Space last deployed: ____
- Release readiness: ____
