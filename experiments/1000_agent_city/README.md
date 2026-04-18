# 1000-Agent City Experiment

Phase 52 extends the deterministic scale evidence from the 500-agent metropolis run to a modeled 1000-agent city benchmark.

```powershell
.venv\Scripts\python experiments\1000_agent_city\run.py
```

The experiment writes `results/summary.json` and `results/latency_scaling.svg` for three backends: single-process, process-pool, and Ray. If Ray is not installed, Knoema keeps the Ray row as a modeled envelope and records `ray_available=false`, preserving the optional-dependency contract.
