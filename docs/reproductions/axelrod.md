# Axelrod Reproduction

This reproduction runs a deterministic 10-strategy iterated prisoner's dilemma tournament with 200 rounds per pairing.

## What Is Reproduced

- The deterministic tournament keeps Tit-for-Tat inside the top three strategies.
- Cooperative leaders are selected from strategies whose cooperation rate remains at or above `0.6`.
- The same strategy catalog is reported for `deterministic`, `ollama`, and `api` labels without invoking external providers.

## Artifact Paths

- `experiments/axelrod_prisoners_dilemma/config.yaml`
- `experiments/axelrod_prisoners_dilemma/run.py`
- `experiments/axelrod_prisoners_dilemma/results/runs.jsonl`
- `experiments/axelrod_prisoners_dilemma/results/summary.json`
- `experiments/axelrod_prisoners_dilemma/results/scoreboard.svg`
