# Privacy

Luvoire telemetry is anonymous and opt-in.

## Default Behavior

- Telemetry is off by default.
- No telemetry is sent unless the user explicitly opts in with `LUVOIRE_TELEMETRY=1` or the CLI flag `--telemetry`.
- If no telemetry endpoint is configured, Luvoire stays silent even when opt-in is requested.

## What Luvoire Collects

- One anonymous UUID stored locally for telemetry continuity
- CLI surface name
- Whether the run used `--dry-run`
- Whether the summary output used `--json`
- Aggregate run metadata such as agent count, duration, tick size, scheduled event count, log count, and prompt language

## What Luvoire Does Not Collect

- Persona background text
- Prompt content
- Conversation transcripts
- Memory contents
- File paths
- API keys, tokens, or other credentials
- Personal identifiers

## Event Names

- `cli_run_requested`
- `cli_run_completed`
- `cli_summary_emitted`

## Opt-in Examples

Enable telemetry for the current shell session:

```powershell
$env:LUVOIRE_TELEMETRY = "1"
$env:LUVOIRE_TELEMETRY_ENDPOINT = "https://your-posthog-or-self-hosted-endpoint.example/capture"
```

Opt in for a single CLI invocation:

```powershell
luvoire run examples/cli_dorm.yaml --json --telemetry
```

To reset the anonymous identifier, delete the local telemetry id file under the user's `.luvoire` directory.
