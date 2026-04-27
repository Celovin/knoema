# `luvoire.theory.rat.v1` — Design Spec

**Status**: Draft for implementation
**Author**: Celovin (Choi Jihwan)
**Date**: 2026-04-27
**Tracks**: ASC 2026 포스터 방법론 (T1 #2) + 디딤돌 위탁연구 A 범죄학 PoC
**Successor of**: (none; new module)
**Reference target**: `code:luvoire.theory.rat.v1` (the string that DSL v2 Tier A parameters point to)
**Related**: `docs/dsl/v2-design-spec.md`, `docs/dsl/v2-reference.md`

---

## 1. 목적

Routine Activity Theory (Cohen & Felson 1979) 의 세 요소 — motivated offender / suitable target / capable guardianship — 를 **합성 시뮬레이션의 시공간 수렴 조건**으로 코드 안에 잠근다. Tier A 잠금 모듈로서 YAML로 노출되지 않으며, 변수 조절은 Tier B/C로만 이뤄진다.

핵심 메서드 시그니처 한 개:

```python
def opportunity_event(
    actor_state: ActorState,
    target: TargetExposure,
    guardianship: GuardianshipGap,
    tick: int,
    cell: H3CellRef,
) -> OpportunityEvent | None
```

세 요소가 같은 tick + 같은 (또는 인접) cell 에서 수렴할 때만 `OpportunityEvent` 가 발생한다. 이벤트 발생은 **실제 범죄 발생 주장이 아니라**, 이론 조건 수렴을 표시하는 합성 이벤트 (synthetic event).

## 2. 비목표

- 실 사건·실 좌표·실 인물 매핑
- 위험 점수 산출 (Civilian Use Policy v1.0 #2 거부)
- LLM 호출 (이 모듈은 순수 결정성 함수)
- 이론 변형(예: Crime Pattern Theory) — 본 모듈은 RAT 한정. 변형은 별도 모듈

## 3. 데이터 클래스

```python
# src/luvoire/theory/rat.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

H3CellRef = str  # 15-char h3 v4 hex index, 또는 가상 셀 식별자

@dataclass(frozen=True, slots=True)
class ActorState:
    """A simulated actor with non-zero motivation toward an opportunity event.

    Note: The classical RAT term is 'motivated offender'. We use 'actor state' in
    the simulation surface to reduce labeling effects in synthetic populations;
    the connection to motivated-offender component is documented in the spec
    text and ASC abstract.
    """
    actor_id: str
    motivation: float  # [0, 1], synthetic units
    cell: H3CellRef
    tick: int


@dataclass(frozen=True, slots=True)
class TargetExposure:
    """Place- and time-conditional target visibility / accessibility.

    'suitable target' in classical RAT is decomposed via VIVA (Value, Inertia,
    Visibility, Access). Here we collapse VIVA into a single scalar 0..1
    weighted by accessibility * visibility for simplicity; future revisions may
    expose VIVA components.
    """
    target_id: str
    exposure: float  # [0, 1], synthetic units
    cell: H3CellRef
    tick: int


@dataclass(frozen=True, slots=True)
class GuardianshipGap:
    """Place-level guardianship deficit at a given tick.

    Higher values indicate lower guardianship presence (i.e., a larger 'gap').
    Captures formal (police, CCTV) + informal (neighbors, foot traffic) layers
    as a single synthetic scalar.
    """
    place_id: str
    gap: float  # [0, 1], 1 = no guardian, 0 = strong guardian
    cell: H3CellRef
    tick: int


@dataclass(frozen=True, slots=True)
class OpportunityEvent:
    tick: int
    cell: H3CellRef
    actor_id: str
    target_id: str
    place_id: str
    convergence_score: float  # actor.motivation * target.exposure * gap.gap
    kind: Literal["rat_v1_synthetic_opportunity"] = "rat_v1_synthetic_opportunity"
```

## 4. Convergence rule (Tier A 잠금)

```python
def opportunity_event(
    actor_state: ActorState,
    target: TargetExposure,
    guardianship: GuardianshipGap,
    tick: int,
    cell: H3CellRef,
    *,
    threshold: float = 0.125,  # 0.5 * 0.5 * 0.5
) -> OpportunityEvent | None:
    if actor_state.tick != tick or target.tick != tick or guardianship.tick != tick:
        return None
    if not _same_or_adjacent_cell(actor_state.cell, cell):
        return None
    if not _same_or_adjacent_cell(target.cell, cell):
        return None
    if not _same_or_adjacent_cell(guardianship.cell, cell):
        return None
    score = actor_state.motivation * target.exposure * guardianship.gap
    if score < threshold:
        return None
    return OpportunityEvent(
        tick=tick,
        cell=cell,
        actor_id=actor_state.actor_id,
        target_id=target.target_id,
        place_id=guardianship.place_id,
        convergence_score=score,
    )
```

**잠금 결정** (Tier A — YAML 노출 금지):
- 세 요소 곱셈 정의 자체 (`motivation * exposure * gap`)
- 동일 tick 요구 (시간 수렴)
- 셀 근접 정의 (`_same_or_adjacent_cell`)
- 수치 입력 형식 (각 [0,1] 합성 단위)

**조절 가능** (Tier B 또는 C 로 YAML에서):
- `threshold` 값 (Tier C, sweep 가능)
- 각 입력 (motivation/exposure/gap)의 분포 prior (Tier B, KOSTAT/safemap 출처)
- guardianship.gap 의 합산 가중치 (Tier C — formal vs informal layer 비율)

## 5. Cell adjacency

```python
def _same_or_adjacent_cell(a: H3CellRef, b: H3CellRef) -> bool:
    if a == b:
        return True
    # Synthetic-cell label support: e.g., "synthetic-grid-r3c4"
    if not _is_h3_v4_string(a) or not _is_h3_v4_string(b):
        # 동일 ID 외에는 인접으로 보지 않음 (합성 그리드는 별도 어댑터 책임)
        return False
    # Real h3 v4 input: lazy-import to avoid runtime dependency on h3-py
    try:
        import h3  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return False
    return h3.are_neighbor_cells(a, b)
```

**의도**: h3-py는 옵션 의존성 (T2에서 정식 추가). 그 전까지는 `same_or_adjacent`는 동일 셀만 인정. 합성 그리드는 어댑터(T2)에서 자체 인접 함수 주입 가능하도록 별도 protocol을 후에 추가.

## 6. Module surface

```python
# src/luvoire/theory/__init__.py
"""Theory modules referenced as Tier A code constants by Scenario DSL v2."""
from luvoire.theory import rat  # noqa: F401

# src/luvoire/theory/rat.py
__all__ = [
    "ActorState",
    "GuardianshipGap",
    "H3CellRef",
    "OpportunityEvent",
    "TargetExposure",
    "opportunity_event",
]
```

`luvoire/__init__.py` 에는 노출하지 않음 (Tier A 잠금 모듈 — public API surface가 아니라 reference target).

## 7. Tests

`tests/test_theory_rat_v1.py` (≥8 cases):

1. `test_convergence_above_threshold_emits_event` — high motivation/exposure/gap → event
2. `test_convergence_below_threshold_returns_none` — low values → None
3. `test_mismatched_tick_returns_none` — actor at tick 5, target at tick 6 → None
4. `test_actor_in_distant_cell_returns_none` — different unrelated synthetic cells → None
5. `test_same_synthetic_cell_emits_event_when_score_clears` — 동일 합성 cell ID
6. `test_h3_neighbor_cells_recognized` — h3-py 미설치 환경에서는 skip; 설치 시 인접 통과
7. `test_event_contains_convergence_score` — 곱 정확성
8. `test_event_kind_is_locked_to_rat_v1_synthetic` — string literal 변경 방지

추가 (총 12+ 목표):

9. `test_threshold_default_is_one_eighth` — 0.125
10. `test_threshold_override_respected` — keyword-only `threshold=` 인자
11. `test_event_dataclass_is_frozen_and_hashable`
12. `test_actor_state_target_exposure_guardianship_gap_immutable`

## 8. Acceptance Criteria

1. `pytest tests/test_theory_rat_v1.py --no-cov`: ≥8 PASS (목표 12)
2. `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py`: 그린 (직전 768+ 베이스라인 유지)
3. `ruff check .`: clean
4. `mypy src`: clean (152 → 153)
5. `python scripts/verify_replay_shas.py`: 5 baselines 변동 없음
6. `python scripts/lint_dsl_v2.py tests/fixtures/scenarios/v2_rat_baseline.yaml --strict`: 통과 (Tier A의 ref가 이제 실존하는 모듈을 가리킴)
7. `python -m mkdocs build --strict`: pass
8. `pytest tests/test_v7_rename_sweep.py`: 2/2

## 9. 산출 파일

신규:
- `src/luvoire/theory/__init__.py`
- `src/luvoire/theory/rat.py`
- `tests/test_theory_rat_v1.py`
- `docs/theory/rat-v1-design-spec.md` (이 문서)
- `docs/theory/rat-v1-reference.md` (런타임 reference)

수정:
- `CHANGELOG.md` `[Unreleased]` 추가
- `mkdocs.yml` nav 추가
- `src/luvoire/dsl/v2/parameters.py` — Tier A `ref` 값이 이제 실존 모듈을 가리킴을 docstring에 명시 (선택)

## 10. 비범위

- Crime Pattern Theory / Rational Choice 이론 매핑 — 별도 모듈
- 실제 cell 인접성 (h3-py 정식 통합) — T2
- LLM-driven actor motivation 추정 — T3 cognition middleware

## 11. 윤리

이 모듈은 **합성 이벤트 발생기**이며, 어떤 형태로도 실제 사건 예측·개인 위험점수 산출에 사용될 수 없다. README 의 Civilian Use Policy v1.0 #2 (predictive policing/individual crime-risk scoring 거부) 와 정렬되며, scenario YAML의 `ethics.no_prediction: true` 와 `ethics.no_real_geometry: true` 를 디폴트로 가정한 출력을 생성한다.
