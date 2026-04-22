# Luvoire Bench Methodology

Luvoire Bench uses seven axes because the current public evidence bundle spans
memory, planning, belief tracking, and runtime latency. The goal is not to claim
that one score fully summarizes a framework; it is to make evidence boundaries
visible in a single table.

## Statistical Basis

- LoCoMo, MemoryAgentBench, MemoryArena, MLMF, ToM Sally-Anne, and HTN rows are
  deterministic synthetic harnesses generated from committed repository
  artifacts.
- Real-time latency uses measured Luvoire replay-only tick latency normalized
  against published ACE and Inworld target envelopes. It is not an audio-input
  to audio-output conversational pipeline benchmark.
- Published reference rows are treated as target envelopes unless the external
  framework is rerun under a recorded commit, dependency set, prompt policy,
  seed set, and output artifact.

## Caveat Categories

`synthetic` means the row uses fictional or generated tasks rather than a
real-world deployment claim.

`deterministic` means the row uses local deterministic clients or scripted
responses to preserve replayability.

`published` means the row cites a public target or envelope. It does not mean
the referenced external system was rerun inside this repository.

## No-Fabricated-Numbers Rule

Concordia, Mesa, NetLogo-LLM wrappers, NVIDIA ACE, and Inworld rows must remain
absent or explicitly caveated as not measured unless a contributor provides
reproducible run artifacts.
