# Luvoire Unity SDK

Preview Unity package for driving NPC ticks through the Luvoire FastAPI runtime.

## Install

Use Unity Package Manager, choose **Add package from git URL**, and enter:

```text
https://github.com/Celovin/luvoire.git?path=unity-sdk/Packages/com.celovin.luvoire
```

For a manual install, copy `unity-sdk/Packages/com.celovin.luvoire` into your project's
`Packages` directory.

## Run The API Server

```bash
pip install -e ".[api]"
uvicorn luvoire.api.server:app --host 127.0.0.1 --port 8000
```

## Runtime Contract

`LuvoireClient.TickAsync(...)` sends this payload to `POST /simulate/tick`:

```json
{
  "session_id": "unity-demo",
  "agent_id": "guide",
  "player_action": "hello",
  "context_json": "{\"location\":\"Demo Village > Plaza\",\"agent_name\":\"Guide\"}"
}
```

The response includes `content`, `emotion`, `branch_flags`, and a nested simulator action. Memory
inspection uses `GET /agent/{id}/memory?session_id=unity-demo`; action injection uses
`POST /agent/{id}/action`.

## Known Limits

- Codex validates the HTTP contract and package metadata, but C# compilation still needs Unity.
- The Basic NPC sample is a YAML scene description, not a binary `.unity` scene.
- The package is preview-scoped; keep authored story beats in the game and use Luvoire for continuity-heavy NPC state.
