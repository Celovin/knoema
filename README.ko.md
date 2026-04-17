# Knoema Engine

> **실감형 콘텐츠·공공안전·학술연구를 위한 LLM 기반 다중 에이전트 사회 시뮬레이션 엔진.**

[![CI](https://github.com/Celovin/knoema/actions/workflows/ci.yml/badge.svg)](https://github.com/Celovin/knoema/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

English: [README.md](README.md)

---

## 🌐 하나의 엔진, 세 가지 응용

Knoema Engine은 지속 기억·감정·사회 관계를 가진 에이전트를 모델링하는 통합 런타임을 제공하며, 이 런타임을 세 개의 도메인에서 실증합니다.

| 도메인 | 활용 | 배포 트랙 |
|--------|-----|---------|
| 🎮 **게임** | 장기기억 기반 NPC와 동적 서사 분기 | Godot/Unity 어댑터, 상용 SDK |
| 🛡️ **공공안전** | 과거 범죄 행동 재현(PoC) 기반 예방 연구 *(미래 예측 X)* | 학술 PoC, 공동 연구 |
| 🎓 **학술 연구** | 재현 가능한 에이전트 기반 사회 시뮬레이션 | Python 패키지 + 웹 대시보드 |

---

## ✨ 핵심 기능

- **계층적 기억** — 단기 버퍼 · 장기 벡터 저장소 · 자동 요약
- **관계 그래프** — 에이전트 간 타입·가중치 기반 방향 관계
- **환경 모델** — 시공간·조건부 상태
- **감정 모델(PAD)** — Valence·Arousal·Dominance 기반 의사결정
- **LLM 게이트웨이** — Anthropic 우선, OpenAI 폴백, 로컬 모델 백업
- **Godot·Unity 어댑터** — 게임 프로젝트에 바로 통합
- **Streamlit 대시보드** — 시뮬레이션 시각화·메모리 검사·리플레이

---

## 🚀 빠른 시작

```bash
pip install -e ".[dev]"
```

예제 노트북: [`examples/01_two_agents_dorm.ipynb`](examples/01_two_agents_dorm.ipynb) · [`examples/02_crime_scenario_replay.ipynb`](examples/02_crime_scenario_replay.ipynb) · [`examples/03_game_npc_demo.ipynb`](examples/03_game_npc_demo.ipynb)

---

## 📜 라이선스

MIT © 2026 Celovin — [LICENSE](LICENSE)

*본 엔진은 중소벤처기업부 창업성장기술개발사업(디딤돌) 글로벌 R&D 과제의 일환으로 개발 중입니다 (2026~2027).*
