# 위험 시나리오 리플레이의 윤리 경계와 안전장치

Knoema의 public-safety track은 실제 사람을 평가하거나 미래 사건을 판정하는 도구가 아니다. 저장소의 예제는 fictional, synthetic, non-identifying scenario replay를 기준으로 한다. 이 구분은 문구상의 방어가 아니라 시스템 설계의 출발점이다. 사회적 위험을 다루는 시뮬레이션은 연구 목적이 분명하고, 식별 가능한 개인이나 집단에 해를 주지 않는 범위 안에서만 다뤄야 한다.

첫 번째 경계는 실제 개인을 넣지 않는 것이다. 이름, 얼굴, 학교, 주소, 직장, 사건 번호처럼 특정인을 떠올리게 하는 정보는 scenario input이 되어서는 안 된다. Knoema의 DSL validator는 identifiable subject를 거부하는 방향으로 설계되어 있다. 연구자는 synthetic persona를 만들고, 실제 사건의 복사본이 아니라 구조적 요인과 상호작용 패턴을 추상화해야 한다.

두 번째 경계는 점수화하지 않는 것이다. 사람에게 risk score를 매기거나, 특정 인물을 의심 대상으로 분류하거나, 처벌 가능성을 계산하는 방향은 허용되지 않는다. Knoema가 다루는 것은 fictional replay와 prevention-oriented analysis다. 예를 들어 갈등이 커지는 조건을 비교하거나, 중재 이벤트를 넣었을 때 관계 변화가 어떻게 달라지는지 보는 식이다.

세 번째 경계는 결과를 예언처럼 쓰지 않는 것이다. LLM agent simulation은 가능성을 탐색하는 도구일 수 있지만 현실 세계의 판정기가 아니다. 모델 응답은 훈련 데이터와 prompt, 설정에 영향을 받는다. 따라서 결과는 정책 결정이나 개인 판단의 근거가 아니라, 연구 가설을 정리하고 토론을 돕는 보조 자료로만 다뤄야 한다.

네 번째 경계는 로그 공개 범위다. synthetic log라 해도 연구 맥락과 결합되면 오해될 수 있다. 공개 문서에는 사용한 config, seed, guardrail, validator 결과를 함께 남겨야 한다. Knoema는 JSONL 로그와 report를 연결해 어떤 조건에서 결과가 나왔는지 추적할 수 있게 한다. 모호한 그래프만 공개하는 방식은 피한다.

다섯 번째 경계는 실패 사례를 숨기지 않는 것이다. validator가 거부한 scenario, 측정하지 않은 baseline, 모델 호출 없이 replay-only로 제한한 demo는 모두 연구 품질의 일부다. Knoema의 benchmark 문서는 외부 수치를 임의로 만들지 않고 `not-measured`로 남긴다. 안전한 시스템은 할 수 없는 일을 명확히 말해야 한다.

실무적으로는 scenario 작성 단계에서 체크리스트를 둔다. persona는 synthetic인지 확인한다. 장소와 사건은 특정 실제 사건을 재구성하지 않는지 본다. 목적 문구가 prediction, profiling, scoring으로 흐르지 않는지 검사한다. 출력은 개인 식별이나 의심 대상 추천으로 해석될 여지가 없는지 검토한다.

Knoema의 DSL은 연구자가 이 원칙을 반복 적용할 수 있게 돕는다. YAML scenario를 작성하면 validator가 구조와 금지 범위를 확인한다. IRB checklist note를 남기고, report에는 방법과 제한을 같이 적는다. 이 절차는 속도를 늦추는 장치가 아니라 public-safety research가 신뢰를 얻기 위한 최소 조건이다.

위험 시나리오를 다루는 기술은 조심스럽게 설계되어야 한다. 강한 주장을 하기보다, synthetic replay에서 어떤 변수와 상호작용이 나타나는지 투명하게 보여주는 편이 낫다. Knoema의 원칙은 단순하다. 실제 사람을 평가하지 않는다. 미래를 단정하지 않는다. 재현 가능한 연구 artifact로만 말한다.

## Links

- GitHub: https://github.com/Celovin/knoema
- Scenario DSL tutorial: https://github.com/Celovin/knoema/blob/main/docs/dsl/tutorial.md
- Scenario DSL reference: https://github.com/Celovin/knoema/blob/main/docs/dsl/reference.md
- Reproducibility report: https://github.com/Celovin/knoema/blob/main/docs/reports/reproducibility.md

