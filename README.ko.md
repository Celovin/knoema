# Knoema Engine

> 게임, 공공안전 연구, 학술 시뮬레이션을 위한 LLM 기반 다중 에이전트 사회 시뮬레이션 엔진.

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Celovin/knoema-playground)

English: [README.md](README.md)

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

브라우저에서 `http://localhost:8501`을 열고 `Simulator.export_logs(...)`가 만든 JSONL 로그를 불러오면 됩니다. 샘플 로그도 포함되어 있습니다.

## 벤치마크

```bash
python benchmarks/run_benchmark.py --json-output runs/benchmark.json --markdown-output runs/benchmark.md
```

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

YAML 설정 형식, 출력 경로 규칙, dry-run 검증은 [CLI](docs/cli.md)를 참고하세요.

## Godot 연동

Godot 4 스캐폴드, HTTP/local fallback client, 데모 씬 구조는 [adapters/godot/README.md](adapters/godot/README.md)를 참고하세요.

## 문서

- [Architecture](docs/architecture.md)
- [Research Positioning](docs/research.md)
- [CLI](docs/cli.md)
- [Prompt Templates](docs/prompts.md)
- [튜토리얼 블로그 초안](docs/tutorial_blog.md)
- [Discord 커뮤니티 런치 키트](docs/discord_community.md)
- [기술 리포트 LaTeX 초안](paper/main.tex), [PDF 프리뷰](paper/knoema_technical_report.pdf)

## 개발

```bash
pytest
ruff check .
mypy src
```

## 릴리스 준비

로컬 패키지 빌드와 Docker 릴리스 검증 절차는 [RELEASE.md](RELEASE.md)에 정리되어 있습니다. 태그 기반 GitHub Release workflow는 포함되어 있지만, PyPI 업로드는 별도 승인 단계로 남겨두었습니다.

## Playground

[Knoema Playground](https://huggingface.co/spaces/Celovin/knoema-playground)에서 브라우저 기반 데모를 실행할 수 있습니다. API 키가 없는 사용자는 replay-only 모드로 3개 기본 시나리오를 확인할 수 있고, OpenAI 또는 Anthropic 키를 입력하면 현재 세션에서만 live LLM 실행을 사용할 수 있습니다.

```bash
pip install -r playground/requirements.txt
python playground/app.py
```

## 라이선스

MIT License. Copyright (c) 2026 Celovin.
