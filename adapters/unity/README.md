# Knoema Unity Adapter

Unity 2022.3 LTS package scaffold for connecting a game NPC to a local or hosted Knoema runtime.

## Install

Open Unity Package Manager, choose **Add package from git URL**, and enter:

```text
https://github.com/Celovin/knoema.git?path=adapters/unity
```

## Runtime

- `Runtime/KnoemaConfig.cs`: ScriptableObject settings for endpoint URL, session ID, and fallback mode.
- `Runtime/KnoemaClient.cs`: coroutine-based HTTP client with deterministic local fallback.
- `Runtime/NPCAgent.cs`: MonoBehaviour wrapper for game NPC interactions.

Default endpoint:

```text
http://localhost:8000/interact
```

The fallback path returns a deterministic response when no endpoint is configured, when `UseLocalFallback`
is enabled, or when the HTTP request fails. This keeps the sample scene runnable without a Python server.

## Protocol Draft

Request:

```json
{
  "session_id": "unity-demo",
  "agent_id": "guide",
  "player_action": "Hello",
  "context_json": "{\"location\":\"sample scene\"}"
}
```

Response:

```json
{
  "content": "I remember that and update my next step.",
  "emotion": "calm",
  "branch_flags": ["continue_dialogue"]
}
```

## Sample

Import `Samples~/BasicNPC` from Package Manager. The sample contains:

- `Scenes/BasicNPC.unity`: placeholder scene for a one-NPC chat demo.
- `Scripts/BasicNPCDemo.cs`: small UI controller using `NPCAgent.Interact(...)`.

## Unity Test Runner

The package includes an Editor test scaffold under `Tests/Editor`. In Unity, open **Window > General > Test Runner**, select **EditMode**, then run the Knoema tests.
