# 본문1-구현 서브태스크 상세 매핑

목적: `planning/본문1_연구개발계획서_초안.md`의 핵심 문장을 저장소 산출물, 서브태스크, 검증 파일로 1:1에 가깝게 연결해 평가자 질의응답에 바로 쓰기 위한 운영 메모다.

## 핵심 매핑

| 계획서 섹션 | 라인 | 인용 발췌(50자 내외) | 연결 주장 | 대응 Sub-task | 저장소 근거 | 검증 파일 / 테스트 |
| --- | --- | --- | --- | --- | --- | --- |
| §① 과제 개요 | 22-23 | "게임 NPC...범죄...학술연구 SaaS" | 3대 도메인 엔진 실증 | 24, 31, 35, 38, 47, 58 | `playground/app.py`, `adapters/godot/`, `adapters/unity/`, `docs/research/` | `tests/test_playground_game_actions.py`, `tests/test_playground_preregistration.py`, `tests/test_phase47_unreal_adapter.py`, `tests/test_playground_simulation_template.py` |
| §3.1 개발 배경 | 49-51 | "상용 미들웨어는 공백" | 오픈 런타임 + 비교 포지셔닝 | 29, 57 | `docs/competitor_matrix.md`, `benchmarks/cross_framework/`, `playground/app.py` | `tests/test_phase17_competitor_matrix.py`, `tests/test_phase57_cross_framework.py`, `tests/test_playground_competitive_comparison.py` |
| §3.2 최종 목표 | 54-60 | "Godot/Unity 플러그인 + Python SDK + 웹 대시보드" | 게임/SDK/대시보드 동시 제공 | 24, 31, 33, 34, 47, 48 | `sdk/`, `adapters/godot/`, `adapters/unity/`, `playground/app.py` | `tests/test_phase24_game_sdk.py`, `tests/test_phase34_game_demos.py`, `tests/test_playground_player_mode.py` |
| §3.2 정량 지표 | 58-60 | "맥락정합도...재현 정합도...레이턴시" | 정량 KPI를 로컬 산출물로 추적 | 43, 44, 45, 54, 56, 59 | `benchmarks/memory_benchmark_integration/results/summary.json`, `experiments/theory_of_mind_ablation/results/summary.json`, `experiments/planning_depth/results/summary.json`, `benchmarks/formal_report/results/latency_comparison.json`, `experiments/mlmf_retention_benchmark/results/summary.json` | `tests/test_phase54_memory_benchmark_integration.py`, `tests/test_phase44_tier_ablation.py`, `tests/test_phase45_htn_depth_scaling.py`, `tests/test_phase56_latency_comparison.py`, `tests/test_phase59_mlmf.py` |
| §4.1 전체 아키텍처 | 79-87 | "Memory Module...Relationship DB...LLM Gateway" | 코어 런타임 5계층 + 게이트웨이 | 1, 2, 4, 17, 19, 30, 55, 59 | `src/knoema/types.py`, `src/knoema/memory/`, `src/knoema/relationship.py`, `src/knoema/llm/gateway.py`, `src/knoema/planning/hierarchical.py` | `tests/test_phase1_types.py`, `tests/test_phase2_memory.py`, `tests/test_phase17_monologue.py`, `tests/test_phase30_arxiv_paper.py`, `tests/test_phase59_mlmf.py` |
| §4.2 Phase 1 | 98-100 | "계층적 메모리...SQLite+FAISS" | 다층 메모리 + 검색형 장기기억 | 2, 43, 54, 55, 59 | `src/knoema/memory/long_term.py`, `src/knoema/memory/external_benchmark_integration.py`, `src/knoema/memory/multi_layer.py` | `tests/test_phase2_memory.py`, `tests/test_phase43_memory_retrieval_benchmark.py`, `tests/test_phase54_memory_benchmark_integration.py`, `tests/test_phase59_mlmf.py` |
| §4.2 Phase 2 | 103-107 | "Godot 4.x...Crime Sim...Jupyter/Web SaaS" | 3개 어댑터와 연구 패키징 | 32, 34, 35, 37, 47, 48, 51 | `adapters/godot/`, `adapters/unity/`, `playground/app.py`, `docs/research/papers_with_code_submission.md` | `tests/test_phase34_game_demos.py`, `tests/test_playground_routines.py`, `tests/test_playground_replication_package.py`, `tests/test_playground_zenodo_deposit.py` |
| §4.2 Phase 3 | 109-113 | "Steam 출시, KCI 논문, SaaS 파일럿 3곳" | 배포/실증/아카이브 준비 | 35, 50, 51, 62 | `paper/main.tex`, `paper/abstract.txt`, `docs/research/academic-indexing.md`, `scripts/pre_release_check.py` | `tests/test_phase31_academic_indexing.py`, `tests/test_phase50_arxiv_packet.py`, `tests/test_arxiv_metadata_readiness.py`, `tests/test_pre_release_check.py` |
| §4.3 기술 차별성 | 120-125 | "O (Godot/Unity)...로그·DSL 표준" | 엔진 통합 + 재현성 + 이중 라이선스 | 22, 24, 47, 57 | `adapters/`, `docs/competitor_matrix.md`, `README.md`, `paper/sections/04_experiments.tex` | `tests/test_phase22_dsl.py`, `tests/test_phase24_game_sdk.py`, `tests/test_phase47_unreal_adapter.py`, `tests/test_phase57_cross_framework.py` |
| §4.4 위험 대응 | 131-136 | "로컬 모델 폴백...IRB...콘텐츠 필터링" | 로컬 LLM 폴백 + 안전 게이트 | 36, 39, 53, 60 | `src/knoema/llm/local/`, `playground/app.py`, `src/knoema/safety/content_filter.py` | `tests/test_phase36_local_llm.py`, `tests/test_playground_advanced_research_gate.py`, `tests/red_team/test_harmful_content.py`, `tests/test_phase60_honesty_humility_caveat.py` |
| §4.5 결과 검증 | 138-144 | "정량 검증...학술 검증...공개 검증" | 테스트·보고서·재현 패키지 삼각 검증 | 27, 35, 37, 40, 50, 51 | `benchmarks/formal_report/results/summary.md`, `docs/research/proposal_mapping.md`, `playground/app.py`, `scripts/verify_replication.py` | `tests/test_phase20_formal_benchmark.py`, `tests/test_phase40_proposal_mapping.py`, `tests/test_playground_replication_package.py`, `tests/test_verify_replication.py` |
| §5.1 선행개발 | 154-158 | "v0.1.0 공개 프로토타입...pytest 76개" | 공개 프로토타입과 품질 게이트 이력 | 13, 35, 62 | `README.md`, `.github/workflows/ci.yml`, `scripts/pre_release_check.py` | `tests/test_phase13_release.py`, `tests/test_phase35_ci_release.py`, `tests/test_phase62_release.py` |
| §5.2 활용계획 | 176-183 | "Godot 4.x 어댑터 스텁...방법론 확장" | 게임/범죄학/평가 프레임워크 확장 | 34, 40, 43, 44 | `adapters/godot/`, `docs/research/proposal_mapping.md`, `src/knoema/theory_of_mind.py` | `tests/test_phase34_game_demos.py`, `tests/test_phase40_proposal_mapping.py`, `tests/test_phase43_theory_of_mind.py`, `tests/test_phase44_tier_ablation.py` |
| §6.1 연구팀 역량 | 203-219 | "LLM Gateway·장기기억·Godot/Unity" | 주관/위탁 역할 분리와 구현 범위 | 30, 32, 47, 48, 56 | `src/knoema/llm/gateway.py`, `src/knoema/memory/`, `adapters/unity/`, `playground/voice.py`, `benchmarks/formal_report/results/latency_comparison.json` | `tests/test_playground_player_mode.py`, `tests/test_phase47_unreal_adapter.py`, `tests/test_phase56_latency_comparison.py` |
| §7.2 연차별 산출물 | 265-267 | "v0.1...v0.5...v1.0" | 단계별 릴리스 패키징 | 13, 35, 37, 50, 62 | `CHANGELOG.md`, `paper/`, `docs/research/papers_with_code_submission.md`, `scripts/pre_release_check.py` | `tests/test_phase13_release.py`, `tests/test_phase35_ci_release.py`, `tests/test_phase50_arxiv_packet.py`, `tests/test_phase62_release.py` |
| §9.1 제품 포트폴리오 | 324-328 | "KNOT...SaaS...SDK...Core" | 게임/연구/SDK/오픈소스 수익 분기 | 24, 31, 34, 47, 51 | `sdk/`, `adapters/`, `paper/main.tex`, `README.md` | `tests/test_phase24_game_sdk.py`, `tests/test_phase34_game_demos.py`, `tests/test_phase31_academic_indexing.py` |
| §9.2-9.4 사업화/시장/효과 | 337-371 | "B2C...B2B...B2G / 해외 1곳" | 사업화 근거는 코드+문서+배포로만 제한 | 25, 29, 35, 57, 62 | `website/`, `docs/competitor_matrix.md`, `docs/research/academic-indexing.md`, `benchmarks/` | `tests/test_phase25_website.py`, `tests/test_phase17_competitor_matrix.py`, `tests/test_phase31_academic_indexing.py`, `tests/test_phase57_cross_framework.py` |

## 벤치마크 caveat 교차표

| 항목 | 측정값 | caveat 라벨 | 근거 파일 | 검증 |
| --- | --- | --- | --- | --- |
| LoCoMo / MemoryAgentBench / MemoryArena | 각 `score=1.000` | `synthetic local proxy` | `benchmarks/memory_benchmark_integration/results/summary.json` | `tests/test_phase54_memory_benchmark_integration.py` |
| MLMF 4-layer retention | `measured_retention=0.875` vs `published_baseline=0.569` | `deterministic local measurement` | `experiments/mlmf_retention_benchmark/results/summary.json` | `tests/test_phase59_mlmf.py` |
| ToM Sally-Anne | `baseline_accuracy=1.000` | `deterministic local measurement` | `experiments/theory_of_mind_ablation/results/summary.json` | `tests/test_phase44_tier_ablation.py`, `tests/test_phase43_theory_of_mind.py` |
| HTN scaling | depth-5 `0.955` vs planning-off `0.565` | `deterministic local measurement` | `experiments/planning_depth/results/summary.json` | `tests/test_phase45_htn_depth_scaling.py` |
| ACE / Inworld latency | ACE `198-200 ms`, Inworld `130-250 ms`, `1000-3000 ms` | `published reference (not measured)` | `benchmarks/formal_report/results/latency_comparison.json` | `tests/test_phase56_latency_comparison.py` |

## 메모

- 외부 파트너십, 해외 파일럿 계약, 특허 출원 등은 저장소만으로 완료 여부를 단정할 수 없으므로 여기서는 "준비 산출물"까지만 연결했다.
- 발표 시에는 `synthetic local proxy`, `deterministic local measurement`, `published reference (not measured)` 세 문구를 그대로 읽어 과장 해석을 피한다.
