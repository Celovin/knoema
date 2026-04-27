# KCI 투고 초안 (한국 범죄학 / 전산사회과학 학술지 대상)

**제목 (가제)**: 합성 한국형 도시격자 ABM에서의 일상활동이론 — 감사 가능한 시나리오를 위한 결정성 리플레이와 변수 3-tier 노출

**저자**: 최지환 (셀로빈) · [공동저자 TBD — 위탁연구실 교수님 동의 후]
**대상 학술지 후보**: 한국범죄학회지, 한국컴퓨터정보학회지 융합 트랙
**투고 목표**: 2027-09 (디딤돌 2단계 종료 직전)

## 초록 (한국어 600자 이내)

일상활동이론(RAT)은 동기화된 행위자, 적합한 표적, 유능한 보호자의 부재가 시공간에서 수렴할 때 범죄 기회가 발생한다고 본다. RAT를 투명한 에이전트 기반 모형(ABM)으로 옮길 때 흔히 수렴 규칙은 코드 깊숙이 묻히고 숫자 knob만 외부에 노출되어, 어떤 주장이 이론적이고 어떤 것이 실증적이며 어떤 것이 탐색적인지 평가자가 구분하기 어렵다. 본 연구는 RAT 수렴 규칙을 코드 상수로 잠그고 시나리오 YAML에서는 타입드 문자열(Tier A)로만 참조하도록 한 결정성 Python ABM을 제안한다. 실증 prior(Tier B)는 출처 메타데이터를, 탐색 knob(Tier C)는 범위와 기본값을 의무로 선언한다. 시나리오 DSL의 윤리 블록은 ``no_real_geometry: true``를 기본값으로 두며, 합성이 아닌 좌표계 라벨은 검증 단계에서 거부된다. 4096-샘플 Saltelli 설계에서 RAT 세 요소의 Sobol 지표는 거의 대칭(1차 ≈ 0.23, 총 차수 ≈ 0.54)이며, 약 30%가 상호작용 효과로 곱셈형 수렴 규칙의 이론적 예측과 일치한다. 동일 시드 실행은 로컬과 CI에서 바이트 단위로 재현된다.

## 1. 서론 (1.5p)

기존 한국 범죄학에서 ABM은 *Mesa* 또는 *NetLogo* 위에 통계 모형을 결합한 형태가 주류였다. LLM 에이전트가 ABM에 도입되면서(예: Park et al. 2023, CrimeMind 2025), 이론적 가정과 실증적 가정이 같은 평면에서 노출되는 새 위험이 생겼다. 본 연구는 위험을 두 갈래로 나눈다.

1. **이론 대 실증의 혼동.** 어떤 변수가 *이론에서 유도된* 상수이고 어떤 것이 *데이터에서 추정된* prior이며 어떤 것이 *연구자가 자유로이 흔드는* knob인지 시나리오 파일만 보고 알 수 없다.
2. **재현성의 결여.** 동일 시드·동일 시나리오·동일 코드에서 동일 결과가 나오는지 평가자가 확인할 수 없다.

본 연구는 이 둘을 동시에 해결한다.

## 2. 방법

(공통 §) — `methodology_section.md` 인용. RAT 잠금 모듈, DSL v2 변수 3-tier, Sobol 민감도 패널, 재현성 인프라, CrimeMind 비교 harness, POM 3-gate 검증 모두 동일.

## 3. 결과

### 3.1 변수 3-tier가 잘 작동함을 보이는 사례

5×5 합성 도시격자에서 default seed 20260427로 25개 cell 중 7개 cell에서 이벤트 발생. 동일 시드 재실행은 byte-identical 요약(SHA-256 invariant 검증).

### 3.2 곱셈형 수렴 규칙의 sensitivity 패턴

Sobol 1차 ≈ 0.23 / 총 차수 ≈ 0.54로 세 요소가 대칭적으로 동등한 영향력을 가짐. 상호작용 효과 약 30%는 multiplicative 모델의 이론적 예측과 일치.

### 3.3 CrimeMind 비교 — 가중치만 흔들어도 분포가 이동

6×6 격자에서 equal_weights 13건, motivation_heavy 0건, guardian_heavy 0건. Tier A 잠금 규칙은 그대로이고 Tier C 가중치만 흔들었음에도 합성 이벤트 분포가 크게 이동.

## 4. 논의 (1p)

본 프레임워크는 예측 시스템이 아니라 방법론 포스터이며, 본질적으로 허구·합성·비식별이다. Luvoire 엔진은 정책 차원에서 국방·예측치안·PSYOP·비동의 트위닝·미성년 합성 파이프라인 사용을 거부한다(``POLICIES/civilian_use.md``). 한국 범죄학에서 ABM 활용이 늘어나는 시점에, 이론·실증·탐색을 분리해 노출하는 변수 3-tier가 평가가능성과 재현성을 동시에 끌어올리는 실용적 경로임을 제시한다.

## 5. 한계 (0.5p)

- 합성 도시격자는 실제 한국 도시의 특정 지역을 대표하지 않음.
- LLM 에이전트의 의사결정 일관성은 본 연구 범위 밖. SOTOPIA 등 별도 fidelity benchmark 필요.
- 디딤돌 위탁연구실의 IRB 자문 결과를 추후 후속 논문에 반영 예정.

## 참고문헌 (선별)

- Cohen LE, Felson M. (1979). Social change and crime rate trends: A routine activity approach.
- Park JS et al. (2023). Generative agents: Interactive simulacra of human behavior. arXiv:2304.03442.
- CrimeMind (2025). Simulating urban crime with multi-modal LLM agents. arXiv:2506.05981.
- Saltelli A. (2002). Making best use of model evaluations to compute sensitivity indices.
- Anderson JR. (2007). How can the human mind occur in the physical universe?
- Grimm V et al. (2005). Pattern-oriented modeling of agent-based complex systems.

## 윤리 진술 (Civilian Use)

본 연구는 합성·허구 시나리오만 사용하며 실제 사건·인물·좌표를 다루지 않는다. Luvoire 엔진의 ``POLICIES/civilian_use.md`` v1.0(2026-04-23) 정책에 따라 국방, 예측치안, PSYOP, 비동의 실인물 시뮬, 미성년 합성 파이프라인 응용을 거부하며, 본 논문의 어떤 결과도 개인별 위험점수나 운영 의사결정에 사용되어서는 안 된다.
