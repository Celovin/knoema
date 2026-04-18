# CLI

Knoema provides a small command line entry point for deterministic simulation runs:

```powershell
knoema run examples\cli_dorm.yaml --json
```

When running from a source checkout, this equivalent command also works:

```powershell
python -m knoema.cli run examples\cli_dorm.yaml --json
```

## Config Shape

```yaml
runtime:
  duration_days: 1
  tick_duration_minutes: 720
  output_path: ../runs/cli_dorm.jsonl
  prompt_language: en

environment:
  start_time: "2026-03-02T09:00:00"
  location_path: [Korea, Seoul, Dormitory]
  conditions:
    weather: clear

agents:
  - agent_id: alice
    name: Alice
    age: 17
    background: Dormitory student.
    personality:
      openness: 0.8
      conscientiousness: 0.6
      extraversion: 0.2
      agreeableness: 0.7
      neuroticism: 0.4
    values: [privacy]
    goals: [finish a short story]

events: []
local_response: '{"action_type": "wait", "target": null, "content": "observes the situation."}'
```

`output_path` in the config is resolved relative to the config file. `--output` overrides it and is resolved relative to the current working directory unless it is absolute.

## Validation

Use `--dry-run` to validate a config without running the simulation or writing logs:

```powershell
knoema run examples\cli_dorm.yaml --dry-run --json
```

The CLI is intentionally local-first. It uses `LocalClient` and the configured `local_response`, so it does not need API keys.

## Scoring

Use `score` to compute Persona Consistency Score (PCS) and Relationship Coherence Score (RCS) from a JSONL log:

```powershell
knoema score experiments\50_agent_village\results\sim_log.jsonl
```

The command prints JSON with PCS summary statistics, per-agent PCS values, RCS pair counts, and an RCS sample for quick inspection.
