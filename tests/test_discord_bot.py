from __future__ import annotations

from luvoire_bots.discord import build_embed_for_command


def test_batch_nn_discord_embed_payload_is_demo_ready() -> None:
    embed = build_embed_for_command('luvoire run "Dorm: two agents" --ticks 2')

    assert embed["title"] == "Luvoire run: Dorm: two agents"
    assert embed["color"] == 0x2F855A
    assert any(field["name"] == "Action mix" for field in embed["fields"])
    assert "Ticks" in {field["name"] for field in embed["fields"]}
