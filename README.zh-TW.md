# Knoema Engine

> 面向遊戲、公共安全研究與學術模擬的 LLM 多代理社會模擬引擎。

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/celovin/knoema-playground)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19643409.svg)](https://doi.org/10.5281/zenodo.19643409)

## Current version

0.2.0

## Knoema Bench

Knoema Bench 是面向持久型代理框架的七軸公開排行榜。線上頁面：[https://celovin.github.io/knoema/bench/](https://celovin.github.io/knoema/bench/)。提交範本：[bench/submissions/TEMPLATE.yaml](bench/submissions/TEMPLATE.yaml)。

- Unity SDK（預覽）提供 FastAPI tick、memory、action 合約與 UPM 套件結構。
- 可選 OpenAI TTS 語音播放支援 Playground 時間軸中的 `speak` 動作，包含每個代理的聲音與基於快取的 WAV fallback。

## 語言

| English | 한국어 | 日本語 | 简体中文 | 繁體中文 | Deutsch | Français | Español |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md) |

Knoema Engine 是一個早期 MVP，用來建模具備記憶、關係、情緒、環境脈絡與 LLM 驅動決策的持續型代理。它可以在同一套執行時中支援遊戲 NPC、虛構公共安全回放研究，以及可重現的社會模擬。

本儲存庫中的公共安全範例皆為虛構、合成且不可識別的資料。它不是犯罪預測、嫌疑人評分或真實執法自動化工具。

## 主要用途

| 領域 | 用途 | 目前 MVP 介面 |
| --- | --- | --- |
| 遊戲 | 具長期記憶的 NPC 與動態對話 | Godot 介接器與 NPC 筆記本 |
| 公共安全研究 | 用於預防研究的虛構情境回放 | 合成回放筆記本 |
| 學術研究 | 可重現的 LLM 代理實驗 | Python 套件、筆記本、Streamlit 儀表板 |

## 核心能力

- 具備 Big Five 特質、價值觀與目標的 Persona
- 以 SQLite + FAISS 為基礎的長期記憶檢索與 semantic-temporal 重排序
- 含信任與熟悉度的關係圖
- PAD 情緒狀態與環境事件脈絡
- 整合 Anthropic、OpenAI 與本地決定論客戶端的 LLM gateway
- 帶有倫理護欄的 YAML Scenario DSL v1
- 支援 JSONL 匯出的模擬執行器、CLI 與儀表板
- Playground、基準測試、遊戲 SDK 與研究報告
- 城市規模 1K 基準、離線 msgpack replay 檢視器，以及 CAT-28 五級人格檔案的教學 overlay
- 面向本機 10K 江南 replay 的可選 Nemotron-Personas-Korea 人設種子

## 快速開始

```bash
pip install -e ".[dev]"
```

執行本機 YAML 模擬：

```bash
knoema run examples/cli_dorm.yaml --json
```

在本機啟動 Playground：

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

啟動儀表板：

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

## 重要連結

- [Knoema Playground](https://huggingface.co/spaces/celovin/knoema-playground)
- [Scenario Marketplace Beta](scenarios_hub/README.md)
- [DSL Tutorial](docs/dsl/tutorial.md)
- [Game SDK Docs](docs/sdk/python-api.md)
- [Research Positioning](docs/research.md)
- [Security Policy](docs/SECURITY.md)

更完整的技術說明、架構、基準、SDK 與論文資料請參閱 [English README](README.md)。

## 開發

```bash
pytest
ruff check .
mypy src
```

## 授權

MIT License. Copyright (c) 2026 Celovin.
