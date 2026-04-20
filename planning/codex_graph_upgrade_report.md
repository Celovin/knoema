# 관계 그래프 v2 보고서

- 작업 일시: 2026-04-20
- 브랜치: `main`
- 작업 디렉터리: `C:\Users\admin\Projects\knoema`

## 커밋

- Git commit: `003aceb` - `feat(playground): force-directed 3D relationship graph`
- HF Space commit: `a66ce5571c7a60ed099b088bd03aa8905580f95b`
- HF Space runtime.stage: `RUNNING`

## 변경 파일

- `playground/app.py`
- `tests/test_playground_agent_colors.py`

## 구현 요약

1. 관계 그래프 배치를 정적 구면 분포에서 force-directed 3D 레이아웃으로 교체했다.
2. `n == 1`, `n == 2`는 기존 특수 케이스를 유지하고, 그 외에는 `networkx.spring_layout(..., dim=3, seed=42, iterations=100)`을 사용한다.
3. 노드 크기는 degree 기반으로 `12 + degree * 4`를 적용하고 최대값은 `30`으로 제한했다.
4. 엣지는 개별 `Scatter3d` trace로 분리해서 weight에 따라 선 굵기, trust에 따라 투명도가 달라지도록 바꿨다.
5. 카메라는 perspective로 바꾸고 `scene.aspectmode='cube'`, `dragmode='orbit'`, 노드 외곽선과 텍스트 색을 조정해 깊이 인지를 강화했다.
6. 기존 `_agent_color_map` 경로는 그대로 유지해 다른 surface와의 색상 동기화를 깨지 않게 했다.

## 테스트 및 검증

- `pytest -q tests/test_playground_agent_colors.py tests/test_playground_layout.py tests/test_playground_encoding_guard.py`
  - 통과
- `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py`
  - 통과 (`511 passed, 1 skipped`)
- `ruff check .`
  - 통과
- `mypy src`
  - 통과

## 추가 테스트

- 5개 에이전트, 6개 엣지 입력에서 edge trace가 2개 이상 생성되는지 확인
- node marker size가 모두 동일하지 않은지 확인
- edge line width가 weight 차이를 반영하는지 확인
- `scene.aspectmode == "cube"`인지 확인

## 배포 메모

- GitHub `main` 푸시 완료
- HF Space는 로컬 `HF_TOKEN`으로 `playground/app.py`만 직접 업로드했다.
- 업로드 후 90초 대기 뒤 `space_info('celovin/knoema-playground').runtime.stage`가 `RUNNING`임을 확인했다.

## 미실시 항목

- 없음
