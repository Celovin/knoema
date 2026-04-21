# Knoema Engine

> Moteur de simulation sociale multi-agents piloté par LLM pour les jeux, la recherche en sécurité publique et la simulation académique.

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/celovin/knoema-playground)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19643409.svg)](https://doi.org/10.5281/zenodo.19643409)

## Current version

0.2.0

## Knoema Bench

Knoema Bench is the seven-axis public leaderboard for persistent-agent frameworks. Live page: [https://celovin.github.io/knoema/bench/](https://celovin.github.io/knoema/bench/). Submission template: [bench/submissions/TEMPLATE.yaml](bench/submissions/TEMPLATE.yaml).

## Langues

| English | 한국어 | 日本語 | 简体中文 | 繁體中文 | Deutsch | Français | Español |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md) |

Knoema Engine est un MVP précoce pour modéliser des agents persistants dotés de mémoire, de relations, d'émotions, de contexte environnemental et de décisions pilotées par LLM. Le même runtime prend en charge les NPC de jeu, la recherche fictive de replay en sécurité publique et la simulation sociale reproductible.

Tous les exemples liés à la sécurité publique dans ce dépôt sont fictifs, synthétiques et non identifiants. Le projet n'est pas un outil de prédiction criminelle, de scoring de suspects ou d'automatisation décisionnelle opérationnelle.

## Cas d'usage

| Domaine | Usage | Surface MVP actuelle |
| --- | --- | --- |
| Jeux | NPC à mémoire persistante et dialogue dynamique | Adaptateur Godot et notebook NPC |
| Recherche sécurité publique | Relecture de scénarios fictifs pour la prévention | Notebook de replay synthétique |
| Recherche académique | Expériences reproductibles avec agents LLM | Package Python, notebooks, tableau de bord Streamlit |

## Capacités clés

- Personas avec traits Big Five, valeurs et objectifs
- Mémoire long terme SQLite + FAISS avec reranking semantic-temporal
- Graphe de relations avec confiance et familiarité
- État émotionnel PAD et contexte d'événements environnementaux
- LLM gateway pour Anthropic, OpenAI et clients locaux déterministes
- Scenario DSL v1 en YAML avec garde-fous éthiques
- Moteur de simulation, CLI et tableau de bord avec export JSONL
- Playground, benchmarks, SDK de jeu et rapports de recherche
- 1K city-scale benchmark, offline msgpack replay viewer, and pedagogical archetype overlays

## Démarrage rapide

```bash
pip install -e ".[dev]"
```

Lancer une simulation YAML locale :

```bash
knoema run examples/cli_dorm.yaml --json
```

Lancer le Playground en local :

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

Démarrer le tableau de bord :

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

## Liens essentiels

- [Knoema Playground](https://huggingface.co/spaces/celovin/knoema-playground)
- [Scenario Marketplace Beta](scenarios_hub/README.md)
- [DSL Tutorial](docs/dsl/tutorial.md)
- [Game SDK Docs](docs/sdk/python-api.md)
- [Research Positioning](docs/research.md)
- [Security Policy](docs/SECURITY.md)

Pour la documentation technique complète, l'architecture, les benchmarks, les SDK et les documents de recherche, consultez le [English README](README.md).

## Développement

```bash
pytest
ruff check .
mypy src
```

## Licence

MIT License. Copyright (c) 2026 Celovin.
