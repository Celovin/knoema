# Effort Allocation by Sub-task

This document translates the 60 execution sub-tasks into a repository-backed person-hour plan that can be compared against the 1.5-year R&D budget narrative in `planning/본문1_연구개발계획서_초안.md`.

## Assumptions

1. These are **software-deliverable estimates only**. They do not attempt to price external professor time, travel, commercialization, or institutional overhead.
2. The numbers are **planning estimates**, not timesheet measurements. They represent the auditable coding, testing, documentation, and packaging effort attached to each sub-task.
3. Budget comparison is done through two dimensions:
   - `Phase`: Phase 1 core engine, Phase 2 adapters/productization, Phase 3 validation and evaluator packaging.
   - `Budget lane`: the closest proposal bucket for personnel allocation.

## Budget Lanes

| Budget lane | What it covers |
| --- | --- |
| Core runtime and simulation | Typed runtime, memory, planning, prompts, streaming, caching, and engine behavior |
| UX and control surface | Playground layout, controls, visualization, accessibility, and operator-facing UX |
| Application B game delivery | Game-domain actions, routines, player loop, voice mode, adapters, and demos |
| Application C research delivery | Statistics, preregistration, exports, replication, deposit, and validated input layers |
| Validation and benchmark | Benchmark harnesses, ablations, scaling studies, and comparative measurement |
| Compliance and audit docs | Reviewer mode, ethics gates, mapping docs, effort docs, and cross-cultural caveats |

## Summary

| Rollup | Hours |
| --- | ---: |
| Group 1 | 4.75 |
| Group 2 | 6.00 |
| Group 3 | 6.50 |
| Group 4 | 5.50 |
| Group 5 | 9.25 |
| Group 6 | 8.50 |
| Group 7 | 12.25 |
| Group 8 | 5.75 |
| Group 9 | 15.00 |
| Group 10 | 2.50 |
| Group 11 | 2.25 |
| Total tracked hours | 78.25 |

## Canonical Row-Level Allocation

| ID | Sub-task | Hours | Phase | Budget lane |
| ---: | --- | ---: | --- | --- |
| 1 | Relationship graph widened and timeline stacked | 1.00 | Phase 2 | UX and control surface |
| 2 | Agent count override slider | 1.25 | Phase 2 | UX and control surface |
| 3 | Big Five info hints and clearer Korean label | 0.75 | Phase 2 | UX and control surface |
| 4 | Environment presets | 1.50 | Phase 1 | Core runtime and simulation |
| 5 | 30-trait personality layer | 2.00 | Phase 1 | Core runtime and simulation |
| 6 | Persona archetype presets | 1.25 | Phase 2 | UX and control surface |
| 7 | Three-agent tab editor | 1.50 | Phase 2 | UX and control surface |
| 8 | Action breakdown chart | 1.25 | Phase 2 | UX and control surface |
| 9 | Tick scrubber and focus view | 1.00 | Phase 2 | UX and control surface |
| 10 | Memory inspector | 1.25 | Phase 2 | UX and control surface |
| 11 | Consistent agent colors | 0.75 | Phase 2 | UX and control surface |
| 12 | HTML report export | 1.00 | Phase 3 | Application C research delivery |
| 13 | Scenario-specific guidance hints | 0.75 | Phase 2 | UX and control surface |
| 14 | 30-scenario library | 1.75 | Phase 2 | UX and control surface |
| 15 | Seed-to-persona, event injection, report, compare, interview bundle | 2.25 | Phase 2 | UX and control surface |
| 16 | 20 social action verbs | 1.25 | Phase 1 | Core runtime and simulation |
| 17 | Inner monologue layer | 1.25 | Phase 1 | Core runtime and simulation |
| 18 | WebSocket live tick streaming | 1.50 | Phase 1 | Core runtime and simulation |
| 19 | HTN planning hookup | 1.50 | Phase 1 | Core runtime and simulation |
| 20 | Conversation thread view | 1.00 | Phase 2 | UX and control surface |
| 21 | Per-agent PAD trajectory | 1.00 | Phase 2 | UX and control surface |
| 22 | Spatial heatmap | 1.00 | Phase 2 | UX and control surface |
| 23 | Sankey action-flow diagram | 1.00 | Phase 2 | UX and control surface |
| 24 | Statistical analysis panel | 1.25 | Phase 3 | Application C research delivery |
| 25 | Batch run mode | 1.25 | Phase 3 | Application C research delivery |
| 26 | Cultural prior modules | 1.50 | Phase 1 | Core runtime and simulation |
| 27 | CSV and LaTeX export | 1.00 | Phase 3 | Application C research delivery |
| 28 | Built-in tutorial walkthrough | 1.00 | Phase 2 | UX and control surface |
| 29 | Competitive comparison table | 0.75 | Phase 3 | Validation and benchmark |
| 30 | LLM cache and async I/O | 1.50 | Phase 1 | Core runtime and simulation |
| 31 | Game-domain action verbs | 1.50 | Phase 2 | Application B game delivery |
| 32 | NPC daily routine system | 1.50 | Phase 2 | Application B game delivery |
| 33 | Player-as-agent mode | 1.75 | Phase 2 | Application B game delivery |
| 34 | Godot and Unity tavern demos | 1.50 | Phase 2 | Application B game delivery |
| 35 | OSF preregistration generator | 1.50 | Phase 3 | Application C research delivery |
| 36 | Mixed effects and Bayesian posterior | 1.75 | Phase 3 | Application C research delivery |
| 37 | Replication package bundler | 1.50 | Phase 3 | Application C research delivery |
| 38 | Reviewer-mode anonymization | 1.00 | Phase 3 | Compliance and audit docs |
| 39 | Dark Tetrad IRB consent gate | 1.00 | Phase 3 | Compliance and audit docs |
| 40 | Proposal mapping document | 0.75 | Phase 3 | Compliance and audit docs |
| 41 | Trait correlation matrix and ablation | 1.75 | Phase 3 | Validation and benchmark |
| 42 | Effort allocation document | 0.75 | Phase 3 | Compliance and audit docs |
| 43 | Memory retrieval recall@k benchmark | 1.75 | Phase 3 | Validation and benchmark |
| 44 | ToM Sally-Anne tier ablation | 1.50 | Phase 3 | Validation and benchmark |
| 45 | HTN depth scaling experiment | 1.50 | Phase 3 | Validation and benchmark |
| 46 | Procedural quest generation | 1.25 | Phase 2 | Application B game delivery |
| 47 | NPC coordination and resource conflict handling | 1.25 | Phase 2 | Application B game delivery |
| 48 | Voice conversation mode | 1.25 | Phase 2 | Application B game delivery |
| 49 | Mini-map | 1.00 | Phase 2 | UX and control surface |
| 50 | Power analysis and sample size planner | 1.25 | Phase 3 | Application C research delivery |
| 51 | arXiv and Zenodo deposit flow | 1.25 | Phase 3 | Application C research delivery |
| 52 | Theme system | 0.75 | Phase 2 | UX and control surface |
| 53 | WCAG 2.1 AA sweep | 1.00 | Phase 3 | Compliance and audit docs |
| 54 | LoCoMo, MemoryAgentBench, MemoryArena integration | 2.00 | Phase 3 | Validation and benchmark |
| 55 | Selective forgetting mechanism | 1.75 | Phase 1 | Core runtime and simulation |
| 56 | NVIDIA ACE and Inworld latency comparison | 1.25 | Phase 3 | Validation and benchmark |
| 57 | IPIP-HEXACO-60 questionnaire mode | 2.50 | Phase 3 | Application C research delivery |
| 58 | OSF simulation-studies template | 1.00 | Phase 3 | Application C research delivery |
| 59 | Multi-layer memory framework | 2.00 | Phase 1 | Core runtime and simulation |
| 60 | Honesty-Humility cross-cultural caveat | 0.75 | Phase 3 | Compliance and audit docs |

## Readout for Evaluators

- The table is intentionally conservative and repository-scoped. It is suitable for tracing where software labor sits inside the proposal, but it should not be misread as a payroll ledger.
- Phase 1-heavy items cluster around runtime, memory, and planning because those are prerequisite enablers for every later demo surface.
- Phase 3-heavy items cluster around academic packaging and benchmark work because evaluator-facing evidence generation depends on features already existing.
