# Schelling Segregation Reproduction

This experiment reproduces the qualitative outcome of Schelling's segregation model with a deterministic 50x50 grid and 2,000 agents split evenly across two groups.

Outputs:

- `results/runs.jsonl`: one row per threshold and mode
- `results/summary.json`: aggregate metrics and alignment checks
- `results/segregation_curve.svg`: threshold-to-segregation plot

The `deterministic` mode is the acceptance target. `ollama` and `api` are labeled deployment surfaces that reuse the same seeded move policy so the committed artifacts stay reproducible.
