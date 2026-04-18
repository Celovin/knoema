# Mobile SDKs

Phase 60 adds mobile SDK scaffolds for game and interactive-media clients.

## iOS

Path: `sdk/ios/KnoemaMobile`

```bash
swift build --package-path sdk/ios/KnoemaMobile
swift test --package-path sdk/ios/KnoemaMobile
```

Public surface:

- `KnoemaClient` builds REST requests for the Phase 44 API.
- `KnoemaClient.buildWebSocketURL` derives live-stream URLs.
- `NPCAgent` wraps an agent ID and exposes cached offline fallback responses.
- `NPCActionResponse` and `AgentSnapshot` are Codable value types.

## Android

Path: `sdk/android`

```bash
cd sdk/android
./gradlew build
```

Public surface:

- `KnoemaClient.restUrl` builds REST endpoints.
- `KnoemaClient.webSocketUrl` derives live-stream endpoints.
- `KnoemaClient.cacheResponse` and `cachedResponse` provide local caching hooks.
- `NPCAgent.cachedOrOfflineResponse` provides an offline-safe NPC wrapper.

The committed Android wrapper validates source shape in environments without JDK, Gradle, or the Android SDK. Production Android CI should run the same module with the native Android toolchain installed.
