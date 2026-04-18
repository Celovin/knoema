# Knoema Engine

> 面向游戏、公共安全研究和学术仿真的 LLM 多智能体社会仿真引擎。

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Celovin/knoema-playground)

## 语言

| English | 한국어 | 日本語 | 简体中文 | 繁體中文 | Deutsch | Français | Español |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md) |

Knoema Engine 是一个早期 MVP，用于构建具备记忆、关系、情绪、环境上下文以及 LLM 驱动决策的持续型智能体。它可以在同一运行时中支持游戏 NPC、虚构公共安全回放研究，以及可复现的社会仿真。

本仓库中的公共安全示例全部为虚构、合成、不可识别的数据。它不是犯罪预测、嫌疑人评分或现实执法自动化工具。

## 主要应用

| 领域 | 用途 | 当前 MVP 形态 |
| --- | --- | --- |
| 游戏 | 具备长期记忆的 NPC 与动态对话 | Godot 适配器和 NPC 笔记本 |
| 公共安全研究 | 面向预防研究的虚构场景回放 | 合成回放笔记本 |
| 学术研究 | 可复现的 LLM 智能体实验 | Python 包、笔记本、Streamlit 仪表板 |

## 核心能力

- 具备 Big Five 特质、价值观和目标的 Persona
- 基于 SQLite + FAISS 的长期记忆检索与 semantic-temporal 重排
- 含信任和熟悉度的关系图
- PAD 情绪状态与环境事件上下文
- 同时支持 Anthropic、OpenAI 和本地确定性客户端的 LLM gateway
- 带伦理护栏的 YAML Scenario DSL v1
- 支持 JSONL 导出的仿真运行器、CLI 与仪表板
- Playground、基准测试、游戏 SDK 和研究报告

## 快速开始

```bash
pip install -e ".[dev]"
```

运行本地 YAML 仿真：

```bash
knoema run examples/cli_dorm.yaml --json
```

本地启动 Playground：

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

启动仪表板：

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

## 关键链接

- [Knoema Playground](https://huggingface.co/spaces/Celovin/knoema-playground)
- [Scenario Marketplace Beta](scenarios_hub/README.md)
- [DSL Tutorial](docs/dsl/tutorial.md)
- [Game SDK Docs](docs/sdk/python-api.md)
- [Research Positioning](docs/research.md)
- [Security Policy](docs/SECURITY.md)

更完整的技术说明、架构、基准、SDK 和论文材料请查看 [English README](README.md)。

## 开发

```bash
pytest
ruff check .
mypy src
```

## 许可证

MIT License. Copyright (c) 2026 Celovin.
