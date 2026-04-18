# Formal Benchmark Report v1

## Run Matrix

- Scenarios: 4
- Approaches: Knoema memory policy and naive full-context LLM baseline
- Model profiles: local-small, local-medium, local-large
- Total deterministic runs: 24

## Scenario Summary

| Scenario | Approach | Recall@k | Token efficiency | Actions/sec | Branches / 100 turns |
| --- | --- | ---: | ---: | ---: | ---: |
| A memory_recall | knoema | 0.789 | 4.662 | 1141.626 | 6.650 |
| A memory_recall | naive_llm | 0.500 | 1.000 | 707.620 | 4.947 |
| B relationship_dynamics | knoema | 0.786 | 4.482 | 1053.809 | 7.838 |
| B relationship_dynamics | naive_llm | 0.495 | 1.000 | 631.120 | 5.830 |
| C narrative_branching | knoema | 0.784 | 4.429 | 1095.961 | 11.400 |
| C narrative_branching | naive_llm | 0.492 | 1.000 | 667.184 | 8.480 |
| D scalability | knoema | 0.780 | 4.280 | 608.868 | 5.971 |
| D scalability | naive_llm | 0.487 | 1.000 | 311.353 | 4.442 |

## Significance

Composite score compares paired Knoema and naive runs for each scenario or model profile.
- Paired sign-test p-value: 0.000244
- Interpretation: deterministic evidence favors the Knoema memory policy across all paired profiles.

## Metrics

- Memory recall accuracy: deterministic top-k proxy for preserving scenario facts.
- Token efficiency ratio: naive prompt tokens divided by approach prompt tokens.
- Scalability curve: estimated actions/sec at 5, 10, 25, and 50 agents, plus a 500-agent metropolis appendix.
- Narrative branching count: branch flags normalized per 100 turns.

## Baseline Discipline

- Naive LLM baseline receives full-history prompt context every turn.
- Mesa stub status: not-measured; Mesa-style agent loops do not provide LLM memory recall without custom extensions.
- Concordia is documented as an external reference only in baselines/concordia_reference.md.
- Stanford Generative Agents is documented as an external reference only in baselines/stanford_reference.md.

## Phase 42 Metropolis Appendix

- Summary source: experiments/500_agent_metropolis/results/summary.json
- Figure source: results/figures/metropolis_scale.svg

| Metric | Knoema 500-Agent Metropolis | Google DeepMind Concordia | Stanford Generative Agents |
| --- | --- | --- | --- |
| Comparison status | Measured local deterministic run | External reference only | External reference only |
| Agent scale | 500 agents x 20 seeds | Not measured in this repo | 25-agent sandbox in paper |
| Latency / memory | p95 65.055 ms / max 436.000 MB | Equivalent adapter run required | Equivalent adapter run required |
| Throughput | mean 1657.527 actions/sec | Equivalent adapter run required | Paper or code reference only |
| Artifacts | JSONL + summary.json + SVG | Separate appendix needed | Separate appendix needed |
| Surface | Godot + Unity scaffolds, Korean prompt surface | No packaged game-engine adapter | No packaged game-engine adapter |
