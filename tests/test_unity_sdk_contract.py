from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from luvoire.api.server import create_app

UNITY_PACKAGE = Path("unity-sdk/Packages/com.celovin.luvoire")


def test_unity_sdk_package_json_is_upm_compatible() -> None:
    package = json.loads((UNITY_PACKAGE / "package.json").read_text(encoding="utf-8"))

    assert package["name"] == "com.celovin.luvoire"
    assert package["version"] == "0.3.0"
    assert package["unity"] == "2022.3"
    assert package["samples"][0]["path"] == "Samples~/BasicNPC"
    assert (UNITY_PACKAGE / "Runtime/LuvoireClient.cs").exists()
    assert (UNITY_PACKAGE / "Runtime/LuvoireNPC.cs").exists()
    assert (UNITY_PACKAGE / "Runtime/Models/LuvoireTickRequest.cs").exists()
    assert (UNITY_PACKAGE / "Editor/LuvoireSettingsWindow.cs").exists()
    assert (UNITY_PACKAGE / "Samples~/BasicNPC/BasicNPC.scene.yaml").exists()


def test_unity_sdk_client_documents_exact_tick_payload_fields() -> None:
    client = (UNITY_PACKAGE / "Runtime/LuvoireClient.cs").read_text(encoding="utf-8")
    tick_request = (UNITY_PACKAGE / "Runtime/Models/LuvoireTickRequest.cs").read_text(
        encoding="utf-8"
    )
    readme = Path("unity-sdk/README.md").read_text(encoding="utf-8")

    for field in ["session_id", "agent_id", "player_action", "context_json"]:
        assert field in tick_request
        assert field in readme
    assert '"/simulate/tick"' in client
    assert "GET /agent/{id}/memory?session_id=unity-demo" in readme
    assert "POST /agent/{id}/action" in readme


def test_unity_sdk_fastapi_contract_tick_memory_and_action(monkeypatch: Any) -> None:
    monkeypatch.delenv("LUVOIRE_API_KEY", raising=False)
    with TestClient(create_app()) as client:
        tick_response = client.post(
            "/simulate/tick",
            json={
                "session_id": "unity-demo",
                "agent_id": "guide",
                "player_action": "asks about the lantern market",
                "context_json": '{"location":"Demo Village > Plaza","agent_name":"Guide"}',
            },
        )
        assert tick_response.status_code == 200
        tick_payload = tick_response.json()
        assert tick_payload["session_id"] == "unity-demo"
        assert tick_payload["agent_id"] == "guide"
        assert tick_payload["tick"] == 0
        assert tick_payload["content"]
        assert tick_payload["emotion"] in {"neutral", "positive", "tense"}
        assert "session:unity-demo" in tick_payload["branch_flags"]
        assert tick_payload["action"]["action_type"] == "speak"
        assert tick_payload["action"]["target"] == "player"

        memory_response = client.get("/agent/guide/memory", params={"session_id": "unity-demo"})
        assert memory_response.status_code == 200
        memory_payload = memory_response.json()
        assert memory_payload["agent_id"] == "guide"
        assert len(memory_payload["memories"]) == 1
        assert memory_payload["memories"][0]["content"] == tick_payload["content"]

        action_response = client.post(
            "/agent/guide/action",
            json={
                "session_id": "unity-demo",
                "action_type": "observe",
                "target": "player",
                "content": "Guide notices the player inspecting a lantern.",
                "location": "Demo Village > Plaza",
                "metadata_json": '{"source":"unity-test"}',
            },
        )
        assert action_response.status_code == 200
        action_payload = action_response.json()
        assert action_payload["accepted"] is True
        assert action_payload["tick"] == 1
        assert action_payload["action"]["action_type"] == "observe"
        assert action_payload["action"]["metadata"] == {"source": "unity-test"}


def test_unity_sdk_api_openapi_lists_contract_paths(monkeypatch: Any) -> None:
    monkeypatch.delenv("LUVOIRE_API_KEY", raising=False)
    with TestClient(create_app()) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/simulate/tick" in paths
    assert "/agent/{agent_id}/memory" in paths
    assert "/agent/{agent_id}/action" in paths
