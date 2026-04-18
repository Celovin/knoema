# 학술 연구에서 LLM 에이전트 시뮬레이션을 재현 가능하게 만드는 방법

LLM 에이전트 시뮬레이션은 흥미로운 현상을 보여주기 쉽지만, 연구 도구로 인정받으려면 재현성이 필요하다. 어떤 persona가 있었는지, 어떤 환경에서 시작했는지, 어떤 seed를 썼는지, 어떤 로그가 생성됐는지, 결과 표가 어떻게 계산됐는지를 남겨야 한다. Knoema는 이 과정을 연구 workflow의 기본값으로 둔다.

첫 번째 구성 요소는 YAML config다. 실험 조건이 코드 안에 흩어져 있으면 재실행이 어렵다. Knoema의 CLI와 Scenario DSL은 agents, environment, duration, tick, language, output path 같은 값을 명시적으로 기록한다. 연구자는 config 파일을 논문 보조 자료로 제공할 수 있고, 동료 연구자는 같은 입력으로 실행해 결과를 비교할 수 있다.

두 번째 구성 요소는 seed propagation이다. seed가 persona 생성, environment event, local decision에 일관되게 전달되지 않으면 deterministic run이 깨진다. Knoema의 reproducibility test suite는 같은 seed에서 반복 실행한 로그와 canonical memory가 bit-for-bit로 일치하는지 확인한다. 이 테스트는 단순한 품질 보증이 아니라 연구 주장의 기반이다.

세 번째 구성 요소는 JSONL log다. 시뮬레이션 결과를 화면에만 보여주면 검증할 수 없다. JSONL은 각 tick의 action, agent, target, content, timestamp를 행 단위로 남긴다. 이후 dashboard, notebook, benchmark script가 같은 log를 읽어 분석한다. 시각화와 원본 로그가 분리되지 않기 때문에 결과 추적이 쉬워진다.

네 번째 구성 요소는 benchmark report다. Knoema는 50-agent village experiment와 formal benchmark report를 저장소에 포함한다. 여기에는 raw JSONL, summary markdown, SVG figures, PDF report가 함께 있다. 중요한 점은 외부 프레임워크와 비교할 때 측정하지 않은 값을 만들지 않는다는 것이다. 측정하지 않은 항목은 `not-measured`로 남긴다.

다섯 번째 구성 요소는 public safety guardrail이다. 사회적 시나리오를 연구할 때는 실제 개인을 식별하거나 평가하는 방향으로 흐르면 안 된다. Knoema의 Scenario DSL은 synthetic persona와 fictional replay를 기준으로 하고, disallowed purpose phrase와 identifiable subject를 validator에서 걸러낸다. 연구는 예방과 재현 실험의 범위 안에서 설계되어야 한다.

실험을 준비하는 순서는 단순하다. 먼저 sample scenario를 복사해 연구 질문에 맞는 synthetic setting으로 바꾼다. 다음으로 CLI dry run으로 config를 확인한다. 그다음 deterministic local client로 로그를 생성한다. 마지막으로 dashboard와 notebook에서 memory retrieval, relationship dynamics, branching count를 확인한다.

논문이나 기술 보고서에는 코드 링크만 넣는 것으로 충분하지 않다. 실행 명령, config hash, seed, output path, commit hash, report generation script를 함께 남겨야 한다. Knoema는 이 요소들을 한 저장소 안에 모아 연구자가 빠뜨리기 쉬운 재현성 문서를 보강한다.

LLM 기반 연구 도구는 매력적인 demo와 엄격한 실험 사이의 간격이 크다. Knoema의 방향은 demo를 숨기는 것이 아니라, demo를 재현 가능한 artifact로 바꾸는 것이다. 연구자가 결과를 믿기 위해 필요한 것은 멋진 스크린샷보다 다시 실행 가능한 조건과 검증 가능한 로그다.

## Links

- GitHub: https://github.com/Celovin/knoema
- Reproducibility report: https://github.com/Celovin/knoema/blob/main/docs/reports/reproducibility.md
- Formal benchmark report: https://github.com/Celovin/knoema/blob/main/benchmarks/formal_report/report.pdf
- Scenario DSL tutorial: https://github.com/Celovin/knoema/blob/main/docs/dsl/tutorial.md

