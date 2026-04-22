# LLM NPC 기억 설계 원칙 5가지

LLM NPC의 핵심은 말을 잘하는 것이 아니라 적절히 기억하는 것이다. 기억이 없으면 NPC는 매 장면 새로 태어난다. 기억이 과하면 중요하지 않은 로그까지 prompt를 채워 비용과 오류를 만든다. Luvoire는 이 문제를 단기 기억, 장기 기억, 관계 상태, 환경 맥락, 재현 가능한 로그로 나누어 다룬다.

첫 번째 원칙은 최근성과 중요도를 분리하는 것이다. 최근 사건은 대화 흐름에 중요하지만, 최근이라는 이유만으로 항상 장기적으로 중요하지는 않다. 반대로 오래된 약속이나 갈등은 시간이 지나도 캐릭터 행동에 영향을 줄 수 있다. Luvoire의 short-term memory는 현재 장면의 흐름을 유지하고, SQLite와 FAISS 기반 long-term memory는 검색 가능한 의미 기억을 관리한다.

두 번째 원칙은 검색 결과를 점수와 함께 남기는 것이다. 모델에게 어떤 기억이 전달됐는지 개발자가 볼 수 없다면 디버깅이 불가능하다. Luvoire의 scored retrieval은 semantic score, temporal score, importance score, final rerank score를 분리해 보여준다. 이렇게 하면 NPC가 왜 특정 사건을 떠올렸는지, 어떤 가중치가 영향을 줬는지 추적할 수 있다.

세 번째 원칙은 관계를 prompt 안의 설명문으로만 두지 않는 것이다. 플레이어가 한 NPC를 여러 번 도왔거나 속였다는 사실은 문장으로만 남기기보다 graph state로 유지하는 편이 낫다. RelationshipGraph는 trust, familiarity, interaction weight를 방향성 있는 edge로 기록한다. 이 값은 대사 tone, 협조 여부, 정보 공개 수준 같은 게임 규칙에 연결될 수 있다.

네 번째 원칙은 기억과 환경을 섞지 않는 것이다. NPC가 알고 있는 사실과 현재 장면의 조건은 다르다. 비가 오는지, 어느 장소인지, 지금 시간이 밤인지 같은 정보는 environment context에서 들어와야 한다. 기억 저장소에 날씨와 위치를 무작정 쌓으면 검색 노이즈가 생긴다. Luvoire는 Environment를 별도 상태로 두어 현재 tick에서 필요한 context를 제공한다.

다섯 번째 원칙은 모든 실험을 로그로 되돌릴 수 있게 하는 것이다. LLM 기반 시스템은 재현성이 약하다는 비판을 받기 쉽다. Luvoire는 deterministic local client, seed propagation, YAML config, JSONL export를 조합해 같은 설정의 결과를 다시 확인할 수 있게 한다. 연구자는 실험 조건을 남길 수 있고, 게임 개발자는 회귀 테스트를 만들 수 있다.

좋은 NPC 기억은 무한 저장소가 아니다. 무엇을 잊을지, 무엇을 요약할지, 어떤 기억을 다시 꺼낼지 정하는 구조다. 예를 들어 상점 주인 NPC가 플레이어의 첫 방문, 이전 거래, 축제 준비 요청을 모두 기억하더라도, 전투 장면에서 그 모든 정보가 필요하지는 않다. 장면의 목적과 관계 상태에 맞는 기억만 꺼내야 한다.

Luvoire의 MemorySummarizer는 많은 이벤트를 적은 수의 semantic memory로 압축하는 테스트를 포함한다. 이 압축은 단순한 저장 공간 절약이 아니다. 게임 작가와 연구자가 이해할 수 있는 수준으로 사건을 정리하고, 이후 검색 품질을 안정화하는 과정이다.

실제 제작에서는 처음부터 복잡한 memory policy를 만들 필요가 없다. 먼저 deterministic local mode로 캐릭터 2명과 짧은 장면을 실행한다. 다음으로 관계 edge를 확인한다. 그다음 long-term retrieval 결과가 의도한 사건을 꺼내는지 본다. 마지막으로 branch flags를 게임 규칙에 연결한다. 이 순서가 비용과 불확실성을 줄인다.

LLM NPC가 자연스럽게 느껴지는 순간은 모델이 긴 문장을 생성할 때가 아니다. 플레이어가 이전에 한 일을 알고, 현재 장소에 맞게 반응하며, 관계 변화가 대사와 행동에 작게 묻어날 때다. 기억 설계의 목표는 바로 그 작은 일관성을 반복 가능하게 만드는 것이다.

## Links

- GitHub: https://github.com/Celovin/luvoire
- Playground: https://huggingface.co/spaces/celovin/luvoire-playground
- Memory architecture: https://github.com/Celovin/luvoire/blob/main/docs/architecture.md
- Reproducibility report: https://github.com/Celovin/luvoire/blob/main/docs/reports/reproducibility.md
- Python SDK: https://github.com/Celovin/luvoire/blob/main/docs/sdk/python-api.md
