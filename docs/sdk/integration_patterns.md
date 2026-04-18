# Game SDK Integration Patterns

## Server-Authoritative NPCs

Run `GameSession` on the game server, store NPC ids in your game state, and persist interaction logs after each player action.

## Local Prototype Mode

Use the deterministic local facade during prototyping. This makes demos testable without API keys and keeps CI independent from model providers.

## Engine Adapters

- Python: use `knoema.game` for installed packages or `sdk/python/knoema_game.py` when vendoring the SDK folder directly.
- TypeScript: use `sdk/typescript/src/index.ts` for web or Electron tooling.
- Godot: use `sdk/godot-gdscript/knoema.gd` for direct GDScript experiments.

## Response Contract

Each facade returns:

- `text`: player-facing NPC response.
- `emotion`: compact emotional state label.
- `branch_flags`: deterministic flags for quest or narrative state.
- `raw`: debug metadata that can be logged or inspected.
