"""Phase 7 tests for the Godot adapter stub."""

from __future__ import annotations

from pathlib import Path

GODOT_ROOT = Path("adapters/godot")


def test_godot_adapter_expected_files_exist() -> None:
    expected = [
        "project.godot",
        "README.md",
        "scenes/chat_demo.tscn",
        "scripts/npc.gd",
        "scripts/luvoire_client.gd",
        "addons/luvoire/plugin.cfg",
        "addons/luvoire/plugin.gd",
    ]

    missing = [path for path in expected if not (GODOT_ROOT / path).exists()]

    assert missing == []


def test_godot_project_points_to_chat_demo_scene() -> None:
    project = (GODOT_ROOT / "project.godot").read_text(encoding="utf-8")

    assert 'run/main_scene="res://scenes/chat_demo.tscn"' in project
    assert 'LuvoireClient="*res://scripts/luvoire_client.gd"' in project


def test_godot_client_supports_http_and_local_fallback() -> None:
    client = (GODOT_ROOT / "scripts/luvoire_client.gd").read_text(encoding="utf-8")

    assert "HTTPRequest.new()" in client
    assert "_fallback_response" in client
    assert "session_id" in client


def test_godot_scene_uses_npc_controller() -> None:
    scene = (GODOT_ROOT / "scenes/chat_demo.tscn").read_text(encoding="utf-8")

    assert 'path="res://scripts/npc.gd"' in scene
    assert 'name="Input" type="LineEdit"' in scene
    assert 'name="SendButton" type="Button"' in scene
