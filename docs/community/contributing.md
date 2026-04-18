# Contributing

See the root `CONTRIBUTING.md` for the canonical contribution guide.

## Good First Contributions

- Reproducible examples.
- Scenario DSL samples with guardrails.
- Game-engine adapter tests.
- Documentation fixes.
- Benchmark critique with runnable alternatives.

## Local Checks

```bash
pytest
ruff check .
mypy src
```

## Documentation Checks

```bash
pip install -e '.[docs]'
mkdocs build
```
