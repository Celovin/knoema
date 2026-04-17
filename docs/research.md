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
