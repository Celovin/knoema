# Scenario DSL Reference

## Version

`schema_version: "1.0"`

## Root Object

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `scenario_id` | string | yes | Lowercase letters, digits, `_`, and `-`. |
| `title` | string | yes | Human-readable scenario title. |
| `domain` | enum | yes | `game`, `public_safety_research`, or `academic_research`. |
| `description` | string | yes | Fictional scenario summary. |
| `seed` | integer | yes | Non-negative deterministic seed. |
| `tick_duration_minutes` | integer | no | Defaults to 60. |
| `duration_days` | integer | no | Defaults to 1. |
| `environment` | object | yes | Start time, location path, and conditions. |
| `agents` | list | yes | One or more synthetic agents. |
| `events` | list | no | Scheduled world events. |
| `metrics` | list | no | Evaluation metrics. |
| `ethics` | object | no | Defaults to safe fictional flags. |

## Ethics Rules

The validator enforces:

- `fictional: true`
- `no_real_people: true`
- `no_prediction: true`
- `no_suspect_scoring: true`
- every agent has `synthetic: true`
- sensitive scenarios include non-empty `irb_notes`

It also blocks phrases that indicate prediction, identification, suspect ranking, or personal data use.

## JSON Schema

The generated schema is available at [schemas/scenario_v1.json](../../schemas/scenario_v1.json).
