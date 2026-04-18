# CLI Reference

The `knoema` CLI runs deterministic YAML-driven simulations.

## Run A Config

```bash
knoema run examples/cli_dorm.yaml --json
```

## Override Output

```bash
knoema run examples/cli_dorm.yaml --output runs/dorm.jsonl --json
```

## Dry Run

```bash
knoema run examples/cli_dorm.yaml --dry-run --json
```

## Source Reference

::: knoema.cli.main
