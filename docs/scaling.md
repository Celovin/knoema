# City-Scale Scaling

Knoema's city-scale runner is a deterministic proof-of-concept for large offline social simulation runs. It is designed for benchmark evidence, replay demos, and reproducibility checks rather than live LLM inference.

## Architecture

`CityScaleRunner` shards agents into worker-owned state partitions. Each shard receives an immutable tick payload and returns updated agent state, frame deltas, and outbound messages. The coordinator merges shard outputs and routes the next tick's inbox through a deterministic round-robin queue. No worker mutates shared state.

The default backend is `multiprocessing`. The `ray` backend flag is accepted for compatibility with `knoema[scale]`, but Ray is optional; when Ray is unavailable, the runner falls back to the same deterministic multiprocessing path.

## Benchmark

Run the 1K proof:

```bash
python benchmarks/city_scale_1k.py --output tmp/city_scale
```

The benchmark runs 1000 agents for 100 ticks across three repetitions with no live API calls. The generated report is `benchmarks/city_scale_1k_report.md`, and the JSON/JSONL traces are written under `tmp/city_scale`.

Comparison rows for Concordia and Mesa are marked `not-measured` unless those frameworks are actually run with equivalent adapters. The report does not fabricate external throughput numbers.

## Offline Replay

The replay demo lives in `demo/replay/`.

- `generate_replay.py` regenerates deterministic msgpack files.
- `viewer.html` renders the 100-agent and 1000-agent scenarios with Canvas 2D.
- `profiles/` contains Tier 1 and Tier 2 pedagogical overlays only.

Some browsers block `fetch()` for local `file://` msgpack files. The viewer includes a network-free file-selection fallback: open `viewer.html`, choose both replay files with `Load files`, then use the scenario switcher.

## Extending To 10K Agents

The runner is intentionally simple. For 10K-agent work, keep the same constraints:

- preserve deterministic seeds and output hashing;
- keep inter-shard messages coordinator-routed;
- avoid shared mutable state in worker code;
- emit compact frame deltas instead of full snapshots;
- benchmark external frameworks only when equivalent adapters actually run.

For live LLM scenarios, use replay-only deterministic traces for stakeholder demos and reserve live calls for smaller controlled experiments.
