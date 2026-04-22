# Configuration

Luvoire has two common configuration paths:

- Python object construction for scripts and notebooks.
- YAML scenario files for repeatable CLI and DSL workflows.

## Runtime Package Config

Use `load_config` when you want package-level settings from a YAML file plus environment overrides.

::: luvoire.config.LuvoireConfig

::: luvoire.config.load_config

## Scenario Config

Scenario DSL files define agents, environment, events, duration, and safety metadata in YAML.

```python
from luvoire.dsl import load_scenario

scenario = load_scenario('examples/scenarios/01_shopkeeper_winter_crime.yaml')
logs = scenario.to_simulator().run(duration_days=scenario.duration_days)
```

See the scenario guide:

- `docs/dsl/tutorial.md`
- `docs/dsl/reference.md`
- `schemas/scenario_v1.json`

## Provider Keys

Keep provider keys in environment variables or per-session UI input. Do not commit `.env` files, API keys, or generated credentials.
