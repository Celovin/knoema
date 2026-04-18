"""Phase 16 tests for the Unity adapter package scaffold."""

from __future__ import annotations

import json
from pathlib import Path

UNITY_ROOT = Path("adapters/unity")


def test_phase16_unity_adapter_expected_files_exist() -> None:
    expected = [
        "README.md",
        "package.json",
        "Runtime/Knoema.Runtime.asmdef",
        "Runtime/KnoemaClient.cs",
        "Runtime/NPCAgent.cs",
        "Runtime/KnoemaConfig.cs",
        "Samples~/BasicNPC/Scenes/BasicNPC.unity",
        "Samples~/BasicNPC/Scripts/BasicNPCDemo.cs",
        "Tests/Editor/Knoema.EditorTests.asmdef",
        "Tests/Editor/KnoemaClientTests.cs",
    ]

    missing = [path for path in expected if not (UNITY_ROOT / path).exists()]

    assert missing == []


def test_phase16_unity_package_supports_upm_git_install() -> None:
    package = json.loads((UNITY_ROOT / "package.json").read_text(encoding="utf-8"))
    readme = (UNITY_ROOT / "README.md").read_text(encoding="utf-8")

    assert package["name"] == "com.celovin.knoema"
    assert package["unity"] == "2022.3"
    assert package["samples"][0]["path"] == "Samples~/BasicNPC"
    assert "https://github.com/Celovin/knoema.git?path=adapters/unity" in readme


def test_phase16_unity_runtime_client_matches_knoema_protocol() -> None:
    client = (UNITY_ROOT / "Runtime/KnoemaClient.cs").read_text(encoding="utf-8")
    config = (UNITY_ROOT / "Runtime/KnoemaConfig.cs").read_text(encoding="utf-8")
    npc_agent = (UNITY_ROOT / "Runtime/NPCAgent.cs").read_text(encoding="utf-8")

    assert "UnityWebRequest" in client
    assert "http://localhost:8000/interact" in config
    assert "session_id" in client
    assert "player_action" in client
    assert "LocalFallback" in client
    assert "MonoBehaviour" in npc_agent
    assert "StartCoroutine" in npc_agent


def test_phase16_unity_sample_and_editor_tests_are_present() -> None:
    sample = (UNITY_ROOT / "Samples~/BasicNPC/Scripts/BasicNPCDemo.cs").read_text(
        encoding="utf-8"
    )
    editor_test = (UNITY_ROOT / "Tests/Editor/KnoemaClientTests.cs").read_text(
        encoding="utf-8"
    )

    assert "NPCAgent" in sample
    assert "InputField" in sample
    assert "ConfigDefaultsToLocalhostEndpoint" in editor_test
    assert "KnoemaClient" in editor_test
