# ODD Protocol Export

Luvoire can export a scenario-derived ODD protocol markdown draft:

```bash
python -m luvoire.cli export odd examples/scenarios/gangnam_7pm.yaml --out odd_report.md
```

The exporter is a pure code-to-markdown transformation. It loads Scenario DSL YAML, builds the corresponding Luvoire simulator, extracts machine-derivable fields, and leaves author-written sections as explicit TODO stubs.

```python
from pathlib import Path

from luvoire.dsl import load_scenario
from luvoire.export.odd import populate_from_simulation, render_markdown

scenario = load_scenario("examples/scenarios/gangnam_7pm.yaml")
simulator = scenario.to_simulator()
report = populate_from_simulation(simulator, scenario)
Path("odd_report.md").write_text(render_markdown(report), encoding="utf-8")
```

The seven canonical sections are:

1. Purpose and Patterns
2. Entities, State Variables, and Scales
3. Process Overview and Scheduling
4. Design Concepts
5. Initialization
6. Input Data
7. Submodels

The reference protocol is Grimm et al. 2020, JASSS 23(2) 7: <https://www.jasss.org/23/2/7.html>.
