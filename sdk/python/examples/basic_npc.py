from __future__ import annotations

from pathlib import Path

from luvoire.game import GameSession

ROOT = Path(__file__).resolve().parent

session = GameSession(game_id="demo-village")
npc = session.create_npc(
    persona_file=ROOT / "personas" / "shopkeeper.yaml",
    initial_relationships={"player": "neighbor"},
)
response = npc.interact(
    "asks whether the lantern market is ready",
    context={"location": "Harbor Village", "time": "2026-06-01T18:00:00"},
)
print(response.text)
