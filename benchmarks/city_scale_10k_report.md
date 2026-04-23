# 10K Agent City-Scale Benchmark Report

Scenario: `gangnam-10k-city-scale-60x60`
Agents: 10000
Ticks: 100
Repetitions: 3
Backend: `single`
Seed: `20260421`
Grid: 60x60

## Summary

- Median wall-clock time: 15.861854 seconds
- Median throughput: 63044.33 agent-ticks/sec
- Peak RSS: 543.570 MB
- Deterministic output hash: `a81bbde312257d250d13cf44e94a3573aabe826d92ef6e27200b66fdd76bf395`
- Repetition hashes match: `True`
- Deterministic JSONL SHA256: `0453db8f182206471a21543da4cfd531d6dda8dd9a09ab8429b6869b90e3d6cc`
- JSONL hashes match: `True`

## Framework Comparison

| Framework | Status | Agents | Ticks | Median seconds | Agent-ticks/sec | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Luvoire | measured | 10000 | 100 | 15.861854 | 63044.33 | Deterministic local city-scale runner; no live LLM calls. |
| Concordia | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |
| Mesa | not-measured | not-measured | not-measured | not-measured | not-measured | External adapter was not benchmarked in this run. |

Concordia and Mesa are deliberately marked `not-measured`; this report does not invent external framework numbers.
