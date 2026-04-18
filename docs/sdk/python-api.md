# Python Game SDK

The Python facade is intended for game servers or tooling scripts that want a stable high-level NPC API.

```python
from knoema.game import GameSession

session = GameSession(game_id="demo-village")
npc = session.create_npc(
    persona_file="sdk/python/examples/personas/shopkeeper.yaml",
    initial_relationships={"player": "neighbor"},
)
response = npc.interact(
    "asks whether the lantern market is ready",
    context={"location": "Harbor Village"},
)
print(response.text)
```

## Classes

- `GameSession`: owns game id, provider name, and NPC registry.
- `NPC`: exposes `interact(player_action, context)`.
- `NPCResponse`: returns `text`, `emotion`, `branch_flags`, and `raw` metadata.

The Phase 24 facade is local and deterministic by default. Provider-backed calls can be added behind the same surface later.

The repository-level `sdk.python.knoema_game` module is kept as a compatibility import for examples that vendor the SDK folder directly.
