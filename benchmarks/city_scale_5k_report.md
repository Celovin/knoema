# 5K Agent City-Scale Benchmark Report

Scenario: `gangnam-5k-city-scale-40x40`
Agents: 5000
Ticks: 100
Repetitions: 3
Backend: `single`
Seed: `20260421`
Grid: 40x40

## Summary

- Median wall-clock time: 6.801190 seconds
- Median throughput: 73516.55 agent-ticks/sec
- Peak RSS: 311.004 MB
- Deterministic output hash: `923f55541e1f5e079c2c5e9af58693048d6079ae25a7c07b49dec037248deb26`
- Repetition hashes match: `True`
- Deterministic JSONL SHA256: `78a71d9504d602e810043cf3eb6c2b5730865a89cf600b6ed77eb490893ba9e3`
- JSONL hashes match: `True`

## Framework Comparison

| Framework | Status | Agents | Ticks | Median seconds | Agent-ticks/sec | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Knoema | measured | 5000 | 100 | 6.801190 | 73516.55 | Deterministic local city-scale runner; no live LLM calls. |
| Concordia | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |
| Mesa | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |

Concordia and Mesa are deliberately marked `not-measured`; this report does not invent external framework numbers.
