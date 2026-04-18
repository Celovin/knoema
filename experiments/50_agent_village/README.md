# 50-Agent Village Experiment

Phase 19 scales the Knoema demo from small notebooks to a deterministic 50-agent, one-week village run.

## Run

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python experiments\50_agent_village\run.py
```

Outputs:

- `results/sim_log.jsonl`: full deterministic simulation log.
- `results/metrics.json`: action counts, action mix, latency model percentiles, token/cost estimate, and checksums.
- `results/trace_sample.json`: first 50 log entries for quick review.
- `docs/reports/50_agent_benchmark.pdf`: 10-page report with charts and interpretation.

## Reproducibility

The committed artifacts avoid wall-clock timings so they can be regenerated bit-for-bit from the same config and seed. The script prints measured generation time to stdout for local operator awareness, but the tracked JSON artifacts use deterministic metrics and SHA-256 checksums.

## Scenario

The fictional Harbor Village contains 50 synthetic residents coordinating a weekly lantern market. No real people, real incidents, or personal data are modeled.
