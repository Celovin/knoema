# 10-Minute Demo Script

Goal: detailed developer and researcher walkthrough covering architecture, reproducibility, and integration paths.

## Segment Plan

| Time | Screen | Narration |
| --- | --- | --- |
| 0:00-0:40 | README and project scope | Luvoire targets three surfaces: game NPCs, fictional public-safety replay research, and academic social simulation. The shared point is persistent agent state with auditable logs. |
| 0:40-1:30 | Architecture section | Walk through persona, memory, relationship, environment, emotion, decision, LLM gateway, simulator, and JSONL export. Emphasize that each part is testable as a Python module. |
| 1:30-2:30 | YAML CLI scenario | Open `examples/cli_dorm.yaml`, then run `luvoire run examples\cli_dorm.yaml --json`. Explain deterministic local responses and prompt language selection. |
| 2:30-3:20 | JSONL log sample | Open the generated JSONL. Point out tick, timestamp, agent ID, action type, target, and content fields. |
| 3:20-4:20 | Playground | Run Dorm: two agents in replay-only mode, then show timeline, relationship graph, JSONL preview, and download. Explain user-supplied API keys are per-session only. |
| 4:20-5:20 | Memory retrieval diagnostics | Show `retrieve_with_scores(...)` in the README and explain semantic, temporal, and importance scoring. |
| 5:20-6:10 | Relationship graph | Show relationship tests or dashboard relationship view. Explain trust, familiarity, and weight as separate edge values. |
| 6:10-7:10 | Dashboard playback | Open the Streamlit dashboard with a sample log and show fixed playback windows plus live-tail controls. |
| 7:10-8:10 | Godot and Unity adapters | Open both adapter READMEs. Explain the HTTP/local fallback protocol and why engine adapters are kept thin. |
| 8:10-9:00 | Competitor matrix | Open `docs/competitor_matrix.md`. Summarize how Luvoire differs from hosted NPC platforms, orchestration frameworks, and classic ABM frameworks. |
| 9:00-9:40 | Verification | Show local `pytest`, `ruff check .`, and `mypy src` passing. Mention GitHub Actions matrix for Python 3.11 and 3.12. |
| 9:40-10:00 | Closing | End with the repository URL, Playground target URL, and next milestones: 50-agent benchmark, reproducibility suite, and scenario DSL. |

## Optional Live Model Variant

Use this only for a live meeting, not for the public recording:

1. Select `OpenAI` or `Anthropic` in the Playground.
2. Paste a personal API key into the password field.
3. Run 1-2 ticks.
4. Clear the field before changing screens.

## Capture Notes

- Resolution: 1920x1080.
- Frame rate: 60 fps.
- Audio: mono or stereo, -16 LUFS target.
- OBS scene order: browser, terminal, editor, dashboard.
- Never record `.env`, API keys, or ignored private planning files.
