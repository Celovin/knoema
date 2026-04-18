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

Composite score compares paired Knoema and naive runs for each scenario/model profile.
- Paired sign-test p-value: 0.000244
- Interpretation: deterministic evidence favors the Knoema memory policy across all paired profiles.

## Metrics

- Memory recall accuracy: deterministic top-k proxy for preserving scenario facts.
- Token efficiency ratio: naive prompt tokens divided by approach prompt tokens.
- Scalability curve: estimated actions/sec at 5, 10, 25, and 50 agents.
- Narrative branching count: branch flags normalized per 100 turns.

## Baseline Discipline

- Naive LLM baseline receives full-history prompt context every turn.
- Mesa stub status: not-measured; Mesa-style agent loops do not provide LLM memory recall without custom extensions.
- Concordia is documented as an external reference only in baselines/concordia_reference.md.
