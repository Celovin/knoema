"""Phase 47 tests for the Unreal Engine 5 adapter scaffold."""

from __future__ import annotations

import json
from pathlib import Path

UNREAL_ROOT = Path("adapters/unreal")


def test_phase47_unreal_adapter_files_exist() -> None:
    expected = [
        "README.md",
        "KnoemaUnreal.uplugin",
        "Source/KnoemaUnreal/KnoemaUnreal.Build.cs",
        "Source/KnoemaUnreal/Public/KnoemaClient.h",
        "Source/KnoemaUnreal/Public/NPCAgentComponent.h",
        "Source/KnoemaUnreal/Private/KnoemaClient.cpp",
        "Source/KnoemaUnreal/Private/NPCAgentComponent.cpp",
        "Source/KnoemaUnreal/Private/KnoemaUnrealModule.cpp",
        "Content/Blueprints/BP_BasicNPC.uasset",
    ]

    missing = [path for path in expected if not (UNREAL_ROOT / path).exists()]
    assert missing == []
    assert Path("docs/adapters/unreal.md").exists()


def test_phase47_plugin_descriptor_is_valid_and_declares_runtime_module() -> None:
    descriptor = json.loads((UNREAL_ROOT / "KnoemaUnreal.uplugin").read_text(encoding="utf-8"))

    assert descriptor["FriendlyName"] == "Knoema Unreal"
    assert descriptor["Modules"][0]["Name"] == "KnoemaUnreal"
    assert descriptor["Modules"][0]["Type"] == "Runtime"
    assert descriptor["CanContainContent"] is True


def test_phase47_unreal_sources_reference_phase44_rest_api_and_tick_polling() -> None:
    client_header = (UNREAL_ROOT / "Source/KnoemaUnreal/Public/KnoemaClient.h").read_text(
        encoding="utf-8"
    )
    client_cpp = (UNREAL_ROOT / "Source/KnoemaUnreal/Private/KnoemaClient.cpp").read_text(
        encoding="utf-8"
    )
    component_header = (
        UNREAL_ROOT / "Source/KnoemaUnreal/Public/NPCAgentComponent.h"
    ).read_text(encoding="utf-8")
    component_cpp = (
        UNREAL_ROOT / "Source/KnoemaUnreal/Private/NPCAgentComponent.cpp"
    ).read_text(encoding="utf-8")

    assert "UCLASS(BlueprintType)" in client_header
    assert "CreateSimulation" in client_header
    assert "PollSimulation" in client_header
    assert 'TEXT("/simulations")' in client_cpp
    assert 'TEXT("/simulations/%s/events")' in client_cpp
    assert "FHttpModule::Get().CreateRequest()" in client_cpp
    assert "BlueprintSpawnableComponent" in component_header
    assert "TickComponent" in component_header
    assert "PrimaryComponentTick.bCanEverTick = true;" in component_cpp


def test_phase47_unreal_sources_have_balanced_braces_for_static_syntax_check() -> None:
    candidates = [
        UNREAL_ROOT / "Source/KnoemaUnreal/KnoemaUnreal.Build.cs",
        UNREAL_ROOT / "Source/KnoemaUnreal/Public/KnoemaClient.h",
        UNREAL_ROOT / "Source/KnoemaUnreal/Public/NPCAgentComponent.h",
        UNREAL_ROOT / "Source/KnoemaUnreal/Private/KnoemaClient.cpp",
        UNREAL_ROOT / "Source/KnoemaUnreal/Private/NPCAgentComponent.cpp",
        UNREAL_ROOT / "Source/KnoemaUnreal/Private/KnoemaUnrealModule.cpp",
    ]

    for path in candidates:
        text = path.read_text(encoding="utf-8")
        assert _is_balanced(text, "{", "}")
        assert _is_balanced(text, "(", ")")


def test_phase47_unreal_docs_cover_installation_and_blueprint_usage() -> None:
    readme = (UNREAL_ROOT / "README.md").read_text(encoding="utf-8")
    doc = Path("docs/adapters/unreal.md").read_text(encoding="utf-8")
    guide = Path("docs/guides/game-integration.md").read_text(encoding="utf-8")
    placeholder = (UNREAL_ROOT / "Content/Blueprints/BP_BasicNPC.uasset").read_text(
        encoding="utf-8"
    )
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert len(readme.split()) >= 100
    assert "UE_5.3" in readme
    assert "NPCAgentComponent" in readme
    assert "BP_BasicNPC" in readme
    assert "REST API" in doc
    assert "Blueprint" in doc
    assert "adapters/unreal" in guide
    assert "docs/adapters/unreal.md" not in guide
    assert "UE5_PLACEHOLDER_ASSET" in placeholder
    assert "adapters/unreal.md" in mkdocs


def _is_balanced(text: str, opening: str, closing: str) -> bool:
    depth = 0
    for char in text:
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth < 0:
                return False
    return depth == 0
