# Game Integration Guide

Use the game SDK when you need a stable NPC contract before committing to a hosted dialogue stack.

## Current Paths

- Python package facade: `knoema.game.GameSession`
- TypeScript package scaffold: `sdk/typescript`
- Godot GDScript facade: `sdk/godot-gdscript/knoema.gd`
- Godot adapter scaffold: `adapters/godot`
- Unity Package Manager scaffold: `adapters/unity`
- Unreal Engine 5 plugin scaffold: `adapters/unreal`

## Minimal Python NPC

```python
from knoema.game import GameSession

session = GameSession(game_id='demo-village')
npc = session.create_npc(
    persona_file='sdk/python/examples/personas/shopkeeper.yaml',
    initial_relationships={'player': 'neighbor'},
)

response = npc.interact(
    'asks about the lantern market',
    context={'location': 'Harbor Village'},
)
print(response.text)
```

## Integration Contract

The response contract intentionally starts small:

- `text`: player-facing NPC response.
- `emotion`: coarse current emotion label.
- `branch_flags`: deterministic tags the game can use for quests, analytics, or test assertions.
- `raw`: structured context for debugging.

## Recommended Flow

1. Prototype NPC state with deterministic local responses.
2. Add memory and relationship tests around the behavior you need.
3. Connect the SDK facade to engine-specific UI or behavior-tree code.
4. Add provider-backed dialogue only after the deterministic contract is stable.

For regressions, export JSONL logs from the simulator or game server boundary and replay the same config, seed, and player-facing action sequence before changing prompts or provider settings.

See also `docs/sdk/integration_patterns.md`.
