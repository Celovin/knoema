# Tutorial 02 - Build Your First Knoema NPC In 15 Minutes

## Goal

Python Game SDK로 deterministic NPC를 만들고, player action, context, response text, emotion, branch flags를 확인한다.

## Audience

- 게임 개발자
- narrative designer
- Godot 또는 Unity 연동 전에 response contract를 검토하려는 팀

## Recording Setup

- Resolution: 1920x1080
- Frame rate: 60 fps
- Capture surfaces: editor, terminal, optional Godot window
- Cursor: visible, slow enough for code reading
- Audio: code explanation 중심

## Script

### 00:00 - 00:50 Opening

Screen: `docs/sdk/integration_patterns.md`.

Narration:
이번 영상에서는 Knoema의 Game SDK 표면을 사용해 첫 NPC를 만듭니다. 목표는 멋진 대사를 한 번 뽑는 것이 아니라, 게임 규칙에 연결 가능한 deterministic response contract를 확인하는 것입니다.

### 00:50 - 02:30 Persona File

Screen: `sdk/python/examples/personas/shopkeeper.yaml`.

Narration:
persona file에는 npc id, name, background, values, goals를 둡니다. 이 예제의 Mina는 항구 마을 축제 준비를 맡은 상점 주인입니다.

Code:

```yaml
npc_id: shopkeeper
name: Mina
background: Synthetic shopkeeper coordinating a lantern market stall.
values: [calm, trust, clear records]
goals: [answer the player consistently, remember local context]
```

### 02:30 - 05:30 Python Session

Screen: `sdk/python/examples/basic_npc.py`.

Code:

```python
from knoema.game import GameSession

session = GameSession(game_id='demo-village')
npc = session.create_npc(
    persona_file='sdk/python/examples/personas/shopkeeper.yaml',
    initial_relationships={'player': 'neighbor'},
)
response = npc.interact(
    'asks whether the lantern market is ready',
    context={'location': 'Harbor Village'},
)
print(response.text)
```

Narration:
GameSession은 게임 id와 provider를 갖고, create_npc는 persona와 초기 관계를 등록합니다. interact는 player action과 context를 받아 NPCResponse를 반환합니다.

### 05:30 - 08:20 Response Contract

Screen: Terminal output and `src/knoema/game.py`.

Narration:
응답은 `text`, `emotion`, `branch_flags`, `raw`로 나뉩니다. text는 UI에 보여줄 문장이고, emotion은 portrait나 animation state에 연결할 수 있습니다. branch flags는 quest와 narrative branch에 연결합니다. raw metadata는 디버깅과 replay에 사용합니다.

### 08:20 - 10:30 TypeScript Surface

Screen: `sdk/typescript/src/index.ts`.

Narration:
TypeScript SDK도 같은 개념을 유지합니다. Electron tooling이나 web-based game tools에서 같은 response contract를 먼저 검토할 수 있습니다.

### 10:30 - 12:40 Godot Surface

Screen: `sdk/godot-gdscript/knoema.gd`.

Narration:
Godot GDScript facade는 direct prototype용입니다. 실제 runtime 연결 전에도 NPC id, player action, context, response dictionary를 씬에서 다뤄볼 수 있습니다.

### 12:40 - 14:10 Safe Branching

Screen: Diagram or code comments.

Narration:
모델이 생성한 문장을 파싱해서 퀘스트를 진행하지 마세요. narrative branch는 branch flags처럼 구조화된 값으로 판정하는 편이 안전합니다.

### 14:10 - 15:00 Wrap

Screen: Game SDK docs.

Narration:
다음 영상에서는 연구용 scenario를 만들고, seed, config, log, report를 통해 재현 가능한 실험으로 정리합니다.

## YouTube Description

Knoema Game SDK로 첫 NPC를 만드는 15분 튜토리얼입니다. Python, TypeScript, Godot GDScript가 공유하는 response contract를 확인하고 branch flags를 게임 규칙에 연결하는 방식을 다룹니다.

Links:
- GitHub: https://github.com/Celovin/knoema
- Python SDK: https://github.com/Celovin/knoema/blob/main/docs/sdk/python-api.md
- TypeScript SDK: https://github.com/Celovin/knoema/blob/main/docs/sdk/typescript-api.md
- Godot SDK: https://github.com/Celovin/knoema/blob/main/docs/sdk/godot-api.md

