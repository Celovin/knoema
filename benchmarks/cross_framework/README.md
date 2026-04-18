# Cross-Framework Comparison Benchmark

Phase 57 compares Knoema with AutoGen, CrewAI, LangGraph, Mesa, and NetLogo on a common 5-agent dormitory scenario envelope.

The committed rows are deterministic adapter-envelope rows. They capture configuration effort, memory footprint, persona consistency, reproducibility, and local throughput under the same reporting schema. They are not claims of externally optimized production throughput for the other frameworks.

## Run

```bash
python benchmarks/cross_framework/run_comparison.py
```

or through the isolated container envelope:

```bash
docker compose -f benchmarks/cross_framework/docker-compose.yml up --build
```

Outputs are written to `benchmarks/cross_framework/results/summary.json` and `benchmarks/cross_framework/results/summary.md`.
