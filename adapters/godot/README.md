# Knoema Godot Adapter

Minimal Godot 4.2+ adapter scaffold for testing a single NPC chat loop against Knoema.

## Run

1. Install Godot 4.2 or newer.
2. Open this folder as a Godot project: `adapters/godot`.
3. Open `scenes/chat_demo.tscn` for the original UI stub, or `samples/tavern_demo/tavern_demo.tscn` for the tavern scene.
4. Press Run.
5. Type a message and press `Send`.

By default the demo uses a local deterministic fallback response, so it runs without a Python server. To call a Knoema HTTP server later, set `endpoint_url` in `scripts/knoema_client.gd`.

## Files

- `project.godot`: demo project configuration.
- `scenes/chat_demo.tscn`: one-scene chat demo.
- `samples/tavern_demo/tavern_demo.tscn`: 2D tavern sample with proximity-triggered dialog.
- `samples/tavern_demo/web_build/index.html`: browser mirror of the tavern loop.
- `scripts/npc.gd`: UI controller for player input and NPC output.
- `scripts/knoema_client.gd`: HTTP/fallback client wrapper.
- `addons/knoema/plugin.cfg`: editor plugin registration.

## Protocol Draft

Request:

```json
{
  "session_id": "demo-session",
  "agent_id": "school_nurse",
  "message": "Hello"
}
```

Response:

```json
{
  "content": "I remember our last conversation."
}
```
