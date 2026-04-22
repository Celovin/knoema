# Knoema Sequential v6 Night Report - 2026-04-22

## Execution Summary

| Slot | Scope | Commit |
| --- | --- | --- |
| A | API server commercial gating | `6509eea192776d9ec1469fa21bfa6a65f8a0d29b` |
| B | Commercial audit coverage | `f7fa84b882dcc81055bfa5f68be2bb65fa31ec12` |
| C | Customer onboarding CLI | `195cb2c6a739a450e2643095478653f1e59f75b2` |
| D | Public replay benchmark publication | `8d72ad70789f0908147937bd03197b4e5d8ed120` |
| E | Opt-in observability | `ef809522a7553aa3139b83e0d0285af3ceb7ca5c` |
| F | Rolling 7/30/90-day uptime and SLA badges | `8652a767cfb7e33aabdfdb585c2b5bca487ad516` |

Latest status automation commit observed after Slot F: `1d83f8c8691a4b9f2b0c0b886ce98d7319917eef`.

## Final Gate

- Full pytest gate: `680 passed, 4 skipped, 5 warnings`.
- Ruff: `python -m ruff check .` passed.
- Mypy: `python -m mypy src` passed on 113 source files.
- MkDocs: `python -m mkdocs build --strict` passed.
- Encoding / Gradio / Plotly targeted guard: `9 passed`.
- Slot F staged diff guard: whitespace check passed; forbidden pattern scan `0`; raw secret pattern scan `0`.
- Cumulative v6 diff scan from `5b0deb4..HEAD`: forbidden pattern scan `0`; raw secret pattern scan `0`.

## Replay SHA Invariance

| Artifact | SHA256 |
| --- | --- |
| `demo/replay/replay_100agents_gangnam_7pm.msgpack` | `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab` |
| `demo/replay/replay_1000agents_gangnam_7pm.msgpack` | `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b` |
| `demo/replay/replay_5000agents_gangnam_7pm.msgpack` | `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01` |
| `demo/replay/replay_10000agents_gangnam_7pm.msgpack` | `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2` |
| `demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack` | `9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9` |

## Protected v5 Artifact Identity

| Artifact | SHA256 |
| --- | --- |
| `ATTRIBUTIONS.md` | `26455e5c9b4a25057aeea732c07970d5754aab676ef5ec4319da9b39c3eedc08` |
| `sbom.cdx.json` | `cb22e3e88a80b1109d42a0852d4671b8815d7c85d02a15f0612c1d95ec767dff` |
| `site-snapshot/pricing.html` | `68f46cb44609007ea59d3e3128d37d78cf3983ae61964c474c3e26b2457afc09` |

## Commercial Audit Event Registry

`COMMERCIAL_AUDIT_EVENT_TYPES` contains these 8 event types:

```text
commercial.key_issued
commercial.key_rotated
commercial.key_revoked
commercial.webhook_dispatched
commercial.webhook_failed
commercial.webhook_exhausted
commercial.tier_limit_exceeded
commercial.cap_exhausted_output_tokens
```

## Status Snapshot

- `site-snapshot/status.html` size: `7,336` bytes.
- `site-snapshot/status.html` SHA256: `39850633a007786825abeb543dcd08cd05efda6492f68d90c5188f9e0a6c10da`.
- `site-snapshot/uptime.json` SHA256: `bf4e2cc79726ce452a74b0ac840843cb98ee01b2ea3f9003698e13bf9724999f`.
- `site-snapshot/uptime.json` generated at: `2026-04-22T07:44:22Z`.
- Uptime sample count: `10`.
- All 7d / 30d / 90d component windows currently report `insufficient_data` because the available history spans less than 7 days.

## Replay Benchmark JSON

Final `docs/benchmarks/replay-perf.json` contents:

```json
{
  "artifacts": [
    {
      "agent_count": 100,
      "artifact_commit": "ea0783bcc892ba827b73cc7df61db9586f04880a",
      "filename": "replay_100agents_gangnam_7pm.msgpack",
      "fps_20x": 18798.464792,
      "grid": "20x20",
      "label": "100",
      "load_time_s": 0.002646,
      "msgpack_sha256": "8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab",
      "msgpack_size_mb": 0.421688,
      "rss_delta_mb": 2.378906,
      "tick_count": 30,
      "tick_wall_s_per_20x": 0.031918
    },
    {
      "agent_count": 1000,
      "artifact_commit": "ea0783bcc892ba827b73cc7df61db9586f04880a",
      "filename": "replay_1000agents_gangnam_7pm.msgpack",
      "fps_20x": 1644.62684,
      "grid": "20x20",
      "label": "1000",
      "load_time_s": 0.023236,
      "msgpack_sha256": "0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b",
      "msgpack_size_mb": 4.215182,
      "rss_delta_mb": 18.796875,
      "tick_count": 30,
      "tick_wall_s_per_20x": 0.364824
    },
    {
      "agent_count": 5000,
      "artifact_commit": "6f3ac76ae03337d9e1b3e99fdc9d35163692a24a",
      "filename": "replay_5000agents_gangnam_7pm.msgpack",
      "fps_20x": 258.672056,
      "grid": "40x40",
      "label": "5000",
      "load_time_s": 0.055577,
      "msgpack_sha256": "d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01",
      "msgpack_size_mb": 4.558304,
      "rss_delta_mb": 39.894531,
      "tick_count": 30,
      "tick_wall_s_per_20x": 2.319539
    },
    {
      "agent_count": 10000,
      "artifact_commit": "c262c8f912df04be6868740164f6c2c28bf6fc94",
      "filename": "replay_10000agents_gangnam_7pm.msgpack",
      "fps_20x": 105.170042,
      "grid": "60x60",
      "label": "10000",
      "load_time_s": 0.138725,
      "msgpack_sha256": "af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2",
      "msgpack_size_mb": 9.097427,
      "rss_delta_mb": 84.710938,
      "tick_count": 30,
      "tick_wall_s_per_20x": 5.705047
    },
    {
      "agent_count": 10000,
      "artifact_commit": "6c2a2acb56e594b1a0514c86d9a4429e1b6764ae",
      "filename": "replay_10000agents_nemotron_gangnam_7pm.msgpack",
      "fps_20x": 110.478513,
      "grid": "60x60",
      "label": "10000 nemotron",
      "load_time_s": 0.146639,
      "msgpack_sha256": "9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9",
      "msgpack_size_mb": 11.256044,
      "rss_delta_mb": 93.074219,
      "tick_count": 30,
      "tick_wall_s_per_20x": 5.43092
    }
  ],
  "generated_at": "2026-04-22T07:22:29.804389+00:00",
  "hardware": {
    "machine": "AMD64",
    "node": "DESKTOP-VHH7FT3",
    "platform": "Windows-10-10.0.19045-SP0",
    "processor": "AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD",
    "python": "3.13.13",
    "ram_gb": 63.141949,
    "system": "Windows"
  },
  "methodology": {
    "check_repeats": 3,
    "regression_tolerance": 0.15,
    "script": "scripts/bench_replay_throughput.py",
    "sequential_replay_loops": 20,
    "time_noise_floor_seconds": 0.05,
    "timers": "time.perf_counter"
  }
}
```
