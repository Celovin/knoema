# Migration from Knoema to Luvoire

Luvoire is the active product, package, CLI, documentation, website, and SDK name.
Knoema remains only as a temporary compatibility layer for existing Python imports
and environment variables.

## What Changed

Use the Luvoire names for new work:

| Legacy | Current |
| --- | --- |
| `knoema` Python import | `luvoire` Python import |
| `knoema` CLI | `luvoire` CLI |
| `KNOEMA_*` environment variables | `LUVOIRE_*` environment variables |
| Knoema SDK or adapter names | Luvoire SDK or adapter names |

The public docs, website, SDK paths, adapter paths, and benchmark reports should
not use the legacy product name outside this migration note and historical
records.

## Python Imports

Replace legacy imports:

```python
from knoema import Persona, Simulator
```

with current imports:

```python
from luvoire import Persona, Simulator
```

For the 0.3.x line, `import knoema` still redirects to `luvoire` and emits a
`DeprecationWarning`. This keeps existing notebooks and demos from failing while
callers move to the new package name.

## Environment Variables

Use `LUVOIRE_*` names in new deployments:

```powershell
$env:LUVOIRE_API_KEY = "..."
$env:LUVOIRE_METRICS_ENABLED = "1"
$env:LUVOIRE_OTEL_EXPORTER = "http://localhost:4318/v1/traces"
$env:LUVOIRE_SCENARIO_DIR = "scenarios"
$env:LUVOIRE_TTS_CACHE_DIR = "runs/tts-cache"
```

The matching `KNOEMA_*` variables remain accepted for the 0.3.x line when no
`LUVOIRE_*` value is set. They emit a deprecation warning and should not be used
in new examples, docs, CI, or production settings.

## CLI

Use `luvoire` commands:

```powershell
luvoire run examples/cli_dorm.yaml --json
luvoire validate scenarios/library --json
luvoire score experiments/50_agent_village/results/sim_log.jsonl
```

Do not add new docs, scripts, screenshots, or release material that use the
legacy CLI name.

## Compatibility Window

The compatibility layer is limited to the 0.3.x line.

- 0.3.x: legacy imports and `KNOEMA_*` variables work with deprecation warnings.
- 0.4.0 or the next breaking release: legacy imports and `KNOEMA_*` variables may
  be removed.

Before removing compatibility, update the release notes, remove the shim package
entries, and run a wheel install smoke test that confirms the intended behavior.

## Maintainer Checklist

Before each release, verify:

```powershell
git grep -n -I -i "knoema" -- README.md README.*.md docs website playground dashboard saas sdk adapters unity-sdk benchmarks mkdocs.yml .github
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m pytest tests\test_v7_rename_sweep.py tests\test_phase62_release.py --no-cov -q
.venv\Scripts\python.exe scripts\release_dry_run.py --version 0.3.0
```

The grep may return this migration file. Any other product-surface result should
be treated as a rebrand regression unless it is a deliberate compatibility test
or historical record.
