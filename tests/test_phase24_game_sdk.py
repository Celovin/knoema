from __future__ import annotations

import json
from pathlib import Path

import pytest

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
        "sdk/typescript/package-lock.json",
        "sdk/typescript/tsconfig.json",
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


def test_phase24_python_sdk_validates_and_copies_game_inputs() -> None:
    session = GameSession(game_id=" demo-village ", provider=" local ")
    context = {"location": " Harbor Village "}
    npc = session.create_npc(
        persona={"name": " Mina Park "},
        initial_relationships={"player": " neighbor "},
    )

    response = npc.interact(" asks about the lantern market ", context=context)
    context["location"] = "Changed"

    assert session.game_id == "demo-village"
    assert session.provider == "local"
    assert npc.npc_id == "mina-park"
    assert npc.name == "Mina Park"
    assert response.text == (
        "Mina Park responds to asks about the lantern market at Harbor Village as a neighbor."
    )
    assert response.raw["context"]["location"] == " Harbor Village "


def test_phase24_python_sdk_rejects_blank_required_inputs() -> None:
    with pytest.raises(ValueError, match="game_id"):
        GameSession(game_id=" ")

    session = GameSession(game_id="demo-village")

    with pytest.raises(ValueError, match="persona name"):
        session.create_npc(persona={"name": " "})

    npc = session.create_npc(persona={"name": "Mina"})
    with pytest.raises(ValueError, match="player_action"):
        npc.interact(" ")


def test_phase24_typescript_package_declares_public_api() -> None:
    package = json.loads(Path("sdk/typescript/package.json").read_text(encoding="utf-8"))
    tsconfig = json.loads(Path("sdk/typescript/tsconfig.json").read_text(encoding="utf-8"))
    source = Path("sdk/typescript/src/index.ts").read_text(encoding="utf-8")

    assert package["name"] == "@celovin/knoema-game"
    assert package["scripts"]["check"] == "tsc --project tsconfig.json --noEmit"
    assert tsconfig["compilerOptions"]["strict"] is True
    assert tsconfig["compilerOptions"]["target"] == "ES2020"
    assert "export class GameSession" in source
    assert "export class NPC" in source
    assert "NPCResponse" in source
    assert "function requiredText" in source
    assert "copyUnknownRecord" in source
    assert "copyStringRecord" in source


def test_phase24_godot_facade_matches_response_contract() -> None:
    source = Path("sdk/godot-gdscript/knoema.gd").read_text(encoding="utf-8")

    assert "class_name KnoemaGameSession" in source
    assert "func create_npc" in source
    assert "func interact" in source
    assert '"branch_flags"' in source
    assert "npcs.has(resolved_npc_id)" in source
    assert "duplicate(true)" in source
    assert "npc_not_found" in source
    assert '"error:%s"' in source
