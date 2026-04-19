# Knoema Engine

> 게임, 공공안전 연구, 학술 시뮬레이션을 위한 LLM 기반 다중 에이전트 사회 시뮬레이션 엔진.

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/celovin/knoema-playground)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19643409.svg)](https://doi.org/10.5281/zenodo.19643409)

## Current version

0.2.0

## 언어

| English | 한국어 | 日本語 | 简体中文 | 繁體中文 | Deutsch | Français | Español |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md) |

Knoema Engine은 기억, 관계, 감정, 환경 맥락, LLM 기반 의사결정을 가진 지속형 에이전트를 모델링하는 초기 MVP입니다. 하나의 런타임으로 게임 NPC, 완전 가상 공공안전 리플레이 연구, 재현 가능한 에이전트 기반 사회 시뮬레이션을 지원합니다.

이 저장소의 공공안전 예제는 모두 가상, 합성, 비식별 데이터입니다. 범죄 예측, 용의자 점수화, 실무 판단 자동화 도구가 아닙니다.

## 적용 영역

| 영역 | 용도 | 현재 MVP |
| --- | --- | --- |
| 게임 | 장기기억 NPC와 동적 대화 | Godot 어댑터 스캐폴드, NPC 노트북 |
| 공공안전 연구 | 예방 연구용 가상 시나리오 리플레이 | 합성 리플레이 노트북, milestone coverage |
| 학술 연구 | 재현 가능한 LLM 에이전트 시뮬레이션 | Python 패키지, 노트북, Streamlit 대시보드 |

## 핵심 기능

- Big Five 성격, 가치, 목표를 가진 Persona
- Semantic-temporal 재랭킹을 포함한 단기기억 버퍼와 SQLite + FAISS 장기기억 검색
- 신뢰, 친숙도, 상호작용 가중치를 가진 방향성 관계 그래프
- 시간, 장소, 조건, 최근 이벤트를 포함한 환경 맥락
- PAD 감정 상태: valence, arousal, dominance
- Anthropic, OpenAI, deterministic local client를 묶는 LLM gateway
- 영어, 한국어, 일본어, 중국어 실행을 위한 prompt template
- scheduled event와 JSONL export를 지원하는 simulation runner
- YAML 기반 로컬 시뮬레이션을 실행하는 `knoema run` CLI
- MVP 데모 트랙과 10명 마을 확장 실험을 보여주는 Jupyter 노트북
- JSON과 Markdown 리포트를 생성하는 deterministic benchmark script
- Godot 4 어댑터 스캐폴드
- Python, TypeScript, GDScript Game SDK facade
- Playback과 live-tail control을 포함한 Streamlit 시뮬레이션 로그 대시보드

## 설치

```bash
pip install -e ".[dev]"
```

대시보드 의존성은 선택 설치입니다.

```bash
pip install -e ".[dashboard]"
```

## 예제

- [2인 기숙사 시뮬레이션](examples/01_two_agents_dorm.ipynb)
- [가상 범죄 시나리오 리플레이](examples/02_crime_scenario_replay.ipynb)
- [게임 NPC 지속 기억 데모](examples/03_game_npc_demo.ipynb)
- [10명 마을 시뮬레이션](examples/04_village.ipynb)

## 대시보드

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

## Research SaaS

```bash
pip install -r saas/requirements.txt
streamlit run saas/app.py
```

Research dashboard는 simulation run, A/B comparison, memory inspection, relationship exploration, cost budget, citation export 6개 page를 제공합니다.

브라우저에서 `http://localhost:8501`을 열고 `Simulator.export_logs(...)`가 만든 JSONL 로그를 불러오면 됩니다. 샘플 로그도 포함되어 있습니다.

## 벤치마크

```bash
python benchmarks/run_benchmark.py --json-output runs/benchmark.json --markdown-output runs/benchmark.md
```

Phase 19 50명 마을 실험:

```bash
python experiments/50_agent_village/run.py
```

자세한 내용은 [50-Agent Village Experiment](experiments/50_agent_village/README.md)와 [50-Agent Benchmark Report](docs/reports/50_agent_benchmark.pdf)를 참고하세요.

Formal report bundle:

```bash
python benchmarks/formal_report/runner.py
```

## Reproducibility Guarantees

Knoema deterministic local run은 fixed config, seed, JSONL artifact로 replay할 수 있습니다. Phase 21 테스트는 same-seed 반복 실행, seed propagation, YAML config round-trip, JSONL replay summary를 검증합니다.

자세한 내용은 [Reproducibility Report](docs/reports/reproducibility.md)를 참고하세요.

자세한 내용은 [Formal Benchmark Report](benchmarks/formal_report/README.md)와 [Formal Report PDF](benchmarks/formal_report/report.pdf)를 참고하세요.

벤치마크 리포트는 Knoema 처리량을 실제 측정하고, Concordia와 Mesa는 별도 외부 실행이 필요하다는 `not-measured` 비교 슬롯으로 표시합니다. 자세한 기준은 [benchmarks/README.md](benchmarks/README.md)에 정리했습니다.

## 메모리 검색

`SQLiteFaissMemoryStore.retrieve(...)`는 단순한 memory list API를 유지합니다. 분석용 점수가 필요하면 `retrieve_with_scores(...)`로 semantic score, temporal score, importance score, final reranking score를 함께 확인할 수 있습니다.

```python
from knoema import RetrievalWeights

results = store.retrieve_with_scores(
    'shared study routine',
    k=5,
    weights=RetrievalWeights(semantic=0.65, temporal=0.30, importance=0.05),
)
```

## CLI

```bash
knoema run examples/cli_dorm.yaml --json
```

## Scenario DSL

```python
from knoema.dsl import load_scenario

scenario = load_scenario('examples/scenarios/01_shopkeeper_winter_crime.yaml')
logs = scenario.to_simulator().run(duration_days=scenario.duration_days)
```

자세한 내용은 [DSL Tutorial](docs/dsl/tutorial.md), [DSL Reference](docs/dsl/reference.md), [Scenario JSON Schema](schemas/scenario_v1.json)를 참고하세요.

YAML 설정 형식, 출력 경로 규칙, dry-run 검증은 [CLI](docs/cli.md)를 참고하세요.

## Game SDK

Knoema는 설치형 Python 패키지, TypeScript 도구, Godot GDScript 프로토타입에서 사용할 수 있는 deterministic NPC SDK facade를 제공합니다.

```python
from knoema.game import GameSession

session = GameSession(game_id='demo-village')
npc = session.create_npc(
    persona_file='sdk/python/examples/personas/shopkeeper.yaml',
    initial_relationships={'player': 'neighbor'},
)
response = npc.interact('asks about the lantern market', context={'location': 'Harbor Village'})
print(response.text)
```

- [Python Game SDK](docs/sdk/python-api.md)
- [TypeScript Game SDK](docs/sdk/typescript-api.md)
- [Godot GDScript Game SDK](docs/sdk/godot-api.md)
- [Game SDK Integration Patterns](docs/sdk/integration_patterns.md)

## Godot 연동

Godot 4 스캐폴드, HTTP/local fallback client, 데모 씬 구조는 [adapters/godot/README.md](adapters/godot/README.md)를 참고하세요.

## Unity 연동

Unity Package Manager에서 다음 Git URL로 설치할 수 있습니다.

```text
https://github.com/Celovin/knoema.git?path=adapters/unity
```

Unity 2022.3 LTS 패키지 스캐폴드, HTTP/local fallback client, `NPCAgent` 컴포넌트, Basic NPC 샘플은 [adapters/unity/README.md](adapters/unity/README.md)를 참고하세요.

## 문서

- [Architecture](docs/architecture.md)
- [Research Positioning](docs/research.md)
- [Competitor Matrix](docs/competitor_matrix.md)
- [50-Agent Village Experiment](experiments/50_agent_village/README.md)
- [50-Agent Benchmark Report](docs/reports/50_agent_benchmark.pdf)
- [Formal Benchmark Report](benchmarks/formal_report/README.md)
- [Formal Report PDF](benchmarks/formal_report/report.pdf)
- [Reproducibility Report](docs/reports/reproducibility.md)
- [DSL Tutorial](docs/dsl/tutorial.md)
- [DSL Reference](docs/dsl/reference.md)
- [Python Game SDK](docs/sdk/python-api.md)
- [TypeScript Game SDK](docs/sdk/typescript-api.md)
- [Godot GDScript Game SDK](docs/sdk/godot-api.md)
- [Game SDK Integration Patterns](docs/sdk/integration_patterns.md)
- [Research SaaS App](saas/app.py)
- [CLI](docs/cli.md)
- [Prompt Templates](docs/prompts.md)
- [튜토리얼 블로그 초안](docs/tutorial_blog.md)
- [한국어 기술 블로그 초안](docs/blog/ko/01-why-knoema-korean-indie-games.md)
- [Discord 커뮤니티 런치 키트](docs/discord_community.md)
- [Demo Video Scripts](docs/videos/shotlist.md)
- [YouTube 튜토리얼 스크립트](docs/videos/tutorials/01_getting_started_10min.md)
- [Website App](website/app/page.tsx)
- [기술 리포트 LaTeX 초안](paper/main.tex), [PDF 프리뷰](paper/knoema_technical_report.pdf)
- [Papers with Code 제출 패킷](docs/research/papers_with_code_submission.md), [JSON 패킷](docs/research/papers_with_code_submission.json)

## 개발

```bash
pytest
ruff check .
mypy src
```

## 릴리스 준비

로컬 패키지 빌드와 Docker 릴리스 검증 절차는 [RELEASE.md](RELEASE.md)에 정리되어 있습니다. 태그 기반 GitHub Release workflow는 포함되어 있지만, PyPI 업로드는 별도 승인 단계로 남겨두었습니다.

## Playground

[Knoema Playground](https://huggingface.co/spaces/celovin/knoema-playground)에서 브라우저 기반 데모를 실행할 수 있습니다. API 키가 없는 사용자는 replay-only 모드로 3개 기본 시나리오를 확인할 수 있고, OpenAI 또는 Anthropic 키를 입력하면 현재 세션에서만 live LLM 실행을 사용할 수 있습니다.

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

## Website

```bash
cd website
npm install
npm run build
npm run dev
```

Next.js 기반 공식 프로젝트 페이지입니다. 적용 영역, SDK 진입점, 연구 리포트, 공개 링크를 한 화면에서 확인할 수 있게 구성했습니다.

## 라이선스

MIT License. Copyright (c) 2026 Celovin.
