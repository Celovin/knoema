# Knoema Engine

> 게임, 공공안전 연구, 학술 시뮬레이션을 위한 LLM 기반 다중 에이전트 사회 시뮬레이션 엔진.

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

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
- 단기기억 버퍼와 SQLite + FAISS 장기기억 검색
- 신뢰, 친숙도, 상호작용 가중치를 가진 방향성 관계 그래프
- 시간, 장소, 조건, 최근 이벤트를 포함한 환경 맥락
- PAD 감정 상태: valence, arousal, dominance
- Anthropic, OpenAI, deterministic local client를 묶는 LLM gateway
- scheduled event와 JSONL export를 지원하는 simulation runner
- MVP 데모 트랙과 10명 마을 확장 실험을 보여주는 Jupyter 노트북
- Godot 4 어댑터 스캐폴드
- 시뮬레이션 로그를 확인하는 Streamlit 대시보드

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

## Godot 연동

Godot 4 스캐폴드, HTTP/local fallback client, 데모 씬 구조는 [adapters/godot/README.md](adapters/godot/README.md)를 참고하세요.

## 문서

- [Architecture](docs/architecture.md)
- [Research Positioning](docs/research.md)
- [기술 리포트 LaTeX 초안](paper/main.tex), [PDF 프리뷰](paper/knoema_technical_report.pdf)

## 개발

```bash
pytest
ruff check .
mypy src
```

## 릴리스 준비

로컬 패키지 빌드와 Docker 릴리스 검증 절차는 [RELEASE.md](RELEASE.md)에 정리되어 있습니다. 태그 기반 GitHub Release workflow는 포함되어 있지만, PyPI 업로드는 별도 승인 단계로 남겨두었습니다.

## 라이선스

MIT License. Copyright (c) 2026 Celovin.
