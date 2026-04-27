# Scenario DSL v2 Reference

Scenario DSL v2 extends v1 with a **variable 3-tier system**, optional GIS-readiness fields, and the `ethics.no_real_geometry` guardrail. Existing v1 scenarios continue to load via `load_scenario_v2` with a one-release-window deprecation warning.

## Quick Start

```python
from luvoire.dsl.v2 import load_scenario_v2

scenario = load_scenario_v2("examples/scenarios/v2_rat_baseline.yaml")
print(scenario.parameters["guardianship_density"].range)
```

```yaml
schema_version: "2.0"
scenario_id: rat_baseline_v2
title: RAT Baseline Synthetic Plaza
domain: academic_research
description: Synthetic routine activity scenario in a fictional Seoul-style plaza.
seed: 20260427
parameters:
  opportunity_definition:
    tier: A
    ref: "code:luvoire.theory.rat.v1"
  schedule_prior:
    tier: B
    source: "KOSTAT 2024 생활시간조사"
    table_id: "T-08"
    license: "KOGL Type 1"
    value: 0.42
  guardianship_density:
    tier: C
    range: [0.1, 0.9]
    sweep: 9
    default: 0.5
environment:
  start_time: "2026-04-23T19:00:00"
  location_path: ["Luvoire Demo World", "Seoul-style Synthetic Grid", "Plaza A"]
  h3_cell: "8830e1ad81fffff"
  epsg: "luvoire-synthetic-v1"
agents:
  - agent_id: coordinator
    name: Sora
    age: 32
    background: Synthetic coordinator helping participants find a meetup point.
    personality:
      openness: 0.59
      conscientiousness: 0.76
      extraversion: 0.63
      agreeableness: 0.72
      neuroticism: 0.24
    synthetic: true
ethics:
  fictional: true
  no_real_people: true
  no_prediction: true
  no_suspect_scoring: true
  no_real_geometry: true
```

## Variable 3-tier

The 3-tier system lets a scenario declare the **epistemic status** of every parameter, not just its numeric value. Pattern-Oriented Modeling, sensitivity sweeps, and audit trails all become tractable because the scenario itself records which parameters are theoretical, which are empirical, and which are exploratory.

### Tier A — Theoretical constant

Locked code-module reference. No inline value, no range, no source. Used when a parameter encodes the theory itself (e.g., the routine activity convergence rule). Changing a Tier A value requires changing code, not YAML.

```yaml
opportunity_definition:
  tier: A
  ref: "code:luvoire.theory.rat.v1"
```

The `ref` string must match `^code:[a-z_][a-z0-9_.]*\.v\d+$`. The pointed-to module is checked at lint time, not runtime.

### Tier B — Empirical prior

Required source metadata, plus either a single `value` or a `distribution` reference. Optional `range` + `default` allowed for prior bracketing during sensitivity analysis.

```yaml
schedule_prior:
  tier: B
  source: "KOSTAT 2024 생활시간조사"
  table_id: "T-08"
  license: "KOGL Type 1"
  revision: "2024-12-17"
  url: "https://mdis.mods.go.kr/..."
  value: 0.42
  description: "Time-use prior weight for a 30s urban commuter strata."
```

```yaml
schedule_distribution:
  tier: B
  source: "KOSTAT 2024 생활시간조사"
  distribution: "parquet:data/priors/timeuse_v1.parquet#strata=urban_30s"
```

`source` must be non-empty. Either `value` or `distribution` is required.

### Tier C — Exploration knob

Required `range` + `default`, optional `sweep` integer. Tooling such as SALib and Optuna consumes the `range` directly.

```yaml
guardianship_density:
  tier: C
  range: [0.1, 0.9]
  sweep: 9
  default: 0.5
  description: "Place-level capable guardianship density (synthetic units)."
```

`range[0] < range[1]` and `range[0] <= default <= range[1]` are enforced.

## GIS readiness (optional)

Two new optional fields on `environment`:

- `h3_cell`: an [H3 v4](https://h3geo.org/) string index (15 hex characters). Lets a scenario pin to a synthetic hex cell.
- `epsg`: a coordinate-system label. Under the default `ethics.no_real_geometry: true`, only labels starting with `luvoire-synthetic-` are accepted; any real EPSG code (e.g. `EPSG:5174`) raises a validation error.

```yaml
environment:
  start_time: "2026-04-23T19:00:00"
  location_path: ["Luvoire Demo World", "Seoul-style Synthetic Grid", "Plaza A"]
  h3_cell: "8830e1ad81fffff"
  epsg: "luvoire-synthetic-v1"
```

## Ethics extension

`EthicsSpecV2` adds `no_real_geometry: bool = True` on top of v1's `fictional`, `no_real_people`, `no_prediction`, `no_suspect_scoring`. The disallowed-purpose phrase set is extended with `individual risk score`, `real address`, `real coordinate`, and `real-world prediction`. These guardrails align with the project [Civilian Use Policy](https://github.com/Celovin/luvoire/blob/main/POLICIES/civilian_use.md) categorical refusals.

## Lint

`scripts/lint_dsl_v2.py` walks YAML files and reports tier inconsistencies. Strict mode exits non-zero on any issue:

```bash
python scripts/lint_dsl_v2.py scenarios/library/ examples/scenarios/ --strict
```

The lint script skips `schema_version: "1.0"` files and only enforces v2 rules on v2 scenarios.

## JSON Schema export

```python
from luvoire.dsl.v2 import scenario_v2_json_schema
import json

schema = scenario_v2_json_schema()
print(json.dumps(schema, indent=2))
```

The committed copy lives at `schemas/scenario_v2.json`. Regenerate it before pushing if the Pydantic models change.

## Related

- [Scenario DSL v1 to v2 Migration](migration-v1-to-v2.md)
- [Scenario DSL v2 Design Spec](v2-design-spec.md)
- [Scenario DSL v1 Reference](reference.md)
- [Civilian Use Policy](https://github.com/Celovin/luvoire/blob/main/POLICIES/civilian_use.md)
