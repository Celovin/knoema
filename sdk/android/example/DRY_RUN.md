# Android Example Dry Run

The Android module is shaped as a Gradle library module:

```bash
cd sdk/android
./gradlew build
```

The local wrapper validates the committed Kotlin source shape when a full Android toolchain is not installed. In Android Studio or CI with JDK, Gradle, and the Android SDK available, the same module can be opened as `luvoire-android-sdk`.

The sample flow creates a `LuvoireClient`, wraps it in `NPCAgent`, builds Phase 44 REST and WebSocket URLs, and falls back to cached offline responses when the live API is unreachable.
