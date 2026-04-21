# 1K Agent City-Scale Benchmark Report

Scenario: `gangnam-1k-city-scale`
Agents: 1000
Ticks: 100
Repetitions: 3
Backend: `multiprocessing`
Seed: `20260421`

## Summary

- Median wall-clock time: 13.084720 seconds
- Median throughput: 7642.50 agent-ticks/sec
- Peak RSS: 144.426 MB
- Deterministic output hash: `0630fa745fa93a18ec0c37b2718e6cc77c6df632059812ab94d6da4b5af24697`
- Repetition hashes match: `True`

## Framework Comparison

| Framework | Status | Agents | Ticks | Median seconds | Agent-ticks/sec | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Knoema | measured | 1000 | 100 | 13.084720 | 7642.50 | Deterministic local city-scale runner; no live LLM calls. |
| Concordia | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |
| Mesa | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |

Concordia and Mesa are deliberately marked `not-measured`; this report does not invent external framework numbers.
