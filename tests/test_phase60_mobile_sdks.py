from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_phase60_mobile_sdk_files_exist() -> None:
    expected = [
        "sdk/ios/KnoemaMobile/Package.swift",
        "sdk/ios/KnoemaMobile/Sources/KnoemaMobile/KnoemaClient.swift",
        "sdk/ios/KnoemaMobile/Sources/KnoemaMobile/NPCAgent.swift",
        "sdk/ios/KnoemaMobile/Tests/KnoemaMobileTests/KnoemaMobileTests.swift",
        "sdk/ios/Example/DRY_RUN.md",
        "sdk/android/settings.gradle.kts",
        "sdk/android/build.gradle.kts",
        "sdk/android/knoema-mobile/build.gradle.kts",
        "sdk/android/knoema-mobile/src/main/kotlin/com/celovin/knoema/KnoemaClient.kt",
        "sdk/android/knoema-mobile/src/main/kotlin/com/celovin/knoema/NPCAgent.kt",
        "sdk/android/example/DRY_RUN.md",
        "docs/sdk/mobile.md",
    ]

    for path in expected:
        assert Path(path).exists()


def test_phase60_swift_package_builds_and_tests() -> None:
    subprocess.run(
        ["swift", "build", "--package-path", "sdk/ios/KnoemaMobile"],
        check=True,
        cwd=Path.cwd(),
    )
    subprocess.run(
        ["swift", "test", "--package-path", "sdk/ios/KnoemaMobile"],
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
        "sdk/ios/KnoemaMobile/Sources/KnoemaMobile/KnoemaClient.swift"
    ).read_text(encoding="utf-8")
    swift_agent = Path("sdk/ios/KnoemaMobile/Sources/KnoemaMobile/NPCAgent.swift").read_text(
        encoding="utf-8"
    )
    kotlin_client = Path(
        "sdk/android/knoema-mobile/src/main/kotlin/com/celovin/knoema/KnoemaClient.kt"
    ).read_text(encoding="utf-8")
    kotlin_agent = Path(
        "sdk/android/knoema-mobile/src/main/kotlin/com/celovin/knoema/NPCAgent.kt"
    ).read_text(encoding="utf-8")

    for token in ["buildRESTRequest", "buildWebSocketURL", "cache", "offlineResponse"]:
        assert token in swift_client
    assert "cachedOrOfflineResponse" in swift_agent
    for token in ["restUrl", "webSocketUrl", "cacheResponse", "offlineResponse"]:
        assert token in kotlin_client
    assert "cachedOrOfflineResponse" in kotlin_agent


def test_phase60_docs_and_changelog_are_linked() -> None:
    docs = Path("docs/sdk/mobile.md").read_text(encoding="utf-8")

    assert "swift build --package-path sdk/ios/KnoemaMobile" in docs
    assert "./gradlew build" in docs
    assert "Mobile SDKs: sdk/mobile.md" in Path("mkdocs.yml").read_text(encoding="utf-8")
    assert "Phase 60 mobile SDK scaffolds" in Path("CHANGELOG.md").read_text(encoding="utf-8")
