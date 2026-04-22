# Knoema Engine

> LLM-basierte Multi-Agenten-Sozialsimulations-Engine für Spiele, Public-Safety-Forschung und akademische Simulation.

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/celovin/knoema-playground)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19643409.svg)](https://doi.org/10.5281/zenodo.19643409)

## Current version

0.2.0

## Knoema Bench

Knoema Bench ist die öffentliche Bestenliste mit sieben Achsen für Frameworks persistenter Agenten. Live-Seite: [https://celovin.github.io/knoema/bench/](https://celovin.github.io/knoema/bench/). Einreichungsvorlage: [bench/submissions/TEMPLATE.yaml](bench/submissions/TEMPLATE.yaml).

## Sprachen

| English | 한국어 | 日本語 | 简体中文 | 繁體中文 | Deutsch | Français | Español |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md) |

Knoema Engine ist ein frühes MVP zur Modellierung persistenter Agenten mit Gedächtnis, Beziehungen, Emotionen, Umgebungskontext und LLM-gestützten Entscheidungen. Dieselbe Laufzeit unterstützt Spiel-NPCs, fiktive Public-Safety-Replay-Forschung und reproduzierbare agentenbasierte Sozialsimulation.

Alle Public-Safety-Beispiele in diesem Repository sind fiktiv, synthetisch und nicht identifizierend. Das Projekt ist kein Werkzeug für Kriminalitätsprognosen, Verdächtigenbewertung oder automatisierte operative Entscheidungen.

## Einsatzfelder

| Bereich | Nutzung | Aktuelle MVP-Oberfläche |
| --- | --- | --- |
| Spiele | NPCs mit persistentem Gedächtnis und dynamischem Dialog | Godot-Adapter und NPC-Notebook |
| Public-Safety-Forschung | Fiktive Szenario-Replays für Präventionsforschung | Synthetisches Replay-Notebook |
| Akademische Forschung | Reproduzierbare LLM-Agentensimulation | Python-Paket, Notebooks, Streamlit-Dashboard |

## Kernfunktionen

- Personas mit Big-Five-Merkmalen, Werten und Zielen
- SQLite- + FAISS-Langzeitgedächtnis mit semantic-temporal Reranking
- Beziehungsgraph mit Vertrauen und Vertrautheit
- PAD-Emotionszustand und Umgebungsereignisse
- LLM gateway für Anthropic, OpenAI und deterministische lokale Clients
- YAML Scenario DSL v1 mit Ethik-Guardrails
- Simulationsrunner, CLI und Dashboard mit JSONL-Export
- Playground, Benchmarks, Game-SDKs und Forschungsberichte
- City-scale-1K-Benchmark, Offline-msgpack-Replay-Viewer und CAT-28-Persönlichkeitsprofile der Stufe 5 als pädagogische Overlays
- Optionale Nemotron-Personas-Korea-Seeds für das lokale 10K-Gangnam-Replay
- Unity SDK (Vorschau) mit FastAPI-Vertrag für Tick, Memory und Action sowie UPM-Paketlayout
- Optionale OpenAI TTS-Sprachwiedergabe für `speak`-Aktionen in der Playground-Zeitleiste, mit Stimmen pro Agent und cachegestütztem WAV-Fallback

## Schnellstart

```bash
pip install -e ".[dev]"
```

Lokale YAML-Simulation ausführen:

```bash
knoema run examples/cli_dorm.yaml --json
```

Playground lokal starten:

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

Dashboard starten:

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

## Wichtige Links

- [Knoema Playground](https://huggingface.co/spaces/celovin/knoema-playground)
- [Scenario Marketplace Beta](scenarios_hub/README.md)
- [DSL Tutorial](docs/dsl/tutorial.md)
- [Game SDK Docs](docs/sdk/python-api.md)
- [Unity SDK (preview)](docs/unity-sdk.md)
- [Research Positioning](docs/research.md)
- [Security Policy](docs/SECURITY.md)

Für die vollständige technische Beschreibung, Architektur, Benchmarks, SDKs und Paper-Materialien siehe das [English README](README.md).

## Entwicklung

```bash
pytest
ruff check .
mypy src
```

## Lizenz

MIT License. Copyright (c) 2026 Celovin.
