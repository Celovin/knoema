from __future__ import annotations

from pathlib import Path


def test_phase33_unity_and_godot_clients_share_core_payload_fields() -> None:
    unity_client = Path("adapters/unity/Runtime/LuvoireClient.cs").read_text(encoding="utf-8")
    godot_client = Path("adapters/godot/scripts/luvoire_client.gd").read_text(encoding="utf-8")

    for field in ["session_id", "agent_id"]:
        assert field in unity_client
        assert field in godot_client
    assert "content" in unity_client
    assert "content" in godot_client
    assert "local_fallback" in unity_client
    assert "_fallback_response" in godot_client


def test_phase33_adapter_docs_keep_package_and_runtime_entrypoints() -> None:
    unity_readme = Path("adapters/unity/README.md").read_text(encoding="utf-8")
    godot_readme = Path("adapters/godot/README.md").read_text(encoding="utf-8")
    game_docs = Path("docs/guides/game-integration.md").read_text(encoding="utf-8")

    assert "https://github.com/Celovin/luvoire.git?path=adapters/unity" in unity_readme
    assert "addons/luvoire" in godot_readme
    assert "GameSession" in game_docs
    assert "JSONL" in game_docs
