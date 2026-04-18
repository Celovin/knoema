# Godot 4에서 Knoema 붙이기

Godot에서 LLM NPC를 붙일 때 가장 단순한 구조는 게임 씬과 AI 런타임을 분리하는 것이다. Godot은 player action, npc id, location 같은 게임 상태를 보내고, Knoema는 response text, emotion, branch flags, raw metadata를 돌려준다. 이렇게 나누면 게임 루프는 가볍게 유지되고, 기억과 관계 로직은 Python 쪽에서 테스트할 수 있다.

Knoema 저장소에는 두 가지 Godot 경로가 있다. `adapters/godot/`은 Godot 4 프로젝트 스캐폴드와 client 구조를 제공한다. `sdk/godot-gdscript/knoema.gd`는 더 가벼운 GDScript facade다. 처음 실험할 때는 GDScript facade로 response contract를 익히고, 실제 HTTP runtime이 필요해지면 adapter 쪽으로 넘어가는 흐름이 좋다.

먼저 Python 패키지를 설치한다. 저장소 루트에서 `pip install -e .[dev]`를 실행하면 Knoema package와 테스트 의존성을 사용할 수 있다. 모델 API 없이도 deterministic local client로 demo를 돌릴 수 있으므로, Godot 연동 전 Python 예제가 제대로 실행되는지 확인한다.

다음으로 Godot 씬에서는 NPC controller가 player action을 모아 runtime에 보낼 payload를 만든다. payload에는 최소한 npc id, player action, location, time이 들어가면 된다. 더 정교한 게임에서는 current quest id, player reputation, nearby agents 같은 값을 context에 추가할 수 있다. 중요한 점은 모든 값을 자연어 prompt에만 묻지 않는 것이다. 게임 규칙으로 써야 하는 값은 구조화된 필드로 남긴다.

응답은 네 가지 필드를 기준으로 처리한다. `text`는 플레이어에게 보여줄 문장이다. `emotion`은 animation state나 portrait variant에 연결할 수 있는 compact label이다. `branch_flags`는 퀘스트와 narrative branch 판정에 쓰인다. `raw`는 디버깅과 replay를 위한 metadata다. 대사는 바뀔 수 있지만 branch flag는 deterministic하게 유지하는 것이 좋다.

예를 들어 상점 주인 NPC가 축제 준비를 묻는 플레이어에게 답한다면 text는 자연스럽게 출력하고, branch flag는 `location:Harbor Village`, `relationship:neighbor`처럼 남길 수 있다. Godot 쪽 quest script는 이 flag를 보고 다음 대화 선택지를 열거나 닫는다. 모델이 생성한 문장을 직접 파싱해 퀘스트를 진행하는 방식은 피하는 것이 안전하다.

개발 중에는 로그를 반드시 저장해야 한다. Knoema는 JSONL export를 지원한다. Godot에서 특정 장면이 이상하게 반응했다면, 같은 config와 seed로 Python runtime에서 재현해 볼 수 있다. 이 구조가 있어야 작가, 기획자, 프로그래머가 같은 사건을 놓고 대화할 수 있다.

성능 측면에서는 처음부터 모든 NPC를 live LLM으로 돌리지 않는 편이 낫다. 중요한 NPC만 provider-backed response를 쓰고, 배경 NPC는 deterministic 또는 cached response를 사용한다. 장면 단위 tick을 조절하고, 긴 memory retrieval을 필요한 순간에만 수행하면 비용을 통제할 수 있다.

Godot 연동의 성공 기준은 화려한 대사가 아니다. 같은 장면을 다시 실행했을 때 원인을 알 수 있고, NPC 상태가 게임 규칙과 충돌하지 않으며, 플레이어 선택이 작은 관계 변화로 누적되는 것이다. Knoema는 이 기준을 만족시키기 위한 runtime과 문서, 테스트를 공개 저장소에 함께 둔다.

## Links

- GitHub: https://github.com/Celovin/knoema
- Godot adapter: https://github.com/Celovin/knoema/tree/main/adapters/godot
- Godot SDK: https://github.com/Celovin/knoema/blob/main/docs/sdk/godot-api.md
- Game NPC notebook: https://github.com/Celovin/knoema/blob/main/examples/03_game_npc_demo.ipynb

