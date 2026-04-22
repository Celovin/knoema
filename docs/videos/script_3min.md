# 3-Minute Demo Script

Goal: professor meeting walkthrough focused on research credibility and visible execution.

## Segment Plan

| Time | Screen | Narration |
| --- | --- | --- |
| 0:00-0:15 | README top and badges | Luvoire is a public MIT-licensed engine for LLM-based multi-agent social simulation. It is not a prediction or profiling tool; the public-safety examples are fictional replay research demos. |
| 0:15-0:35 | Architecture diagram | The runtime combines persona, short-term memory, long-term retrieval, relationship graph, environment context, emotion state, and LLM decisions. |
| 0:35-1:05 | Playground, replay-only Dorm scenario | The browser demo runs without an API key. Select Dorm: two agents, keep defaults, and run a short deterministic replay. |
| 1:05-1:30 | Timeline and JSONL output | Every simulation step is exported as JSONL, so a reviewer can replay, audit, or analyze the run instead of relying on a screenshot. |
| 1:30-1:50 | Relationship graph | The relationship model is explicit: trust, familiarity, and interaction weight are stored as directed edges. |
| 1:50-2:15 | CLI and notebooks | The same scenario style runs from YAML through the CLI and from notebooks for research workflows. |
| 2:15-2:35 | Godot and Unity adapters | Game integration is separated into adapter scaffolds so the engine can remain a Python research core while games consume a stable protocol. |
| 2:35-2:50 | Competitor matrix | Compared with orchestration frameworks, hosted NPC platforms, and classic ABM tools, the differentiator is open reproducibility plus game-facing integration. |
| 2:50-3:00 | Roadmap | The next proof points are larger-scale benchmarks, reproducibility tests, and domain-specific scenario DSLs. |

## Demo Commands

```powershell
cd C:\Users\admin\Projects\luvoire
.venv\Scripts\python -m pytest
luvoire run examples\cli_dorm.yaml --json
```

## Capture Notes

- Use a clean browser profile or private window.
- Do not show API keys.
- Use replay-only mode for the recorded version.
- Keep terminal output short: final test count, CLI JSON summary, and generated JSONL path.
