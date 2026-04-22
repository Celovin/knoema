# Luvoire Docs

Luvoire is an MIT-licensed runtime for persistent agents with memory, relationships, environment context, emotion, events, deterministic logs, and optional LLM-backed decisions.

## Name and Pronunciation

Luvoire is pronounced `/lu?.vw??r/`; the Korean display name is `猷⑤??꾨Ⅴ`.
The name is constructed from the French `-oire` suffix family, echoing memory, history, and repertoire without claiming to be a French dictionary word.

Use these docs when you need an implementation-oriented path through the repo:

- Install the package and run a deterministic simulation.
- Connect game-facing SDK surfaces.
- Build reproducible research scenarios.
- Inspect the public Python API with mkdocstrings.

## Current Surfaces

| Surface | Entry Point |
| --- | --- |
| Core runtime | `src/luvoire` |
| CLI | `luvoire run examples/cli_dorm.yaml --json` |
| Scenario DSL | `docs/dsl/tutorial.md` |
| Playground | `playground/app.py` |
| Game SDK | `docs/sdk/integration_patterns.md` |
| Dashboard | `dashboard/app.py` |
| Research dashboard | `saas/app.py` |

## Safety Boundary

Public-safety examples in this repository are fictional, synthetic, and non-identifying. Luvoire is not a prediction, suspect scoring, surveillance, or enforcement automation system.

## Quick Links

- [Installation](getting-started/installation.md)
- [First Simulation](getting-started/first-simulation.md)
- [Game Integration](guides/game-integration.md)
- [Research Workflow](guides/research-workflow.md)
- [Safety Scenarios](guides/safety-scenarios.md)
- [KNOT Episode 1 Integration](case_studies/01_knot_episode_1_integration.md)
- [Korean University Pilot](case_studies/02_korean_university_pilot.md)
- [Indie Studio Adoption](case_studies/03_indie_studio_adoption.md)
- [CLI Reference](reference/cli.md)
