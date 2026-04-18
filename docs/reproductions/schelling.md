# Schelling Reproduction

This reproduction uses a deterministic 50x50 grid with 2,000 agents, three similarity thresholds, and three labeled runtime modes.

## What Is Reproduced

- Threshold `0.3` yields a medium segregation regime near `0.5`.
- Threshold `0.7` yields a highly segregated regime near `0.95`.
- The committed acceptance target is the `deterministic` mode.

## Artifact Paths

- `experiments/schelling_segregation/config.yaml`
- `experiments/schelling_segregation/run.py`
- `experiments/schelling_segregation/results/runs.jsonl`
- `experiments/schelling_segregation/results/summary.json`
- `experiments/schelling_segregation/results/segregation_curve.svg`

## Notes

The reported segregation score is a block-based neighborhood dissimilarity index. This keeps the implementation deterministic and compact while preserving the expected qualitative behavior of the original model.
