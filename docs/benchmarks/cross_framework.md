# Cross-Framework Benchmark

The Phase 57 benchmark positions Luvoire against five adjacent frameworks:
AutoGen, CrewAI, LangGraph, Mesa, and NetLogo.

The common scenario is a 5-agent dormitory run over 7 days. The benchmark records:

- Throughput in actions per second.
- Memory footprint in megabytes.
- Persona Consistency Score.
- Reproducibility score.
- Code lines needed to configure the scenario.
- License posture.

Luvoire ranks first on Persona Consistency Score and reproducibility in the committed deterministic envelope. Its configuration is also less than half the line count of the AutoGen and CrewAI rows.

See `benchmarks/cross_framework/results/summary.md` for the committed table and `benchmarks/cross_framework/run_comparison.py` for the reproducible generator.
