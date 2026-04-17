# Research Positioning

Knoema Engine sits between classical agent-based modeling and LLM-driven generative agents. The MVP demonstrates one shared engine across three domains: game NPCs, fictional public-safety replay research, and academic social simulation.

## Related Work

| Area | Representative Work | Knoema Position |
| --- | --- | --- |
| Generative agents | Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" | Uses persistent memory and social context, but keeps a smaller engine-oriented API. |
| Agent-based modeling | Mesa, AnyLogic | Adds LLM-backed decision generation and language-rich memory. |
| Multi-agent LLM orchestration | AutoGen and similar conversation frameworks | Focuses on simulated social behavior, not task automation. |
| Social simulation environments | Concordia-style research environments | Targets reusable notebooks, game adapters, and dashboard inspection. |

## MVP Evaluation Tracks

### 1. Dormitory Social Simulation

The first notebook runs two synthetic students over seven simulated days. It checks whether repeated interaction produces inspectable action logs, short-term memory, and relationship changes.

### 2. Fictional Crime Scenario Replay

The second notebook uses a synthetic low-severity property incident. The metric is milestone coverage over a known replay trace. The goal is to evaluate process reconstruction, not prediction or attribution.

### 3. Game NPC Memory

The third notebook shows an NPC retrieving player-facing memories across sessions and producing an engine-friendly payload for dialogue and animation.

### 4. Deterministic Throughput Benchmark

The benchmark script runs a local village scenario and reports wall time, actions/sec, and relationship edge counts. Concordia and Mesa rows are present as transparent comparison slots, but they remain `not-measured` until equivalent external adapter runs are executed in the same environment.

### 5. Multilingual Prompt Templates

The prompt layer supports English, Korean, Japanese, and Chinese templates while keeping the JSON action schema stable. This lets researchers compare language-localized agent behavior without changing adapters or dashboard ingestion.

### 6. YAML-Driven CLI Runs

The CLI runs deterministic local simulations from versionable YAML configs. It is intended for reproducible demos, CI smoke checks, and handoff scenarios where notebooks are too interactive.

### 7. Semantic-Temporal Memory Retrieval

The long-term memory store now exposes scored retrieval diagnostics. FAISS produces semantic candidates, then Knoema reranks them with configurable semantic, temporal, and importance weights. This keeps the default list-of-memory API simple while giving researchers visibility into why a memory was selected.

### 8. Realtime Dashboard Playback

The dashboard can follow the latest simulation tick or replay a fixed trailing window. This makes longer JSONL exports easier to inspect while preserving the same export format used by notebooks, CLI runs, and engine adapters.

## Safety Boundary

The repository must keep public-safety examples fictional, synthetic, and non-identifying. Recommended constraints:

- Do not include real incident names, victim names, suspect names, or operational data.
- Use replay metrics such as milestone coverage and trace consistency.
- Avoid predictive claims.
- Keep generated outputs reviewable through logs and notebooks.

## Near-Term Research Questions

- How much memory retrieval is enough for believable long-term NPC behavior?
- Which relationship updates are stable under repeated LLM decisions?
- Can synthetic replay traces help researchers compare hypotheses without using sensitive real data?
- Which dashboard views best expose agent drift, repetitive behavior, and unexpected interactions?
