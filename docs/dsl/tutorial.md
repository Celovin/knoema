# Scenario DSL Tutorial

Scenario DSL v1 describes a reproducible Luvoire scenario in YAML. It is intended for fictional game scenes, synthetic public-safety replay research, and academic simulations.

## Minimal Run

```powershell
cd C:\Users\admin\Projects\luvoire
.venv\Scripts\python - <<'PY'
from luvoire.dsl import load_scenario

scenario = load_scenario('examples/scenarios/01_shopkeeper_winter_crime.yaml')
simulator = scenario.to_simulator()
logs = simulator.run(duration_days=scenario.duration_days)
print(len(logs))
PY
```

## Fields

- `schema_version`: currently `1.0`.
- `scenario_id`: stable lowercase identifier.
- `domain`: `game`, `public_safety_research`, or `academic_research`.
- `seed`: deterministic scenario seed.
- `environment`: start time, location path, and simple conditions.
- `agents`: synthetic personas with Big Five traits.
- `events`: scheduled world events.
- `metrics`: declared evaluation metrics.
- `ethics`: required guardrails for sensitive scenarios.

## Ethics Gate

The validator rejects scenarios that are not fictional, model real people, attempt future harm prediction, score suspects, omit review notes for sensitive domains, or include disallowed purpose phrases.

Use `collect_validation_issues(...)` to display all issues without raising.
