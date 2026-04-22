# Safety Audit Log Schema

Safety audit logs are append-only JSONL files. Each line is one object with the following fields.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `event_id` | string | yes | Stable event identifier. |
| `timestamp` | string | yes | ISO-8601 timestamp. |
| `actor_id` | string | yes | Agent, user, or service actor that triggered the event. |
| `category` | string | yes | Safety category such as `prompt_injection`, `pii`, or `scenario_abuse`. |
| `outcome` | string | yes | `allowed`, `blocked`, or `flagged`. |
| `reason` | string | yes | Human-readable reason. |
| `source` | string | yes | Source system, default `luvoire`. |

Example:

```json
{"actor_id":"demo-user","category":"prompt_injection","event_id":"evt-001","outcome":"blocked","reason":"blocked by deterministic content filter","source":"luvoire","timestamp":"2026-04-19T00:00:00+00:00"}
```
