# 500-Agent Metropolis

Phase 42 extends the deterministic scale envelope to a 500-agent metropolis rush-hour scenario.

Run:

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python experiments\500_agent_metropolis\run.py
```

Artifacts:

- `results/runs.jsonl`: one deterministic summary row per seed.
- `results/summary.json`: aggregate latency, memory, throughput, relationship, and reproducibility metrics.
- `results/latency_memory.svg`: p95 latency and modeled peak-memory plot across 20 seeds.

The experiment keeps the committed artifacts bit-for-bit reproducible by using deterministic action generation and modeled latency or memory values instead of wall-clock measurements.
