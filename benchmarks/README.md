# Benchmarks

This directory contains deterministic benchmark helpers for Knoema Engine.

The default benchmark runs a local 10-agent village simulation with no network access, no API keys, and no external framework dependency. It measures the Knoema simulator path and emits JSON plus Markdown reports.

```powershell
cd C:\Users\admin\Projects\knoema
python benchmarks\run_benchmark.py `
  --agents 10 `
  --duration-days 1 `
  --tick-minutes 60 `
  --repetitions 3 `
  --json-output runs\benchmark.json `
  --markdown-output runs\benchmark.md
```

The Markdown report includes explicit comparison slots for Concordia and Mesa. Those rows are marked `not-measured` unless equivalent external adapter runs are performed. This avoids claiming external performance numbers without running the same scenario under the same environment.

The Phase 20 formal bundle expands this into 24 deterministic runs, source SVG figures, a Markdown summary, and a 20-page PDF report. The bundle now also imports the Phase 42 deterministic 500-agent metropolis appendix for scale evidence, the Phase 43 Sally-Anne theory-of-mind appendix, and the Phase 45 classic reproduction summaries:

```powershell
python benchmarks\formal_report\runner.py
```

See [formal_report/README.md](formal_report/README.md) and [formal_report/report.pdf](formal_report/report.pdf).

Recommended comparison discipline:

- Keep agent count, tick cadence, duration, and local deterministic policy equivalent.
- Record Python version, platform, and dependency versions.
- Report wall time and actions/sec separately from qualitative feature comparisons.
- Do not vendor external project source code into this repository.
