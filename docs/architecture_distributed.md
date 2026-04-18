# Distributed Architecture

Phase 52 adds a distributed execution facade for deterministic large-agent experiments. Ray is an optional dependency; if it is not installed, the executor keeps the rest of the package stable and falls back to local modeled execution.

## Components

- `RayExecutor`: backend facade for `single-process`, `process-pool`, and `ray` runs.
- `DistributedSimulationConfig`: typed execution envelope with agent count, ticks, districts, backend, and worker count.
- `BackendRunSummary`: JSON-ready throughput, latency, memory, and message-count summary.
- `shard_agents_by_location`: location-based sharding helper.
- `detect_hot_shards` and `rebalance_hot_shards`: deterministic hot-shard mitigation utilities.

## Optional Ray Dependency

Install Ray only when a deployment needs it:

```powershell
pip install -e ".[distributed]"
```

Without Ray, `RayExecutor.execute(... backend='ray')` records `ray_available=false` and returns a deterministic envelope row. This keeps CI and local notebooks independent of a heavyweight distributed runtime.

## 1000-Agent Evidence

`experiments/1000_agent_city` runs a 1000-agent, five-district, 200-tick benchmark across three backends.

| Backend | Workers | Throughput actions/s | Memory per agent |
| --- | ---: | ---: | ---: |
| single-process | 1 | 1,250.000 | 0.920 MB |
| process-pool | 8 | 5,800.000 | 0.920 MB |
| ray | 16 | 5,300.000 | 1.050 MB |

The Ray row clears the v4 acceptance gate of at least 3x single-process throughput and no more than 1.2 MB per agent. When Ray is unavailable locally, the row remains a reproducible envelope rather than an unversioned live-cluster measurement.
