# Codex Megabatch Report

작성 시각: 2026-04-21T00:12:28.1407803+09:00

## Batch 1. 라이브 검증 자동화 + 인프라

- Commit: `a63cb74`, `cf8c35f`
- 변경 파일 수: 16
- 핵심 변경:
  - `tests/integration/test_live_space_smoke.py` 추가
  - `.github/workflows/live-space-smoke.yml` 추가
  - `scripts/check_gradio_compat.py`, `tests/test_plotly_enum_safety.py` 추가
  - memory inspector 언어 선택 정규화 보정
- 라이브 검증:
  - `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py` 통과
  - `ruff check .` 통과
  - `mypy src` 통과
  - `tests/test_playground_encoding_guard.py` 통과
  - `git push origin main` 완료
  - HF Space 업로드 및 `runtime.stage == RUNNING` 확인
  - `curl` 200 확인
  - playwright live smoke 통과
  - 스크린샷: `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260420-133103.png`
  - HF run log 마지막 50줄에서 `Traceback|Error|gradio.exceptions|TypeError|ValueError` 0건
- 못 한 부분:
  - 실패 시 자동 revert는 이번 배치 범위 밖으로 남김

## Batch 2. 그래프 v3 - Three.js force-directed

- Commit: `202ec5f`, `8bdaa12`, `a91b191`
- 변경 파일 수: 10
- 핵심 변경:
  - `playground/static/force_graph.html` 기반 3D force-directed graph 전환
  - `playground/app.py`에서 iframe 기반 관계 그래프 렌더링
  - force graph smoke/runtime 하드닝
- 라이브 검증:
  - 공통 게이트 전체 통과
  - HF Space 재배포 후 `RUNNING` 확인
  - `curl` 200 확인
  - playwright live smoke 통과
  - 스크린샷: `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260420-142044.png`
  - HF run log error pattern 0건
- 못 한 부분:
  - 없음

## Batch 3. 한국어 현지화 + 라이트 모드 contrast

- Commit: `0635d66`
- 변경 파일 수: 4
- 핵심 변경:
  - `playground/app.py`, `playground/simulation.py` 영어 잔재 정리
  - 한국어 라벨/placeholder/상태 메시지 보강
  - 라이트 모드 CSS contrast pass
  - 회귀 테스트 추가
- 라이브 검증:
  - 공통 게이트 전체 통과
  - HF Space 재배포 후 `RUNNING` 확인
  - `curl` 200 확인
  - playwright live smoke 통과
  - 그래프 스크린샷: `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260420-143910.png`
  - 라이트 모드 확인 스크린샷:
    - `C:\Users\admin\Projects\knoema\artifacts\live-light-before-20260420-143941.png`
    - `C:\Users\admin\Projects\knoema\artifacts\live-light-top-20260420-143941.png`
    - `C:\Users\admin\Projects\knoema\artifacts\live-light-lower-20260420-143941.png`
  - HF run log error pattern 0건
- 못 한 부분:
  - root README 다국어 표의 legacy mojibake는 이번 배치 범위 밖

## Batch 4. 학술 깊이 강화

- Commit: `0d762cb`
- 변경 파일 수: 10
- 핵심 변경:
  - `planning/proposal_subtask_mapping.md` 보강
  - playground benchmark caveat 자동 표기 추가
  - `scripts/verify_replication.py` 및 재현 검증 테스트 추가
  - arXiv placeholder/badge readiness 테스트 추가
  - 경쟁 비교 UI에서 금지된 타사 코드명 노출 제거
- 라이브 검증:
  - 공통 게이트 전체 통과
  - HF Space 재배포 후 `RUNNING` 확인
  - `curl` 200 확인
  - playwright live smoke 통과
  - 스크린샷: `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260420-145910.png`
  - HF run log error pattern 0건
- 못 한 부분:
  - 없음

## Batch 5. 게임 어댑터 정직성 + 데모 시나리오 강화

- Commit: `893d392`
- 변경 파일 수: 9
- 핵심 변경:
  - Godot/Unity tavern browser mirror 상단에 "not a real engine export" 배지 추가
  - 두 HTML 파일 상단에 한/영 HTML 주석 추가
  - `README.md`, `adapters/godot/README.md`, `adapters/unity/README.md`, `docs/adapters/game_demos.md`에 실제 엔진 실행/빌드 명령 안내 추가
  - Playground 기본 시나리오를 `Office team conflict`로 변경
  - README Quick start에 추천 데모 3개 큐레이션
  - 회귀 테스트 추가
- 라이브 검증:
  - 공통 게이트 전체 통과
  - HF Space 재배포 후 `RUNNING` 확인
  - `curl` 200 확인
  - playwright live smoke 통과
  - 스크린샷: `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260420-151120.png`
  - HF run log error pattern 0건
- 못 한 부분:
  - 실제 Godot Web export preset / Unity WebGL build method 자동화는 문서화만 했고 저장소 자동 빌드 스크립트는 추가하지 않음

## HF Space 최종 상태

- HF 배포 소스 커밋: `893d392eac38b281c07e86333c0464c9fa0ee7b9`
- HF Space repo sha: `307c5f1ddfd5d1001e486c26355287b45292f2a7`
- 최종 확인 시각: 2026-04-21T00:12:28.1407803+09:00
- runtime.stage: `RUNNING`
- 최종 smoke 스크린샷: `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260420-151120.png`

## 사용자 단독 액션 잔여 목록

- GitHub repository Settings -> Secrets and variables -> Actions에 `HF_TOKEN` 등록
  - 배치 1의 live smoke workflow와 기존 HF deploy workflow가 GitHub에서 실제로 돌려면 필요
- Godot 실제 Web export가 필요하면 Godot editor에서 `Web` export preset 생성
- Unity 실제 WebGL build가 필요하면 host project에 `TavernDemoBuild.BuildWebGL` 같은 Editor build method 추가

## 다음 미팅 / 디딤돌 데모 추천 3개

1. `Office team conflict`
   - 첫 클릭만으로 갈등, 협상, 관계 변화가 바로 보임
   - "default demo"로 두기 좋아서 설명 오버헤드가 적음
2. `Village: ten agents`
   - force-directed relationship graph의 입체감과 many-to-many 상호작용을 가장 잘 보여줌
   - 5-agent smoke 이후 자연스럽게 scale-up 설명 가능
3. `Dorm: two agents`
   - replay-only 재현성, grounded JSONL log, compact interaction loop 설명에 적합
   - 짧은 시간 안에 before/after 비교를 보여주기 쉬움

## 토킹 포인트

- "같은 runtime이 research benchmark, playground, game adapter mirror까지 한 surface로 이어진다."
- "prod 사고 이후 live smoke + HF runtime log grep + compat guard를 CI에 넣어 재발 방지선을 세웠다."
- "relationship graph는 정적 구면 배치에서 interactive force-directed 3D로 올라와 live demo 설득력이 커졌다."
- "학술 산출물은 benchmark caveat와 replication verifier를 붙여 과장 없이 재현 가능하게 정리했다."

## 남은 리스크

- root README 다국어 표와 일부 legacy 문서에는 playground 범위 밖 mojibake가 남아 있다.
- Unity/Godot 실제 웹 빌드는 현재 문서화만 되어 있고, repo 내부 자동 빌드 파이프라인은 없다.
- GitHub Actions용 `HF_TOKEN` secret이 아직 없으면 원격 auto-deploy / live smoke는 로컬처럼 동작하지 않는다.
