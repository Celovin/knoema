# Academic Indexing

Phase 31 prepares Knoema Engine for archival citation and research indexing. The repository now carries machine-readable citation metadata, Zenodo metadata, and a submission packet for Papers with Code. External account steps still need to be completed by the project owner.

## Repository Record

| Field | Value |
| --- | --- |
| Repository | `https://github.com/Celovin/knoema` |
| Release | `v0.1.0` |
| License | MIT |
| Software metadata | `CITATION.cff` |
| Zenodo metadata | `.zenodo.json` |
| Paper source | `paper/main.tex` |
| PDF preview | `paper/knoema_technical_report.pdf` |

Zenodo reads `.zenodo.json` as the authoritative GitHub integration metadata when both `.zenodo.json` and `CITATION.cff` are present. The repository therefore keeps the fuller deposit metadata in `.zenodo.json` and the general citation metadata in `CITATION.cff`.

## Zenodo DOI Packet

Use this packet when connecting the repository to Zenodo:

- Title: `Knoema Engine: An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation`
- Creator: `Celovin`
- Contact: `hello@celovin.com`
- Upload type: `software`
- Version: `0.1.0`
- License: MIT, encoded for Zenodo as `mit`
- Repository: `https://github.com/Celovin/knoema`
- Related paper source: `https://github.com/Celovin/knoema/blob/main/paper/main.tex`
- Safety note: all public-safety examples are fictional, synthetic, and non-identifying; the system is not designed for prediction, suspect scoring, surveillance, or enforcement automation.

Recommended owner steps:

1. Sign in to Zenodo with the Celovin-controlled account.
2. Enable GitHub integration for `Celovin/knoema`.
3. Import or archive the `v0.1.0` release. If the integration cannot backfill existing releases, archive the next patch release and keep `v0.1.0` as the GitHub release evidence.
4. Confirm Zenodo imported `.zenodo.json` and `CITATION.cff`.
5. Copy the assigned DOI into `CITATION.cff`, `.zenodo.json`, `README.md`, `README.ko.md`, `paper/README.md`, and the website research page.

README badge replacement after DOI assignment:

```markdown
[![DOI](https://zenodo.org/badge/DOI/DOI_VALUE.svg)](https://doi.org/DOI_VALUE)
```

## Papers With Code Packet

Use this packet when creating a Papers with Code entry:

- Paper title: `Knoema Engine: An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation`
- Abstract source: `paper/abstract.tex`
- Code repository: `https://github.com/Celovin/knoema`
- Framework: Python
- License: MIT
- Primary tasks:
  - Multi-agent simulation
  - Agent-based modeling
  - Social simulation
  - Game NPC behavior
  - Reproducible LLM agent evaluation
- Evaluation artifacts:
  - `experiments/50_agent_village/results/metrics.json`
  - `benchmarks/formal_report/results/summary.md`
  - `benchmarks/formal_report/results/raw.jsonl`
  - `docs/reports/reproducibility.md`
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
| Zenodo DOI | Pending external account integration |
| Papers with Code entry | Pending external submission |
| README badges | Pending-state badges added |
