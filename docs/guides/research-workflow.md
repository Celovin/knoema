# Research Workflow Guide

Knoema research workflows should be reproducible before they are persuasive.

## Baseline Workflow

1. Define a synthetic scenario in YAML.
2. Validate it with the DSL parser and guardrails.
3. Run deterministic local simulations with fixed seeds.
4. Export JSONL logs.
5. Replay logs through the dashboard or research SaaS scaffold.
6. Record config, seed, commit hash, logs, and summary metrics.

## Useful Surfaces

- Scenario docs: `docs/dsl/tutorial.md`
- Reproducibility report: `docs/reports/reproducibility.md`
- Formal benchmark: `benchmarks/formal_report/README.md`
- 50-agent experiment: `experiments/50_agent_village/README.md`
- Research dashboard: `saas/app.py`

## Claims Discipline

Keep claims tied to committed artifacts:

- State the config and seed used.
- State whether a provider call or deterministic local client was used.
- Keep third-party baseline comparisons transparent when not reimplemented.
- Treat outputs as simulation artifacts, not empirical claims about real people.
