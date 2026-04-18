from __future__ import annotations

import json
from pathlib import Path

from knoema.game import GameSession
from sdk.python import GameSession as CompatGameSession
from sdk.python.knoema_game import GameSession as LegacyGameSession


def test_phase24_sdk_files_exist() -> None:
    expected = [
        "sdk/python/knoema_game.py",
        "sdk/__init__.py",
        "sdk/python/__init__.py",
        "sdk/python/examples/basic_npc.py",
        "sdk/python/examples/personas/shopkeeper.yaml",
        "sdk/typescript/package.json",
        "sdk/typescript/src/index.ts",
        "sdk/typescript/examples/basic-npc.ts",
        "sdk/godot-gdscript/knoema.gd",
        "sdk/godot-gdscript/examples/basic_npc.gd",
        "docs/sdk/python-api.md",
        "docs/sdk/typescript-api.md",
        "docs/sdk/godot-api.md",
        "docs/sdk/integration_patterns.md",
        "src/knoema/game.py",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase24_python_sdk_creates_and_interacts_with_npc() -> None:
    assert CompatGameSession is GameSession
    assert LegacyGameSession is GameSession

    session = GameSession(game_id="demo-village")
    npc = session.create_npc(
        persona_file="sdk/python/examples/personas/shopkeeper.yaml",
        initial_relationships={"player": "neighbor"},
    )
    response = npc.interact("asks about the lantern market", context={"location": "Harbor Village"})

    assert npc.npc_id == "shopkeeper"
    assert response.text == (
        "Mina responds to asks about the lantern market at Harbor Village as a neighbor."
    )
    assert response.emotion == "neutral"
    assert response.branch_flags == ["location:Harbor Village", "relationship:neighbor"]
    assert json.loads(session.to_json())["npc_count"] == 1


def test_phase24_typescript_package_declares_public_api() -> None:
    package = json.loads(Path("sdk/typescript/package.json").read_text(encoding="utf-8"))
    source = Path("sdk/typescript/src/index.ts").read_text(encoding="utf-8")

    assert package["name"] == "@celovin/knoema-game"
    assert "export class GameSession" in source
    assert "export class NPC" in source
    assert "NPCResponse" in source


def test_phase24_godot_facade_matches_response_contract() -> None:
    source = Path("sdk/godot-gdscript/knoema.gd").read_text(encoding="utf-8")

    assert "class_name KnoemaGameSession" in source
    assert "func create_npc" in source
    assert "func interact" in source
    assert '"branch_flags"' in source
