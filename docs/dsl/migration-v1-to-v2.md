# Scenario DSL v1 to v2 Migration

This guide walks through migrating an existing `schema_version: "1.0"` scenario to `schema_version: "2.0"`. Both versions remain importable for one release window; new scenarios should use v2.

## Why migrate

v2 adds:

- A `parameters:` block where each parameter declares its tier (A/B/C) and required metadata.
- Optional `environment.h3_cell` and `environment.epsg` GIS-readiness fields.
- An `ethics.no_real_geometry: true` guardrail (default).
- Extended disallowed-purpose phrases for ethics validation.

v2 does not change v1's persona, agent, event, or metric schemas. v1-only scenarios can be auto-upgraded by the parser.

## Auto-upgrade path

```python
from luvoire.dsl.v2 import load_scenario_v2

# v1 file: emits one DeprecationWarning, returns a ScenarioV2.
scenario = load_scenario_v2("examples/scenarios/legacy_v1.yaml")
assert scenario.schema_version == "2.0"
assert scenario.parameters == {}
assert scenario.ethics.no_real_geometry is True
```

The auto-upgrade adds:

- `schema_version: "2.0"`
- `parameters: {}`
- `ethics.no_real_geometry: true` (only if not already set)

Auto-upgrade does **not** modify the file on disk. To persist, call `scenario_v2_to_yaml(...)` and write the result back.

## Manual migration checklist

1. **Bump `schema_version`** to `"2.0"`.
2. **Add a `parameters:` block** if the scenario has tunable values. Choose the right tier per parameter:
   - Tier A: theoretical constants only the code defines (locked).
   - Tier B: empirical priors with a citable `source`.
   - Tier C: exploration knobs with `range` + `default`.
3. **Add `ethics.no_real_geometry: true`** (default for v2) explicitly if your audit policy requires the field to be present.
4. **(Optional)** If the scenario uses synthetic spatial structure, add `environment.h3_cell` and `environment.epsg: "luvoire-synthetic-..."`.
5. **Run lint**: `python scripts/lint_dsl_v2.py path/to/scenario.yaml --strict`.

## Worked example

### Before (v1)

```yaml
schema_version: "1.0"
scenario_id: legacy_dorm
title: Legacy Dormitory
domain: academic_research
description: Two-student dormitory.
seed: 1
environment:
  start_time: "2026-04-27T09:00:00"
  location_path: ["Synthetic World", "Dormitory"]
  conditions: { weather: clear }
agents:
  - agent_id: alice
    # ...
ethics:
  fictional: true
  no_real_people: true
  no_prediction: true
  no_suspect_scoring: true
```

### After (v2)

```yaml
schema_version: "2.0"
scenario_id: legacy_dorm
title: Legacy Dormitory
domain: academic_research
description: Two-student dormitory.
seed: 1
parameters:
  shared_routine_weight:
    tier: C
    range: [0.0, 1.0]
    default: 0.5
    description: "Strength of shared dorm routine adherence (synthetic units)."
environment:
  start_time: "2026-04-27T09:00:00"
  location_path: ["Synthetic World", "Dormitory"]
  conditions: { weather: clear }
  h3_cell: "8830e1ad81fffff"
  epsg: "luvoire-synthetic-v1"
agents:
  - agent_id: alice
    # ...
ethics:
  fictional: true
  no_real_people: true
  no_prediction: true
  no_suspect_scoring: true
  no_real_geometry: true
```

## Choosing a tier

| If the parameter ... | Tier |
| --- | --- |
| encodes the theory itself (e.g., RAT convergence rule) and never changes per scenario | A |
| comes from real-world statistics or published literature | B |
| is a tunable knob you sweep across scenarios for sensitivity | C |

If the parameter started life as a numeric constant in code, leave it in code. If it's already a YAML knob you tune by hand, it's almost always Tier C.

## Lint guarantees

`scripts/lint_dsl_v2.py` enforces:

- Tier A: only the `ref` field allowed.
- Tier B: `source` non-empty, plus one of `value` or `distribution`.
- Tier C: `range` and `default` both present.
- All tiers: explicit `tier: A | B | C`.

Run lint as part of CI:

```bash
python scripts/lint_dsl_v2.py scenarios/library/ examples/scenarios/ --strict
```

## Backwards compatibility window

`load_scenario` (v1 loader, returns `Scenario`) and `load_scenario_v2` (v2 loader, returns `ScenarioV2` and accepts both v1 and v2 YAML) coexist for **one release window**. After that window, v1 scenario YAML files are expected to have been migrated; the v1 loader may be removed in a later major version.
