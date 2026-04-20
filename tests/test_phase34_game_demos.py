from __future__ import annotations

from pathlib import Path


def test_phase34_godot_tavern_demo_assets_exist_and_reference_knoema_client() -> None:
    expected = [
        "adapters/godot/samples/tavern_demo/README.md",
        "adapters/godot/samples/tavern_demo/tavern_demo.tscn",
        "adapters/godot/samples/tavern_demo/scripts/tavern_demo.gd",
        "adapters/godot/samples/tavern_demo/scripts/tavern_player.gd",
        "adapters/godot/samples/tavern_demo/web_build/index.html",
        "adapters/godot/scripts/knoema_client.gd",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []

    scene = Path("adapters/godot/samples/tavern_demo/tavern_demo.tscn").read_text(encoding="utf-8")
    script = Path("adapters/godot/samples/tavern_demo/scripts/tavern_demo.gd").read_text(
        encoding="utf-8"
    )
    player = Path("adapters/godot/samples/tavern_demo/scripts/tavern_player.gd").read_text(
        encoding="utf-8"
    )
    client = Path("adapters/godot/scripts/knoema_client.gd").read_text(encoding="utf-8")
    web_build = Path("adapters/godot/samples/tavern_demo/web_build/index.html").read_text(
        encoding="utf-8"
    )

    assert 'path="res://samples/tavern_demo/scripts/tavern_demo.gd"' in scene
    assert "CharacterBody2D" in scene
    assert "DialogPanel" in scene
    assert "INTERACT_DISTANCE := 64.0" in script
    assert 'await client.ask(BJORN_AGENT_ID, clean_text, context_json)' in script
    assert "Input.get_vector" in player
    assert "player_action" in client
    assert "context_json" in client
    assert "WASD" in web_build
    assert "Bjorn" in web_build
    assert "DOM 시뮬레이션" in web_build
    assert "not a real engine export" in web_build


def test_phase34_unity_tavern_demo_assets_exist_and_extend_npc_agent_loop() -> None:
    expected = [
        "adapters/unity/Samples~/TavernDemo/Scenes/TavernDemo.unity",
        "adapters/unity/Samples~/TavernDemo/Scripts/TavernDemo.cs",
        "adapters/unity/Samples~/TavernDemo/Scripts/TavernPlayerController.cs",
        "adapters/unity/Samples~/TavernDemo/web_build/index.html",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []

    scene = Path("adapters/unity/Samples~/TavernDemo/Scenes/TavernDemo.unity").read_text(
        encoding="utf-8"
    )
    demo = Path("adapters/unity/Samples~/TavernDemo/Scripts/TavernDemo.cs").read_text(
        encoding="utf-8"
    )
    player = Path("adapters/unity/Samples~/TavernDemo/Scripts/TavernPlayerController.cs").read_text(
        encoding="utf-8"
    )
    web_build = Path("adapters/unity/Samples~/TavernDemo/web_build/index.html").read_text(
        encoding="utf-8"
    )

    assert "Tavern Demo Root" in scene
    assert "Bjorn" in scene
    assert "DialogCanvas" in scene
    assert "NPCAgent" in demo
    assert "interactionDistance = 64f" in demo
    assert "Input.GetAxisRaw" in player
    assert "WASD" in web_build
    assert "Bjorn" in web_build
    assert "DOM 시뮬레이션" in web_build
    assert "not a real engine export" in web_build


def test_phase34_docs_and_website_embed_both_browser_demos() -> None:
    docs = Path("docs/adapters/game_demos.md").read_text(encoding="utf-8")
    godot_readme = Path("adapters/godot/README.md").read_text(encoding="utf-8")
    unity_readme = Path("adapters/unity/README.md").read_text(encoding="utf-8")
    docs_page = Path("website/app/docs/page.tsx").read_text(encoding="utf-8")
    showcase = Path("website/app/showcase/page.tsx").read_text(encoding="utf-8")
    demos_page = Path("website/app/game-demos/page.tsx").read_text(encoding="utf-8")
    screenshots = [
        Path("docs/adapters/screenshots/godot-tavern-demo.png"),
        Path("docs/adapters/screenshots/unity-tavern-demo.png"),
    ]

    assert "uvicorn knoema.api.server:app" in docs
    assert "not real Godot or Unity engine exports" in docs
    assert "godot4 --path adapters/godot" in docs
    assert "TavernDemoBuild.BuildWebGL" in docs
    assert "screenshots/godot-tavern-demo.png" in docs
    assert "screenshots/unity-tavern-demo.png" in docs
    assert "not a real Godot web export" in godot_readme
    assert "--export-release Web build/godot-tavern/index.html" in godot_readme
    assert "not a real Unity WebGL export" in unity_readme
    assert "TavernDemoBuild.BuildWebGL" in unity_readme
    assert all(path.exists() for path in screenshots)
    assert "docs/adapters/game_demos.md" in docs_page
    assert "/game-demos" in showcase
    assert "srcDoc={godotDemoHtml}" in demos_page
    assert "srcDoc={unityDemoHtml}" in demos_page
