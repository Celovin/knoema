# Tavern Demo

Minimal Godot 4 tavern sample for a one-NPC Luvoire loop.

## Run in Godot

1. Open `adapters/godot` as the Godot project root.
2. Open `samples/tavern_demo/tavern_demo.tscn`.
3. Press Play.
4. Move with `W`, `A`, `S`, `D`.
5. Walk within 64px of Bjorn and type an order.

The sample uses `res://scripts/luvoire_client.gd` and defaults to replay-only fallback so it works without a running API server.

## Browser Build

`web_build/index.html` mirrors the same tavern interaction in a static browser page for quick review.
