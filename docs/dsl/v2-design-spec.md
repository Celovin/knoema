# Scenario DSL v2 — Design Spec

**Status**: Draft for implementation handoff
**Author**: Celovin (Choi Jihwan)
**Date**: 2026-04-27
**Tracks**: ASC 2026 포스터 방법론 (T1 #1) + 디딤돌 위탁연구 A 범죄학 PoC
**Successor of**: `schemas/scenario_v1.json`, `src/luvoire/dsl/`
**Compat policy**: v1 scenarios load with deprecation warning (one release window)

---

## 1. 목표

Scenario DSL v1은 fictional·ethics·event 골조를 잘 갖췄으나, **연구자 조절 변수의 인식론적 지위**를 표현할 방법이 없어, 일상활동이론(RAT) 같은 이론 기반 시뮬레이션에서 다음 두 약점을 노출한다.

1. **Garden-of-forking-paths 노출**: 모든 변수가 평면적으로 점값으로만 들어와, 어떤 게 이론 상수이고 어떤 게 실증 prior이고 어떤 게 탐색 knob인지 구분 불가
2. **Sensitivity sweep 미지원**: range·sweep 표현 불가 → SALib·sbi 같은 캘리브레이션 파이프라인 wiring 어려움

DSL v2는 **변수 3-tier**(A/B/C) + **GIS-readiness** + **realism roadmap E1~E5 게이트**를 도입해 이 둘을 해결한다.

## 2. 비목표 (out of scope, 명시)

- 실 행정구역·실 좌표 기반 분석 (Civilian Use Policy v1.0 #2)
- v1 → v2 자동 마이그레이션 도구 (수동 변환 + deprecation 경로만)
- LLM-call 변경 (DSL은 scenario 직렬화에 한정)
- 기존 replay SHA baseline 변동 (CI gate)

## 3. 변수 3-tier (핵심)

### Tier A — Theoretical constant

이론 정의 그 자체. **YAML로 노출 금지**, code 모듈 reference만.

```yaml
parameters:
  opportunity_definition:
    tier: A
    ref: "code:luvoire.theory.rat.v1"
```

규칙:
- `tier: A` 강제
- `ref` 키는 정규식 `^code:[a-z_][a-z0-9_.]*\.v\d+$` 매칭
- 다른 키(`value`, `range`, `source`) 금지 → validator에서 fail
- `ref`가 가리키는 모듈은 PR 머지 시점에 import 가능해야 함 (lint 시점 자동 검증)

### Tier B — Empirical prior

실측 통계·문헌에서 파생된 값. **출처 메타데이터 강제**.

```yaml
parameters:
  schedule_prior:
    tier: B
    source: "KOSTAT 2024 생활시간조사"
    table_id: "T-08"
    license: "KOGL Type 1"
    value: 0.42  # 또는 distribution 식별자
```

규칙:
- `tier: B` 강제
- `source: str` 필수, 비어있지 않을 것
- `table_id`, `license`, `revision`, `url` 선택 메타데이터
- `value` 또는 `distribution` 둘 중 하나 필수 (`value`: 점값, `distribution`: 외부 분포 식별자 e.g., `parquet:data/priors/timeuse_v1.parquet#strata=urban_30s`)
- `range` 키는 허용 (sensitivity sweep 시 prior bracketing) but 사용 시 `default` 필수

### Tier C — Exploration knob

연구자 자유 조절. **range 기반 sweep 강제**.

```yaml
parameters:
  guardianship_density:
    tier: C
    range: [0.1, 0.9]
    sweep: 9
    default: 0.5
    description: "Place-level capable guardianship density (synthetic units)."
```

규칙:
- `tier: C` 강제
- `range: [lo, hi]` 필수, `lo < hi`
- `default: float` 필수, `lo <= default <= hi`
- `sweep: int >= 2` 선택 (지정 시 SALib·Optuna가 사용)
- `description: str` 권장 (없으면 lint warn)
- `value` 키 단독 사용 금지 (warn) → range로 변환 권고

## 4. 새 ethics 필드

```yaml
ethics:
  fictional: true
  no_real_people: true
  no_prediction: true
  no_suspect_scoring: true
  no_real_geometry: true   # NEW v2 — 실 좌표/실 행정구역 분석 단위 사용 금지 강제
  sensitive_domain: false
  irb_notes: null
```

`no_real_geometry: true`이면:
- `environment.epsg` 필드는 비어있거나 가상 EPSG (`luvoire-synthetic-*`)만 허용
- `environment.h3_cell` 필드는 분석 단위가 아니라 시각화 prior로만 사용 (런타임에 분석 단위로 사용하면 fail)

## 5. Environment 확장 (GIS readiness, optional)

```yaml
environment:
  start_time: "2026-04-23T19:00:00"
  location_path: ["Luvoire Demo World", "Seoul-style Synthetic Grid", "Plaza A"]
  conditions:
    weather: clear
    crowd_level: high
  h3_cell: "8830e1ad81fffff"      # NEW v2 — h3 v4 hex index, 옵션
  epsg: "luvoire-synthetic-v1"   # NEW v2 — 가상 좌표계만 허용
```

규칙:
- `h3_cell`: `^[0-9a-f]{15}$` (h3 v4 string 형식)
- `epsg`: prefix `luvoire-synthetic-`로 시작하지 않으면 ethics.no_real_geometry=true 하에서 fail

## 6. Pydantic 모델 (구현 명세)

```python
# src/luvoire/dsl/v2/parameters.py

from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator

class TierAParam(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tier: Literal["A"] = "A"
    ref: str = Field(pattern=r"^code:[a-z_][a-z0-9_.]*\.v\d+$")

class TierBParam(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tier: Literal["B"] = "B"
    source: str = Field(min_length=1)
    table_id: str | None = None
    license: str | None = None
    revision: str | None = None
    url: str | None = None
    value: float | int | str | bool | None = None
    distribution: str | None = None
    range: tuple[float, float] | None = None
    default: float | None = None

    @model_validator(mode="after")
    def _check_value_or_distribution(self) -> "TierBParam":
        if self.value is None and self.distribution is None:
            raise ValueError("Tier B requires either 'value' or 'distribution'")
        if self.range is not None and self.default is None:
            raise ValueError("Tier B with 'range' requires 'default'")
        return self

class TierCParam(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tier: Literal["C"] = "C"
    range: tuple[float, float]
    default: float
    sweep: int | None = Field(default=None, ge=2)
    description: str | None = None

    @model_validator(mode="after")
    def _check_range_default(self) -> "TierCParam":
        lo, hi = self.range
        if not lo < hi:
            raise ValueError(f"Tier C range must satisfy lo < hi (got {lo}, {hi})")
        if not lo <= self.default <= hi:
            raise ValueError(f"Tier C default {self.default} must be within range [{lo}, {hi}]")
        return self

ParameterSpec = Annotated[
    Union[TierAParam, TierBParam, TierCParam],
    Field(discriminator="tier"),
]
```

```python
# src/luvoire/dsl/v2/scenario.py

class EthicsSpecV2(BaseModel):  # extends v1 EthicsSpec
    fictional: bool = True
    no_real_people: bool = True
    no_prediction: bool = True
    no_suspect_scoring: bool = True
    no_real_geometry: bool = True   # NEW
    sensitive_domain: bool = False
    irb_notes: str | None = None

class EnvironmentSpecV2(BaseModel):  # extends v1 EnvironmentSpec
    start_time: datetime
    location_path: tuple[str, ...] = Field(min_length=1)
    conditions: dict[str, str | int | float | bool] = Field(default_factory=dict)
    h3_cell: str | None = Field(default=None, pattern=r"^[0-9a-f]{15}$")
    epsg: str | None = None

class ScenarioV2(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["2.0"] = "2.0"
    scenario_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    domain: ScenarioDomain
    description: str = Field(min_length=1)
    seed: int = Field(ge=0)
    tick_duration_minutes: int = Field(default=60, ge=1)
    duration_days: int = Field(default=1, ge=1)
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)   # NEW
    environment: EnvironmentSpecV2
    agents: list[AgentSpec] = Field(min_length=1)
    events: list[EventSpec] = Field(default_factory=list)
    metrics: list[MetricSpec] = Field(default_factory=list)
    ethics: EthicsSpecV2 = Field(default_factory=EthicsSpecV2)
    local_response: str = '{"action_type": "observe", "target": null, "content": "records the scenario state."}'
```

## 7. Validator 확장

`src/luvoire/dsl/v2/validator.py`:

추가 validation 규칙:

1. **Tier A code reference 존재 확인**: `parameters.*.ref`가 `code:X.vN`이면 `importlib.import_module(X)`가 성공해야 함 (lint 시점, runtime은 skip)
2. **no_real_geometry 게이트**:
   - `ethics.no_real_geometry=True`이면 `environment.epsg`가 None 또는 `luvoire-synthetic-*` prefix 필수
3. **Tier C sweep + range consistency**: lo < hi, lo <= default <= hi (Pydantic이 처리)
4. **Disallowed phrase check**: v1 DISALLOWED_PURPOSE_PHRASES 그대로 상속 + 신규 추가
   ```python
   ADDITIONAL_DISALLOWED_PHRASES_V2 = (
       "individual risk score",
       "real address",
       "real coordinate",
       "real-world prediction",
   )
   ```

## 8. Parser & Migration

`src/luvoire/dsl/v2/parser.py`:

```python
def load_scenario_v2(path: str | Path, *, validate: bool = True) -> ScenarioV2:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version", "1.0")
    if schema_version == "1.0":
        warnings.warn(
            f"{path}: Scenario DSL v1.0 is deprecated; migrate to v2.0. "
            "v1 scenarios will be auto-upgraded for one release window.",
            DeprecationWarning,
            stacklevel=2,
        )
        payload = _upgrade_v1_to_v2(payload)
    scenario = ScenarioV2.model_validate(payload)
    if validate:
        validate_scenario_v2(scenario)
    return scenario
```

`_upgrade_v1_to_v2(payload)`:
- `schema_version` `"1.0"` → `"2.0"`
- `parameters: {}` 추가
- `ethics.no_real_geometry: true` 추가 (default)
- `environment.h3_cell`, `environment.epsg`는 미설정 유지

기존 `load_scenario` (v1)는 1 release window 동안 유지 (deprecation warning) 후 v2 alias로 전환.

## 9. JSON Schema export

새 파일 `schemas/scenario_v2.json` 추가. 기존 `schemas/scenario_v1.json` 보존 (호환성 보장 evidence).

```python
# src/luvoire/dsl/v2/serializer.py
def scenario_v2_json_schema() -> dict[str, Any]:
    return ScenarioV2.model_json_schema()
```

CI gate: `python -c "import json; from luvoire.dsl.v2 import scenario_v2_json_schema; ..."`로 schema 재생성 후 git diff 없어야 함.

## 10. CI lint 스크립트

`scripts/lint_dsl_v2.py` (신규):

```python
def lint_scenario_yaml(path: Path) -> list[str]:
    issues = []
    payload = yaml.safe_load(path.read_text())
    parameters = payload.get("parameters", {})
    for name, spec in parameters.items():
        tier = spec.get("tier")
        if tier == "C":
            if "range" not in spec:
                issues.append(f"{path}::{name}: Tier C without 'range' (warn)")
            if "value" in spec and "range" not in spec:
                issues.append(f"{path}::{name}: Tier C should use 'range' not 'value' (warn)")
        if tier == "A" and any(k in spec for k in ("value", "range", "source")):
            issues.append(f"{path}::{name}: Tier A must only define 'ref' (fail)")
        if tier == "B" and not spec.get("source"):
            issues.append(f"{path}::{name}: Tier B requires 'source' (fail)")
    return issues
```

CI 호출: `python scripts/lint_dsl_v2.py scenarios/library/ examples/scenarios/ --strict`

## 11. 테스트 매트릭스 (DoD ≥ 14 tests)

새 테스트 파일:

- `tests/test_dsl_v2_schema.py` — JSON schema export, 필드 enumeration (3개 케이스)
- `tests/test_dsl_v2_parameters.py` — 3-tier 검증 (A invalid mix / B no source / C range error / C default out of range — 8 케이스)
- `tests/test_dsl_v2_ethics.py` — no_real_geometry 게이트 (epsg 검증, h3_cell 검증 — 4 케이스)
- `tests/test_dsl_v2_parser.py` — v1 deprecation warning, v2 load, _upgrade_v1_to_v2 (5 케이스)
- `tests/test_dsl_v2_lint.py` — lint script 결과 검증 (5 케이스)

총 25 케이스 목표 (DoD 최소 14).

추가:
- `tests/fixtures/scenarios/v2_rat_baseline.yaml` — Tier A/B/C 모두 포함된 골든 시나리오
- `tests/fixtures/scenarios/v1_legacy.yaml` — deprecation 경로 fixture

## 12. Acceptance Criteria

1. `pytest tests/test_dsl_v2_*.py --no-cov`: 모든 테스트 통과 (≥14, 목표 25)
2. `pytest tests/test_dsl_*.py --no-cov`: 기존 v1 테스트 영향 없음
3. `pytest --no-cov`: 전체 그린 (700+ pass)
4. `ruff check .`: clean
5. `mypy src`: clean
6. `python scripts/verify_replay_shas.py`: **5개 baseline 변동 없음** (가장 중요)
7. `python scripts/lint_dsl_v2.py scenarios/library/ --strict`: 통과 (기존 v1 시나리오는 v2로 lint하지 않음 — 별도 디렉토리)
8. `pytest tests/test_v7_rename_sweep.py`: legacy brand token sweep 게이트 그린 (allowlist 외 토큰 등장 시 fail)
9. `python -m mkdocs build --strict`: pass (docs/dsl/v2-reference.md 추가 시)
10. `python -c "from luvoire.dsl.v2 import ScenarioV2, load_scenario_v2"`: 임포트 성공

## 13. 산출 파일 목록

새 파일:
- `src/luvoire/dsl/v2/__init__.py`
- `src/luvoire/dsl/v2/parameters.py`
- `src/luvoire/dsl/v2/scenario.py`
- `src/luvoire/dsl/v2/parser.py`
- `src/luvoire/dsl/v2/validator.py`
- `src/luvoire/dsl/v2/serializer.py`
- `schemas/scenario_v2.json`
- `scripts/lint_dsl_v2.py`
- `docs/dsl/v2-reference.md`
- `docs/dsl/migration-v1-to-v2.md`
- `tests/test_dsl_v2_schema.py`
- `tests/test_dsl_v2_parameters.py`
- `tests/test_dsl_v2_ethics.py`
- `tests/test_dsl_v2_parser.py`
- `tests/test_dsl_v2_lint.py`
- `tests/fixtures/scenarios/v2_rat_baseline.yaml`
- `tests/fixtures/scenarios/v1_legacy.yaml`

수정 파일:
- `src/luvoire/dsl/__init__.py` — v2 re-export 추가, deprecation warn
- `src/luvoire/__init__.py` — `ScenarioV2` 노출
- `CHANGELOG.md` — `[Unreleased]`에 v2 entry
- `mkdocs.yml` — v2 docs nav
- `pyproject.toml` — entry 변동 없음 (v2는 코어 파트)

## 14. 비범위 (이 PR에서 하지 않는 것)

- T1 #2의 `luvoire.theory.rat.v1` 모듈 — 별도 PR. 이 PR은 ref string만 수용
- GIS 좌표계 통합 — `epsg` 필드 schema만, 실제 `luvoire.geo` 모듈은 T2
- SALib sweep 호출 — `parameters.*.sweep` 필드 schema만, 실제 sweep은 T1 #3
- v1 → v2 자동 변환 도구 (마이그레이션 스크립트는 release window 후)

## 15. 위험 & 완화

| 위험 | 완화 |
|---|---|
| Pydantic discriminated union 런타임 비용 | tier 키 기반 → fast-path, 측정 불필요 |
| v1 시나리오의 silent break | parser에서 deprecation warning + auto-upgrade 1 release window 보장 |
| replay SHA 변동 | DSL 변경은 logger·simulator 호출 경로 안 건드림. CI gate로 강제 검증 |
| 신규 lint 규칙이 기존 v1 fixture에 false-fail | lint 대상 디렉토리 명시 (scenarios/library/ + examples/scenarios/v2/만) |

---

**END Spec**. 구현은 `planning/codex_handoff_dsl_v2_2026-04-27.md` 참조.
