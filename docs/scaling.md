# City-Scale Scaling

Luvoire's city-scale runner is a deterministic proof-of-concept for large offline social simulation runs. It is designed for benchmark evidence, replay demos, and reproducibility checks rather than live LLM inference.

## Architecture

`CityScaleRunner` shards agents into worker-owned state partitions. Each shard receives an immutable tick payload and returns updated agent state, frame deltas, and outbound messages. The coordinator merges shard outputs and routes the next tick's inbox through a deterministic round-robin queue. No worker mutates shared state.

The default backend is `multiprocessing`. The `ray` backend flag is accepted for compatibility with `luvoire[scale]`, but Ray is optional; when Ray is unavailable, the runner falls back to the same deterministic multiprocessing path.

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
- `viewer.html` renders the 100-agent, 1000-agent, and 5000-agent scenarios with Canvas 2D.
- `profiles/` contains Tier 1, Tier 2, and CAT-28 Tier 5 pedagogical overlays.

Some browsers block `fetch()` for local `file://` msgpack files. The viewer includes a network-free file-selection fallback: open `viewer.html`, choose the needed replay msgpack files with `Load files`, then use the scenario switcher.

### 5K Scenario

The 5K replay uses `demo/replay/scenario_config_40x40.yaml`, a 40x40 variant of
the same alley, main-road, and commercial-edge topology used by the 20x20 replay.
The doubled grid keeps the agent-per-cell density close to the 1K/20x20 demo while
leaving the existing 100-agent and 1000-agent artifacts byte-identical.

Regenerate the artifact with:

```bash
python demo/replay/generate_replay.py --scenario 5k
```

Verify the committed artifact with:

```bash
python demo/replay/generate_replay.py --scenario 5k --verify-existing
```

The committed file is `demo/replay/replay_5000agents_gangnam_7pm.msgpack`
(4,779,728 bytes). This replay is local-demo only: it is not bundled into the
HF Space footprint and should not be uploaded as part of the playground surface.

### 10K Scenario

The 10K replay uses `demo/replay/scenario_config_60x60.yaml`, a 60x60 variant
that scales the same alley connectors, main-road corridor, and commercial-edge
zone used by the smaller offline replays. The larger grid keeps per-cell density
near the 1K/20x20 and 5K/40x40 demo configurations while preserving the same
local viewer interaction model.

Regenerate the artifact with:

```bash
python demo/replay/generate_replay.py --scenario 10k
```

Verify the committed artifact with:

```bash
python demo/replay/generate_replay.py --scenario 10k --verify-existing
```

The committed file is `demo/replay/replay_10000agents_gangnam_7pm.msgpack`
(9,539,344 bytes). This replay is local-demo only: it is not bundled into the
HF Space footprint and should not be uploaded as part of the playground surface.

### Nemotron-Seeded 10K Demo

The optional Nemotron replay keeps the same 10K / 30-tick / 60x60 simulation
shape while replacing compact stub demographics with synthetic
Nemotron-Personas-Korea attributes sampled from the committed 512-row Gangnam
fixture. The existing stub 10K artifact remains byte-identical.

Regenerate the Nemotron variant with:

```bash
python demo/replay/generate_replay.py --scenario 10k --persona-source nemotron
```

Verify the committed Nemotron artifact with:

```bash
python demo/replay/generate_replay.py --scenario 10k --persona-source nemotron --verify-existing
```

The committed file is
`demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack` (11,802,818
bytes). Its metadata records `persona_source = "nemotron"` and the pinned
Nemotron-Personas-Korea dataset revision.

## Extending Beyond 10K Agents

The runner is intentionally simple. For larger replay work, keep the same constraints:

- preserve deterministic seeds and output hashing;
- keep inter-shard messages coordinator-routed;
- avoid shared mutable state in worker code;
- emit compact frame deltas instead of full snapshots;
- benchmark external frameworks only when equivalent adapters actually run.

For live LLM scenarios, use replay-only deterministic traces for stakeholder demos and reserve live calls for smaller controlled experiments.
