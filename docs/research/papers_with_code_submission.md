# Papers with Code Submission Packet

This packet is ready for external submission after the arXiv identifier is assigned. Keep `ARXIV_ID_PENDING` unchanged until arXiv accepts the paper.

## Paper Metadata

| Field | Value |
| --- | --- |
| Title | Knoema Engine: An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation |
| arXiv ID | `ARXIV_ID_PENDING` |
| DOI | `10.5281/zenodo.19643409` |
| Repository | `https://github.com/Celovin/knoema` |
| License | MIT |
| Framework | Python |
| Contact | `hello@celovin.com` |
| Paper source | `paper/main.tex` |
| PDF preview | `paper/knoema_technical_report.pdf` |
| Machine packet | `docs/research/papers_with_code_submission.json` |

## Abstract

Knoema Engine is an open runtime for persistent social agents whose state is inspectable outside of a model prompt. It exposes persona, memory, relationship, environment, emotion, optional theory-of-mind belief state, event scheduling, deterministic logs, REST and WebSocket interfaces, scenario DSL artifacts, and game-engine adapters. The v2 report consolidates deterministic evidence for a 500-agent metropolis run, a Sally-Anne false-belief harness, classic Schelling and Axelrod reproductions, and PCS/RCS quality metrics.

## Task Classification

| Task | Positioning |
| --- | --- |
| Multi-agent RL | Runtime and evaluation substrate for multi-agent environments; no policy-training result is claimed. |
| Agent-based modeling | Typed agent state, Scenario DSL, classic ABM reproduction artifacts, and deterministic replay logs. |
| Social simulation | Persistent social-agent runtime with memory, relationships, emotion, and synthetic scenario logs. |
| Theory of mind | Persona opt-in symbolic belief tracker evaluated with a deterministic Sally-Anne false-belief harness. |

## Dataset and Artifact Rows

| Dataset or artifact | Path | Synthetic | Summary |
| --- | --- | --- | --- |
| 500-agent metropolis logs | `experiments/500_agent_metropolis/results/runs.jsonl` | Yes | 20 seeds, 500 agents, 60,000 actions, summary JSON, representative log, latency/memory SVG. |
| Sally-Anne benchmark | `src/knoema/theory_of_mind.py` and `tests/test_phase43_theory_of_mind.py` | Yes | 20 deterministic false-belief and witnessed-move cases. |
| Scenario marketplace library | `scenarios/library/INDEX.md` | Yes | 50 fictional scenarios across school, workplace, family, community, and social-experiment categories. |
| Classic ABM reproductions | `experiments/schelling_segregation` and `experiments/axelrod_prisoners_dilemma` | Yes | Schelling threshold contrast and Axelrod Tit-for-Tat tournament evidence. |
| Scoring artifacts | `benchmarks/scoring/results/metrics.json` | Yes | PCS for 50-agent village logs and RCS for 500-agent representative logs. |

## Result Rows

Use the following table format for Papers with Code. External baseline rows are intentionally left out unless the external project is run in a controlled environment with a recorded commit, dependency set, prompt policy, and seed.

| Model | Task | Dataset | Metric | Value | Better | Source |
| --- | --- | --- | --- | ---: | --- | --- |
| Knoema deterministic local runtime | Social simulation | 500-agent metropolis logs | mean throughput actions/s | 1,657.527 | Higher | `experiments/500_agent_metropolis/results/summary.json` |
| Knoema deterministic local runtime | Social simulation | 500-agent metropolis logs | mean p95 latency ms | 65.055 | Lower | `experiments/500_agent_metropolis/results/summary.json` |
| Knoema persona opt-in ToM | Theory of mind | Sally-Anne benchmark | success rate | 1.000 | Higher | `tests/test_phase43_theory_of_mind.py` |
| Knoema deterministic local runtime | Agent-based modeling | Schelling reproduction | threshold 0.3 segregation index | 0.548 | Target-band | `experiments/schelling_segregation/results/summary.json` |
| Knoema deterministic local runtime | Agent-based modeling | Schelling reproduction | threshold 0.7 segregation index | 0.942 | Target-band | `experiments/schelling_segregation/results/summary.json` |
| Knoema deterministic local runtime | Multi-agent cooperation | Axelrod tournament | Tit-for-Tat rank | 1 | Lower | `experiments/axelrod_prisoners_dilemma/results/summary.json` |
| Knoema scoring utilities | Social simulation | 50-agent village log | PCS average | 0.948 | Higher | `benchmarks/scoring/results/metrics.json` |
| Knoema scoring utilities | Social simulation | 500-agent metropolis representative log | RCS average | 0.760 | Higher | `benchmarks/scoring/results/metrics.json` |

## Comparison Notes

Stanford Generative Agents and Concordia are relevant comparison systems for generative social simulation, but this repository does not report their throughput, Sally-Anne, PCS, or RCS numbers because equivalent external runs have not been performed locally. Mesa, NetLogo, GAMA, Repast, Swarm, MASON, and AnyLogic are ABM references; Knoema compares against their design lineage rather than claiming measured superiority.

## Submission Checklist

- [ ] Confirm arXiv account and endorsement.
- [ ] Submit the paper to arXiv under an appropriate AI or multi-agent systems category.
- [ ] Replace `ARXIV_ID_PENDING` in this file and in the JSON packet.
- [ ] Create the Papers with Code paper entry.
- [ ] Attach the GitHub repository.
- [ ] Add the four tasks: Multi-agent RL, Agent-based modeling, Social simulation, Theory of mind.
- [ ] Add the synthetic datasets and result rows above.
- [ ] Keep the safety boundary in the paper description.

## Safety Boundary

All public-safety examples are fictional, synthetic, and non-identifying. Knoema does not support prediction, suspect scoring, surveillance, enforcement automation, or profiling of identifiable people.
