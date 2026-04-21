from __future__ import annotations

from knoema_bots.slack import build_blocks_for_command


def test_batch_nn_slack_blocks_are_demo_ready() -> None:
    blocks = build_blocks_for_command('knoema run "Village: ten agents" --ticks 2')

    assert blocks[0]["type"] == "header"
    assert blocks[0]["text"]["text"] == "Knoema run: Village: ten agents"
    assert blocks[1]["type"] == "section"
    assert "Action mix" in blocks[1]["text"]["text"]
    assert blocks[2]["type"] == "context"
