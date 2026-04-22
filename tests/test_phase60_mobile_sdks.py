from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_phase60_mobile_sdk_files_exist() -> None:
    expected = [
        "sdk/ios/LuvoireMobile/Package.swift",
        "sdk/ios/LuvoireMobile/Sources/LuvoireMobile/LuvoireClient.swift",
        "sdk/ios/LuvoireMobile/Sources/LuvoireMobile/NPCAgent.swift",
        "sdk/ios/LuvoireMobile/Tests/LuvoireMobileTests/LuvoireMobileTests.swift",
        "sdk/ios/Example/DRY_RUN.md",
        "sdk/android/settings.gradle.kts",
        "sdk/android/build.gradle.kts",
        "sdk/android/luvoire-mobile/build.gradle.kts",
        "sdk/android/luvoire-mobile/src/main/kotlin/com/celovin/luvoire/LuvoireClient.kt",
        "sdk/android/luvoire-mobile/src/main/kotlin/com/celovin/luvoire/NPCAgent.kt",
        "sdk/android/example/DRY_RUN.md",
        "docs/sdk/mobile.md",
    ]

    for path in expected:
        assert Path(path).exists()


def test_phase60_swift_package_builds_and_tests() -> None:
    subprocess.run(
        ["swift", "build", "--package-path", "sdk/ios/LuvoireMobile"],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        ["swift", "test", "--package-path", "sdk/ios/LuvoireMobile"],
        check=True,
        cwd=Path.cwd(),
    )


def test_phase60_android_wrapper_build_validates_module_shape() -> None:
    command = ["cmd", "/c", "gradlew.bat", "build"] if os.name == "nt" else ["./gradlew", "build"]
    result = subprocess.run(
        command,
        check=True,
        cwd=Path("sdk/android"),
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["ok"] is True
    assert payload["missing"] == {}


def test_phase60_mobile_sdks_cover_rest_websocket_cache_and_offline() -> None:
    swift_client = Path(
        "sdk/ios/LuvoireMobile/Sources/LuvoireMobile/LuvoireClient.swift"
    ).read_text(encoding="utf-8")
    swift_agent = Path("sdk/ios/LuvoireMobile/Sources/LuvoireMobile/NPCAgent.swift").read_text(
        encoding="utf-8"
    )
    kotlin_client = Path(
        "sdk/android/luvoire-mobile/src/main/kotlin/com/celovin/luvoire/LuvoireClient.kt"
    ).read_text(encoding="utf-8")
    kotlin_agent = Path(
        "sdk/android/luvoire-mobile/src/main/kotlin/com/celovin/luvoire/NPCAgent.kt"
    ).read_text(encoding="utf-8")

    for token in ["buildRESTRequest", "buildWebSocketURL", "cache", "offlineResponse"]:
        assert token in swift_client
    assert "cachedOrOfflineResponse" in swift_agent
    for token in ["restUrl", "webSocketUrl", "cacheResponse", "offlineResponse"]:
        assert token in kotlin_client
    assert "cachedOrOfflineResponse" in kotlin_agent


def test_phase60_docs_and_changelog_are_linked() -> None:
    docs = Path("docs/sdk/mobile.md").read_text(encoding="utf-8")

    assert "swift build --package-path sdk/ios/LuvoireMobile" in docs
    assert "./gradlew build" in docs
    assert "Mobile SDKs: sdk/mobile.md" in Path("mkdocs.yml").read_text(encoding="utf-8")
    assert "Phase 60 mobile SDK scaffolds" in Path("CHANGELOG.md").read_text(encoding="utf-8")
