# Academic Indexing

Phase 31 prepared Knoema Engine for archival citation and research indexing. Phase 50 adds the arXiv v2 and Papers with Code packet. Phase 62 promotes the repository metadata to `v0.2.0`. The repository now carries machine-readable citation metadata, Zenodo metadata, the final local paper source, a generated PDF preview, and a structured Papers with Code submission packet. External account steps still need to be completed by the project owner.

## Repository Record

| Field | Value |
| --- | --- |
| Repository | `https://github.com/Celovin/knoema` |
| Release | `v0.2.0` |
| Concept DOI (always-latest) | [`10.5281/zenodo.19643409`](https://doi.org/10.5281/zenodo.19643409) |
| v0.2.0 DOI | [`10.5281/zenodo.19645166`](https://doi.org/10.5281/zenodo.19645166) |
| v0.1.1 DOI | [`10.5281/zenodo.19643410`](https://doi.org/10.5281/zenodo.19643410) |
| License | MIT |
| Software metadata | `CITATION.cff` |
| Zenodo metadata | `.zenodo.json` |
| Paper source | `paper/main.tex` |
| PDF preview | `paper/knoema_technical_report.pdf` |
| Papers with Code packet | `docs/research/papers_with_code_submission.md` |
| Papers with Code JSON | `docs/research/papers_with_code_submission.json` |

Zenodo reads `.zenodo.json` as the authoritative GitHub integration metadata when both `.zenodo.json` and `CITATION.cff` are present. The repository therefore keeps the fuller deposit metadata in `.zenodo.json` and the general citation metadata in `CITATION.cff`.

## Zenodo DOI Packet

Use this packet when connecting the repository to Zenodo:

- Title: `Knoema Engine: An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation`
- Creator: `Celovin`
- Contact: `hello@celovin.com`
- Upload type: `software`
- Version: `0.2.0`
- Concept DOI (recommended for citation, always resolves to latest version): `10.5281/zenodo.19643409`
- Latest version DOI: `10.5281/zenodo.19645166` (v0.2.0)
- Earlier version DOI: `10.5281/zenodo.19643410` (v0.1.1)
- License: MIT, encoded for Zenodo as `mit`
- Repository: `https://github.com/Celovin/knoema`
- Related paper source: `https://github.com/Celovin/knoema/blob/main/paper/main.tex`
- Safety note: all public-safety examples are fictional, synthetic, and non-identifying; the system is not designed for prediction, suspect scoring, surveillance, or enforcement automation.

Recommended owner steps:

1. Sign in to Zenodo with the Celovin-controlled account.
2. Enable GitHub integration for `Celovin/knoema`.
3. Import or archive the `v0.2.0` release; both `v0.1.1` (`19643410`) and `v0.2.0` (`19645166`) are now archived under the shared concept record (`19643409`).
4. Confirm Zenodo imported `.zenodo.json` and `CITATION.cff`.
5. Reference the concept DOI (`10.5281/zenodo.19643409`) in citations and badges so readers always resolve to the latest archived version.

README badge replacement after DOI assignment:

```markdown
[![DOI](https://zenodo.org/badge/DOI/DOI_VALUE.svg)](https://doi.org/DOI_VALUE)
```

## Papers With Code Packet

Use `docs/research/papers_with_code_submission.md` as the primary operator packet and `docs/research/papers_with_code_submission.json` as the machine-readable companion. The packet uses `ARXIV_ID_PENDING` until arXiv assigns the accepted identifier.

- Paper title: `Knoema Engine: An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation`
- Abstract source: `paper/abstract.tex`
- Code repository: `https://github.com/Celovin/knoema`
- Framework: Python
- License: MIT
- Primary tasks:
  - Multi-agent RL
  - Agent-based modeling
  - Social simulation
  - Theory of mind
- Evaluation artifacts:
  - `experiments/500_agent_metropolis/results/summary.json`
  - `experiments/500_agent_metropolis/results/runs.jsonl`
  - `experiments/50_agent_village/results/metrics.json`
  - `tests/test_phase43_theory_of_mind.py`
  - `experiments/schelling_segregation/results/summary.json`
  - `experiments/axelrod_prisoners_dilemma/results/summary.json`
  - `benchmarks/scoring/results/metrics.json`
  - `benchmarks/formal_report/results/summary.md`
  - `scenarios/library/INDEX.md`
- Public-safety boundary: fictional, synthetic, non-identifying replay only; no prediction, suspect scoring, surveillance, or enforcement automation.

Suggested short description:

```text
Knoema Engine is an open runtime for persistent social agents. It exposes memory, relationships, emotion, environment state, deterministic logs, scenario DSLs, and game SDK adapters so agent behavior can be inspected and reproduced outside a model prompt.
```

## Status

| Item | Status |
| --- | --- |
| `CITATION.cff` | Prepared |
| `.zenodo.json` | Prepared |
| Zenodo concept DOI | Wired: `10.5281/zenodo.19643409` (always-latest) |
| v0.2.0 DOI | Wired: `10.5281/zenodo.19645166` (2026-04-19) |
| v0.1.1 DOI | Archived: `10.5281/zenodo.19643410` |
| Papers with Code packet | Prepared locally with `ARXIV_ID_PENDING` |
| Papers with Code entry | Pending external submission after arXiv ID |
| README badges | DOI badge live (all eight language variants) |
