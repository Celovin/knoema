# Luvoire Bench

Luvoire Bench is a public leaderboard format for persistent-agent simulation
frameworks. It turns the current Luvoire evidence bundle into a repeatable
submission schema so external frameworks can submit comparable rows without
inventing unmeasured claims.

## Axes

| Axis ID | Axis | Primary Meaning | Current Luvoire Source |
| --- | --- | --- | --- |
| `locomo` | LoCoMo | Long-term conversational memory retention proxy | `benchmarks/memory_benchmark_integration/results/summary.json` |
| `memoryagentbench` | MemoryAgentBench | EventQA and fact-consolidation memory proxy | `benchmarks/memory_benchmark_integration/results/summary.json` |
| `memoryarena` | MemoryArena | Decision-relevant memory retrieval proxy | `benchmarks/memory_benchmark_integration/results/summary.json` |
| `mlmf` | MLMF retention | Multi-layer memory retention over episodic, semantic, procedural, and emotional layers | `experiments/mlmf_retention_benchmark/results/summary.json` |
| `theory_of_mind` | ToM Sally-Anne | Opt-in symbolic false-belief tracking | `experiments/theory_of_mind_ablation/results/summary.json` |
| `htn` | HTN planning | Hierarchical goal achievement at depth 3 | `experiments/planning_depth/results/summary.json` |
| `realtime_latency` | Real-time latency | Replay-only tick latency normalized against published real-time character envelopes | `benchmarks/formal_report/results/latency_comparison.json` |

## Scoring Rubric

- Scores are numeric and should use a 0.0-1.0 scale unless an axis explicitly
  documents a raw unit.
- Targets are the acceptance thresholds used for the submitted run.
- A framework passes an axis when `score >= target`.
- The public leaderboard sorts by the average of the seven submitted `score`
  values, then by framework name.
- External framework rows must not include fabricated Concordia, Mesa,
  NetLogo-LLM wrapper, ACE, or Inworld numbers. Use `not-measured` in the caveat
  language when a comparison was not actually run.

## Caveat Language

Each axis has a required caveat. Use it to disclose whether the row is:

- `synthetic`: a synthetic task or fictional scenario, not a real-world claim.
- `deterministic`: a deterministic local harness, not a live model comparison.
- `published`: a published reference envelope used only as a target, not rerun
  under the submitter's environment.

## Contributor Flow

1. Copy `bench/submissions/TEMPLATE.yaml`.
2. Fill every axis, including caveats and source paths.
3. Run `python scripts/validate_submission.py bench/submissions/<name>.yaml`.
4. Run `python scripts/build_leaderboard.py`.
5. Open a pull request with the submission and regenerated leaderboard.
