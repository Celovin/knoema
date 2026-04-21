# Knoema Engine

> ゲーム、公共安全研究、学術シミュレーション向けの LLM ベース多エージェント社会シミュレーションエンジン。

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/celovin/knoema-playground)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19643409.svg)](https://doi.org/10.5281/zenodo.19643409)

## Current version

0.2.0

## Knoema Bench

Knoema Bench is the seven-axis public leaderboard for persistent-agent frameworks. Live page: [https://celovin.github.io/knoema/bench/](https://celovin.github.io/knoema/bench/). Submission template: [bench/submissions/TEMPLATE.yaml](bench/submissions/TEMPLATE.yaml).

## 言語

| English | 한국어 | 日本語 | 简体中文 | 繁體中文 | Deutsch | Français | Español |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md) |

Knoema Engine は、記憶、関係、感情、環境コンテキスト、LLM ベース意思決定を持つ持続型エージェントを扱う初期 MVP です。ゲーム NPC、架空の公共安全リプレイ研究、再現可能なエージェントベース社会シミュレーションを同じランタイムで支えます。

このリポジトリの公共安全サンプルはすべて架空・合成・非識別です。犯罪予測、容疑者スコアリング、実務判断の自動化を目的としたものではありません。

## 主な用途

| 分野 | 用途 | 現在の MVP |
| --- | --- | --- |
| ゲーム | 長期記憶 NPC と動的対話 | Godot アダプタ、NPC ノートブック |
| 公共安全研究 | 予防研究向けの架空シナリオ再生 | 合成リプレイノートブック |
| 学術研究 | 再現可能な LLM エージェント実験 | Python パッケージ、ノートブック、Streamlit ダッシュボード |

## コア機能

- Big Five 特性、価値観、目標を持つ Persona
- SQLite + FAISS による長期記憶検索と semantic-temporal 再ランキング
- 信頼度と親密度を持つ関係グラフ
- PAD 感情状態と環境イベントコンテキスト
- Anthropic、OpenAI、ローカル決定論クライアントを束ねる LLM gateway
- YAML ベースの Scenario DSL v1 と倫理ガードレール
- JSONL エクスポート付きシミュレーションランナー、CLI、ダッシュボード
- Playground、ベンチマーク、ゲーム SDK、研究用レポート
- 1K city-scale benchmark, offline msgpack replay viewer, and pedagogical archetype overlays

## クイックスタート

```bash
pip install -e ".[dev]"
```

ローカル YAML シミュレーション:

```bash
knoema run examples/cli_dorm.yaml --json
```

Playground をローカル起動:

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

ダッシュボード起動:

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

## 主要リンク

- [Knoema Playground](https://huggingface.co/spaces/celovin/knoema-playground)
- [Scenario Marketplace Beta](scenarios_hub/README.md)
- [DSL Tutorial](docs/dsl/tutorial.md)
- [Game SDK Docs](docs/sdk/python-api.md)
- [Research Positioning](docs/research.md)
- [Security Policy](docs/SECURITY.md)

完全な技術説明、アーキテクチャ、ベンチマーク、SDK、論文資料は [English README](README.md) を参照してください。

## 開発

```bash
pytest
ruff check .
mypy src
```

## ライセンス

MIT License. Copyright (c) 2026 Celovin.
