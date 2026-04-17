# Knoema Engine

> **LLM-based multi-agent social simulation engine for games, public safety, and academic research.**

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Korean: [README.ko.md](README.ko.md)

---

## 🌐 Three Applications, One Engine

Knoema Engine provides a unified runtime for modeling persistent, emotionally aware, socially connected agents — and then plugs that runtime into three very different production domains:

| Domain | Use | Release Track |
|--------|-----|---------------|
| 🎮 **Games** | Persistent-memory NPCs with dynamic narrative branching | Godot/Unity adapters, commercial SDK |
| 🛡️ **Public Safety** | Criminal behavior *reproduction* for preventive research (no future prediction) | Research PoC, academic collaboration |
| 🎓 **Academic Research** | Reproducible agent-based social simulation | Python package + web dashboard |

---

## ✨ Core Features

- **Hierarchical Memory** — short-term buffer, long-term vector store, automatic summarization
- **Relationship Graph** — agent-to-agent directed relationships with type and weight
- **Environment Model** — time, place, and conditional world state
- **Emotion (PAD)** — valence, arousal, dominance driving decisions
- **LLM Gateway** — Anthropic first, OpenAI fallback, local model (Llama/Gemma) backup
- **Godot & Unity Adapters** — drop into your game project
- **Streamlit Dashboard** — visualize simulations, inspect memories, replay runs

---

## 🚀 Quick Start

### Install
```bash
pip install -e ".[dev]"
```

### First Simulation
```python
from knoema import Simulator, Persona, Personality

alice = Persona(
    name="Alice",
    age=17,
    background="introverted literature student, night owl",
    personality=Personality(openness=0.8, extraversion=0.2, ...),
    values=["honesty", "solitude"],
    goals=["finish novel"],
)

bob = Persona(
    name="Bob",
    age=17,
    background="extroverted science student, early bird",
    personality=Personality(openness=0.6, extraversion=0.9, ...),
    values=["curiosity", "social"],
    goals=["top grade in physics"],
)

sim = Simulator(agents=[alice, bob], environment=seoul_dormitory)
sim.run(duration_days=7)
sim.export_logs("runs/dorm_001.jsonl")
```

### Example Notebooks
- [`examples/01_two_agents_dorm.ipynb`](examples/01_two_agents_dorm.ipynb) — two high-schoolers in a dorm, 7 days
- [`examples/02_crime_scenario_replay.ipynb`](examples/02_crime_scenario_replay.ipynb) — fictional case reproduction (anonymized)
- [`examples/03_game_npc_demo.ipynb`](examples/03_game_npc_demo.ipynb) — KNOT-style NPC with persistent memory

### Godot Integration
See [`adapters/godot/README.md`](adapters/godot/README.md) for the plugin and a playable demo scene.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│              Knoema Engine Core (Python)             │
│  ┌────────────────────────────────────────────────┐  │
│  │  Persona      Memory       Relationship        │  │
│  │  Environment  Emotion      Decision Engine     │  │
│  └────────────────────────────────────────────────┘  │
│              ▼           ▼           ▼               │
│     [LLM Gateway: Anthropic · OpenAI · Local]        │
└──────────────────────────────────────────────────────┘
         │              │               │
         ▼              ▼               ▼
    [Adapter: Games]  [Adapter: Safety]  [Adapter: Research]
```

Full design notes in [`docs/architecture.md`](docs/architecture.md).

---

## 📚 Related Work

- Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" (Stanford, 2023) — arXiv:2304.03442
- DeepMind, "Concordia" (2024) — open-source LLM agent research framework
- Microsoft, "AutoGen" — multi-agent conversation framework
- Mesa, AnyLogic — classical agent-based modeling (non-LLM)

Knoema's differentiator: unified engine spanning games, safety research, and academic simulation with Korean-first language support and a dual-licensing model (open MIT core + commercial SDK).

---

## 📈 Roadmap

| Version | Target | Milestones |
|---------|--------|-----------|
| **v0.1** | 2026 Q2 (current) | Core engine prototype, 3 sample notebooks, Godot stub |
| v0.5 | 2027 Q2 | Production adapters, SaaS beta, first academic paper |
| v1.0 | 2027 Q4 | Steam-released game using the engine, paid SaaS GA, overseas pilot contracts |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Pull requests, issues, and discussions welcome.

---

## 📜 License

MIT © 2026 Celovin. See [LICENSE](LICENSE).

*Knoema Engine is being developed as part of a Korean government R&D project (중소벤처기업부 창업성장기술개발사업 디딤돌 글로벌 R&D, 2026–2027).*
