# 100K Agent Aggregate City-Scale Benchmark Report

Scenario: `gangnam-100k-city-scale-aggregate`
Agents: 100000
Ticks: 100
Repetitions: 1
Backend: `single`
Trace mode: `aggregate`
Sampled agents: 1000
Seed: `20260421`
Grid: 200x200

## Summary

- Median wall-clock time: 103.922122 seconds
- Median throughput: 96225.90 agent-ticks/sec
- Peak RSS: 243.980 MB
- Deterministic output hash: `0faaf29cf454702459e5d5f78601409418b28fb6f5f3acd01d33e0e87b9d512f`
- Repetition hashes match: `True`
- Aggregate JSONL SHA256: `38ef9e542700b8efcf9ef80d5055b9745add824da196de844428821f41dde059`
- Sample frame JSONL SHA256: `3d5dfdf08acf775b43e4a3c97bcc90d9ec20ff55d22c061e45f7f3e6994d7787`

## Framework Comparison

| Framework | Status | Agents | Ticks | Median seconds | Agent-ticks/sec | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Luvoire | measured | 100000 | 100 | 103.922122 | 96225.90 | Deterministic aggregate city-scale runner; sampled frames only; no live LLM calls. |
| Concordia | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |
| Mesa | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |

Concordia and Mesa are deliberately marked `not-measured`; this report does not invent external framework numbers.
