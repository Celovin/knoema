# Unity SDK

The preview Unity SDK packages a small HTTP client, one `KnoemaNPC` component, DTO models, and an
Editor settings window. It is designed for Unity 2022.3 LTS and the FastAPI runtime exposed by
`knoema.api.server`.

## Install

Install from Unity Package Manager with a Git URL:

```text
https://github.com/Celovin/knoema.git?path=unity-sdk/Packages/com.celovin.knoema
```

For a manual install, copy `unity-sdk/Packages/com.celovin.knoema` into the host game's `Packages`
directory.

## Start The Runtime

```bash
pip install -e ".[api]"
uvicorn knoema.api.server:app --host 127.0.0.1 --port 8000
```

Set `KNOEMA_API_KEY` only when you want bearer-token protection. If it is set, pass the same token to
`KnoemaClient` or the `KnoemaNPC` component.

## Minimum Scene

1. Add a GameObject named `Guide`.
2. Attach `KnoemaNPC`.
3. Set `Base URL` to `http://localhost:8000`.
4. Set `Session ID` to `unity-demo`.
5. Set `Agent ID` to `guide`.
6. Set `Context JSON` to `{"location":"Demo Village > Plaza","agent_name":"Guide"}`.

The package includes `Samples~/BasicNPC/BasicNPC.scene.yaml` as a text scene contract so the repository
can validate the sample without a Unity editor.

## HTTP Contract

`KnoemaClient.TickAsync(...)` sends:

```json
{
  "session_id": "unity-demo",
  "agent_id": "guide",
  "player_action": "asks about the lantern market",
  "context_json": "{\"location\":\"Demo Village > Plaza\",\"agent_name\":\"Guide\"}"
}
```

to:

```text
POST /simulate/tick
```

The response contains `content`, `emotion`, `branch_flags`, and an `action` object with
`action_type`, `target`, `content`, `location`, `timestamp`, and `metadata`.

Memory inspection:

```text
GET /agent/{id}/memory?session_id=unity-demo
```

Action injection:

```text
POST /agent/{id}/action
```

## Known Limitations

- Contract tests verify the Python API payloads and UPM metadata; C# compilation still needs Unity.
- The sample scene is YAML, not a binary `.unity` scene.
- The SDK is preview-scoped and intended for continuity-heavy NPC interactions, not full authored-story replacement.
