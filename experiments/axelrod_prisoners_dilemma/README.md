# Axelrod Prisoner's Dilemma Reproduction

This experiment reproduces a deterministic iterated prisoner's dilemma tournament with 10 strategies and 200 rounds per pairing.

Outputs:

- `results/runs.jsonl`: one row per mode and strategy
- `results/summary.json`: rankings, cooperation rates, and acceptance checks
- `results/scoreboard.svg`: strategy score plot

The committed acceptance target is the `deterministic` mode, where Tit-for-Tat style behavior should remain inside the top three strategies under cooperative tournament conditions.
