# CLI Reference

The `luvoire` CLI runs deterministic YAML-driven simulations.

## Run A Config

```bash
luvoire run examples/cli_dorm.yaml --json
```

## Override Output

```bash
luvoire run examples/cli_dorm.yaml --output runs/dorm.jsonl --json
```

## Dry Run

```bash
luvoire run examples/cli_dorm.yaml --dry-run --json
```

## Source Reference

::: luvoire.cli.main
