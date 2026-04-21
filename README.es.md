# Knoema Engine

> Motor de simulación social multiagente basado en LLM para juegos, investigación de seguridad pública y simulación académica.

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/celovin/knoema-playground)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19643409.svg)](https://doi.org/10.5281/zenodo.19643409)

## Current version

0.2.0

## Knoema Bench

Knoema Bench is the seven-axis public leaderboard for persistent-agent frameworks. Live page: [https://celovin.github.io/knoema/bench/](https://celovin.github.io/knoema/bench/). Submission template: [bench/submissions/TEMPLATE.yaml](bench/submissions/TEMPLATE.yaml).

## Idiomas

| English | 한국어 | 日本語 | 简体中文 | 繁體中文 | Deutsch | Français | Español |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md) |

Knoema Engine es un MVP temprano para modelar agentes persistentes con memoria, relaciones, emociones, contexto ambiental y decisiones guiadas por LLM. El mismo runtime puede servir para NPC de juegos, investigación ficticia de replay en seguridad pública y simulación social reproducible.

Todos los ejemplos de seguridad pública de este repositorio son ficticios, sintéticos y no identificables. No es una herramienta de predicción del crimen, puntuación de sospechosos ni automatización de decisiones operativas.

## Casos de uso

| Dominio | Uso | Superficie MVP actual |
| --- | --- | --- |
| Juegos | NPC con memoria persistente y diálogo dinámico | Adaptador Godot y notebook de NPC |
| Investigación en seguridad pública | Replay de escenarios ficticios para investigación preventiva | Notebook de replay sintético |
| Investigación académica | Experimentos reproducibles con agentes LLM | Paquete Python, notebooks y panel Streamlit |

## Capacidades principales

- Personas con rasgos Big Five, valores y objetivos
- Recuperación de memoria a largo plazo con SQLite + FAISS y reranking semantic-temporal
- Grafo de relaciones con confianza y familiaridad
- Estado emocional PAD y contexto de eventos del entorno
- LLM gateway para Anthropic, OpenAI y clientes locales deterministas
- Scenario DSL v1 en YAML con guardrails éticos
- Motor de simulación, CLI y panel con exportación JSONL
- Playground, benchmarks, SDK de juego e informes de investigación

## Inicio rápido

```bash
pip install -e ".[dev]"
```

Ejecutar una simulación YAML local:

```bash
knoema run examples/cli_dorm.yaml --json
```

Iniciar el Playground en local:

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

Lanzar el panel:

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

## Enlaces clave

- [Knoema Playground](https://huggingface.co/spaces/celovin/knoema-playground)
- [Scenario Marketplace Beta](scenarios_hub/README.md)
- [DSL Tutorial](docs/dsl/tutorial.md)
- [Game SDK Docs](docs/sdk/python-api.md)
- [Research Positioning](docs/research.md)
- [Security Policy](docs/SECURITY.md)

Para la descripción técnica completa, arquitectura, benchmarks, SDK y materiales de investigación, consulta el [English README](README.md).

## Desarrollo

```bash
pytest
ruff check .
mypy src
```

## Licencia

MIT License. Copyright (c) 2026 Celovin.
