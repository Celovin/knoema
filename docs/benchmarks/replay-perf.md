# Replay Throughput Benchmark

Generated at: `2026-04-22T07:22:29.804389+00:00`

## Methodology

The benchmark loads each committed msgpack artifact with `msgpack.unpackb`, then applies all replay tick deltas in order for 20 sequential loops. Timings use `time.perf_counter`; RSS deltas use `psutil.Process().memory_info().rss` around load and replay phases.

Check mode runs three measurements and compares the best current value to the committed baseline. It fails when load time, replay wall time, or FPS regresses by more than 15%. A 0.05s floor is applied to time metrics so millisecond-scale I/O noise does not fail small artifacts.

Hardware caveat: Single-thread sequential on Windows 10, i5-class CPU. Throughput on Linux / modern server-class hardware is typically 2-4x higher but not yet published.

Methodology script: [scripts/bench_replay_throughput.py](https://github.com/Celovin/knoema/blob/main/scripts/bench_replay_throughput.py).

## Hardware

| Field | Value |
| --- | --- |
| System | Windows |
| Platform | Windows-10-10.0.19045-SP0 |
| Machine | AMD64 |
| Processor | AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD |
| RAM GB | 63.141949 |
| Python | 3.13.13 |

## Results

| Artifact | Agent count | Grid | load_time_s | tick_wall_s_per_20x | fps_20x | rss_delta_mb | msgpack_size_mb | msgpack_sha256 |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `replay_100agents_gangnam_7pm.msgpack` | 100 | 20x20 | 0.002646 | 0.031918 | 18798.464792 | 2.378906 | 0.421688 | `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab` |
| `replay_1000agents_gangnam_7pm.msgpack` | 1000 | 20x20 | 0.023236 | 0.364824 | 1644.62684 | 18.796875 | 4.215182 | `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b` |
| `replay_5000agents_gangnam_7pm.msgpack` | 5000 | 40x40 | 0.055577 | 2.319539 | 258.672056 | 39.894531 | 4.558304 | `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01` |
| `replay_10000agents_gangnam_7pm.msgpack` | 10000 | 60x60 | 0.138725 | 5.705047 | 105.170042 | 84.710938 | 9.097427 | `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2` |
| `replay_10000agents_nemotron_gangnam_7pm.msgpack` | 10000 | 60x60 | 0.146639 | 5.43092 | 110.478513 | 93.074219 | 11.256044 | `9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9` |

## Artifact Commits

| Artifact | Source commit |
| --- | --- |
| `replay_100agents_gangnam_7pm.msgpack` | `ea0783bcc892ba827b73cc7df61db9586f04880a` |
| `replay_1000agents_gangnam_7pm.msgpack` | `ea0783bcc892ba827b73cc7df61db9586f04880a` |
| `replay_5000agents_gangnam_7pm.msgpack` | `6f3ac76ae03337d9e1b3e99fdc9d35163692a24a` |
| `replay_10000agents_gangnam_7pm.msgpack` | `c262c8f912df04be6868740164f6c2c28bf6fc94` |
| `replay_10000agents_nemotron_gangnam_7pm.msgpack` | `6c2a2acb56e594b1a0514c86d9a4429e1b6764ae` |
