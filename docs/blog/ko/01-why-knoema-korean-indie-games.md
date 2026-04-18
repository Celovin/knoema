# 한국 인디 게임에 왜 Knoema가 필요한가

한국 인디 게임 팀이 AI NPC를 검토할 때 가장 먼저 부딪히는 문제는 모델 호출 자체가 아니다. 대사를 한 번 생성하는 일은 이미 쉬워졌다. 어려운 부분은 NPC가 어제의 대화를 기억하고, 플레이어와의 관계 변화를 유지하며, 같은 상황을 다시 실행했을 때 개발자가 원인을 추적할 수 있게 만드는 일이다. Knoema는 이 지점을 게임 엔진 밖의 독립 런타임으로 다룬다.

일반적인 프로토타입은 캐릭터 설정을 긴 prompt에 붙이고 매번 전체 맥락을 모델에 보낸다. 이 방식은 빠르게 시작할 수 있지만, 플레이 시간이 길어질수록 비용과 일관성 문제가 커진다. 같은 캐릭터가 장면마다 다른 가치관으로 말하거나, 플레이어가 이미 해결한 갈등을 다시 처음 보는 것처럼 반응한다. Knoema의 목표는 대사를 멋지게 꾸미는 것이 아니라, NPC의 기억과 관계를 게임 시스템이 다룰 수 있는 상태로 정리하는 것이다.

Knoema의 기본 단위는 persona, memory, relationship, environment, emotion, decision이다. persona는 캐릭터의 배경과 가치관을 담고, memory는 단기 기억과 장기 검색을 나눈다. relationship은 플레이어와 NPC, NPC와 NPC 사이의 신뢰와 친밀도를 관리한다. environment는 장소와 시간, 최근 이벤트를 제공한다. emotion은 현재 반응의 정서적 방향을 압축한다. decision은 이 상태들을 모아 행동과 대사를 만든다.

인디 팀에게 중요한 장점은 deterministic local mode다. 모든 빌드에서 실제 모델 API를 호출해야 한다면 테스트와 데모 비용이 곧바로 부담이 된다. Knoema는 local client와 고정 seed를 사용해 같은 입력에서 같은 로그를 얻을 수 있게 한다. 이 방식은 기획자가 장면을 재현하고, 프로그래머가 회귀 테스트를 만들고, 작가가 대사 흐름을 검토하는 데 유리하다.

Godot과 Unity를 모두 고려한 점도 현실적인 이유가 있다. 한국 인디 개발 현장에서는 Godot으로 빠르게 실험하는 팀과 Unity 기반 제작 파이프라인을 유지하는 팀이 공존한다. Knoema는 특정 엔진의 씬 구조를 강제하지 않고, HTTP payload와 SDK response contract를 통해 연결된다. 게임 쪽에서는 NPC id, player action, location 같은 정보를 넘기고, 런타임은 text, emotion, branch flags, raw metadata를 돌려준다.

branch flags는 작은 기능처럼 보이지만 게임 제작에서는 중요하다. 모델이 생성한 문장을 그대로 퀘스트 상태로 쓰면 위험하다. 대신 응답 옆에 deterministic flag를 붙이면, 게임 시스템은 안전하게 분기 조건을 판정할 수 있다. 플레이어가 상점 주인에게 축제 준비를 물었고 관계가 neighbor라면, `location:Harbor Village`와 `relationship:neighbor` 같은 값이 기록된다. 대사는 자연스럽게 바뀌어도 분기 판정은 안정적으로 유지된다.

Knoema가 모든 팀에 필요한 것은 아니다. 짧은 대화형 장면이나 고정 대사 중심 게임이라면 기존 dialogue tree가 더 단순하다. 하지만 장기 플레이, NPC 간 관계 변화, 연구형 시뮬레이션, 플레이어 선택의 누적 결과를 다루려는 팀이라면 기억과 로그를 별도 시스템으로 관리하는 편이 낫다.

시작 경로는 가볍다. GitHub 저장소를 clone하고 Python package를 editable mode로 설치한 뒤, `examples/03_game_npc_demo.ipynb` 또는 `sdk/python/examples/basic_npc.py`를 실행하면 된다. 브라우저에서 먼저 감을 보고 싶다면 Hugging Face Playground의 replay-only mode로 API 키 없이 흐름을 확인할 수 있다.

Knoema는 게임의 재미를 자동으로 만들어주는 도구가 아니다. 대신 기억, 관계, 상태, 재현성을 엔진 바깥에서 일관되게 유지해 주는 기반이다. 인디 팀에게 필요한 것은 거대한 AI 플랫폼이 아니라, 작은 장면부터 안전하게 붙일 수 있는 투명한 런타임이다.

## Links

- GitHub: https://github.com/Celovin/knoema
- Playground: https://huggingface.co/spaces/Celovin/knoema-playground
- Game SDK: https://github.com/Celovin/knoema/blob/main/docs/sdk/integration_patterns.md
- Unity adapter: https://github.com/Celovin/knoema/tree/main/adapters/unity

