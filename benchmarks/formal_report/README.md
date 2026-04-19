# Formal Benchmark Report

Phase 20 turns the compact benchmark helper into a reproducible report bundle for review meetings and proposal evidence.

The bundle uses deterministic local metrics only. It does not call external LLM APIs and does not claim measured numbers for external frameworks.

## Run

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python benchmarks\formal_report\runner.py
```

Outputs:

- `results/raw.jsonl`: 24 deterministic runs across 4 scenarios, 2 approaches, and 3 local model profiles.
- `results/summary.md`: aggregate tables, metric definitions, paired sign-test p-value, the Phase 42 and Phase 52 scale appendices, the Phase 43 theory-of-mind appendix, and the Phase 45 classic reproduction section.
- `results/latency_comparison.json`: measured Playground replay/OpenAI tick latency plus cited NVIDIA ACE and Inworld reference envelopes.
- `results/figures/*.svg`: source figures for recall, token efficiency, scalability, branching, the Phase 42 metropolis appendix, and the Phase 52 1000-agent city appendix.
- `report.pdf`: 20-page formal benchmark report.

Use `--skip-pdf` when running in environments without the optional `paper` dependencies.
