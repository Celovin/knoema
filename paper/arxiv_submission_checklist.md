# arXiv v2 Submission Checklist

This checklist is for the human arXiv account owner. Do not use an automated
agent to click the final submit button or to request endorsement.

## Local Artifacts

- Run: `python paper/build_arxiv_bundle.py`
- Upload source bundle: `dist/luvoire_arxiv_v2.tar.gz`
- Local preview PDF: `dist/luvoire_arxiv_v2.pdf`
- Visual proof renders: `tmp/arxiv_render/first_page-01.png` and the
  `tmp/arxiv_render/last_page-*.png` file produced for the final page.

## arXiv Form Fields

Primary category: `cs.MA`

Secondary category: `cs.AI`

License: `CC BY 4.0` is recommended for the preprint. The software repository
itself remains MIT licensed.

### Title Block

```text
Luvoire: An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation
```

### Abstract Block

```text
Luvoire is an open, MIT-licensed runtime for persistent social agents whose state is inspectable outside of a model prompt. The system combines persona definitions, short-term and long-term memory, directed relationship state, environment context, PAD-style emotion, optional persona-level theory-of-mind tracking, event scheduling, deterministic logs, REST and WebSocket interfaces, game-engine adapters, and optional LLM-backed decisions. This arXiv v2 report consolidates the Phase 30 preprint structure with the Phase 43--46 evidence layer: a persona opt-in Sally-Anne false-belief harness, classic Schelling and Axelrod reproductions, a 500-agent deterministic metropolis run, and Persona Consistency Score and Relationship Coherence Score metrics. Luvoire demonstrates a triple-use runtime surface for persistent game NPCs, fictional synthetic replay research, and reproducible academic simulation while keeping each claim tied to seeds, configs, logs, and package tests. The central engineering claim is modest: persistent-agent applications need explicit runtime state, replayable artifacts, adapter contracts, and safety-bounded scenario definitions before they need larger prompts. Public-safety examples are fictional, synthetic, and non-identifying; the system is not designed for prediction, suspect scoring, surveillance, or enforcement automation.
```

### Author Block

Preferred:

```text
Celovin
```

Optional real-name expansion, if the account owner wants the arXiv author line
to include it:

```text
Celovin (Jihwan Choi)
```

Contact email for repository metadata: `hello@celovin.com`

## Source Bundle Contents to Confirm

- `main.tex`
- `appendix.tex`
- `abstract.tex`
- `references.bib`
- `main.bbl`
- `sections/*.tex`
- `tables/*.tex`
- `figures/*.tex`

## Endorsement Request Template

Subject: arXiv cs.MA endorsement request for Luvoire preprint

```text
Dear [endorser name],

I am preparing to submit a cs.MA preprint titled "Luvoire: An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation" and would be grateful if you would consider endorsing the submission category.

The paper presents an open, MIT-licensed runtime for persistent social agents with explicit state, deterministic replay artifacts, benchmark evidence, game-adapter surfaces, and safety-bounded fictional scenario definitions. The work is positioned as agent-based modeling and reproducible simulation infrastructure rather than as a human-behavior prediction claim.

If you are open to reviewing the submission for endorsement fit, I can send the PDF, source bundle, and repository link.

Thank you,
Celovin
```

After arXiv assigns the identifier, run:

```text
python scripts/set_arxiv_id.py YYMM.NNNNN
```
