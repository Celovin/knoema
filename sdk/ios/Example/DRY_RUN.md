# iOS Example Dry Run

The Swift package builds without an Apple developer account:

```bash
swift build --package-path sdk/ios/LuvoireMobile
swift test --package-path sdk/ios/LuvoireMobile
```

The sample flow creates a `LuvoireClient`, wraps it in `NPCAgent`, builds a REST request for the Phase 44 API, derives a WebSocket URL for live streams, and falls back to a local offline response when the network is unavailable.
