# Knoema Godot Adapter

Minimal Godot 4.2+ adapter scaffold for testing a single NPC chat loop against Knoema.

## Run

1. Install Godot 4.2 or newer.
2. Open this folder as a Godot project: `adapters/godot`.
3. Open `scenes/chat_demo.tscn` for the original UI stub, or `samples/tavern_demo/tavern_demo.tscn` for the tavern scene.
4. Press Run.
5. Type a message and press `Send`.

By default the demo uses a local deterministic fallback response, so it runs without a Python server. To call a Knoema HTTP server later, set `endpoint_url` in `scripts/knoema_client.gd`.

## Real engine run and export

`samples/tavern_demo/web_build/index.html` is a DOM simulation for the adapter call pattern. It is not a real Godot web export.

Open the actual Godot project from the command line with:

```bash
godot4 --path adapters/godot
```

After adding a `Web` export preset in the Godot editor, build a real export with:

```bash
godot4 --headless --path adapters/godot --export-release Web build/godot-tavern/index.html
```

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
