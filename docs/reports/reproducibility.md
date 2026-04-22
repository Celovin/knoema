# Reproducibility Report

## Scope

Phase 21 documents the reproducibility guarantees currently exercised by the public test suite. The goal is not to claim that every future model provider is deterministic. The guarantee is narrower and operational: when a run uses a fixed config, fixed seed, deterministic local response policy, and canonical JSONL export, Luvoire can reproduce the same observable behavior and replay summary.

## Method

The tests under `tests/reproducibility/` cover four surfaces:

1. Ten repeated runs with the same seed produce one stable log hash and one stable canonical memory hash.
2. Changing the seed changes persona goals, environment conditions, and action content.
3. YAML scenario configs round-trip through the CLI schema without losing fields.
4. JSONL logs restore the same action count, agent set, tick set, timestamps, and relationship edge summary.

The canonical memory hash intentionally excludes runtime UUID values. Current short-term memories receive UUID identifiers at write time, while the replay-relevant memory payload is the timestamped content, type, importance, and agent owner.

## Results

The local Phase 21 verification passes as part of the standard suite:

```powershell
.venv\Scripts\python -m pytest tests\reproducibility
```

The full suite also passes with the reproducibility tests enabled:

```powershell
.venv\Scripts\ruff check .
.venv\Scripts\mypy src
.venv\Scripts\python -m pytest
```

## Guarantees

- Fixed deterministic local policy produces stable exported JSONL logs.
- Fixed deterministic local policy produces stable canonical short-term memory payloads.
- Config serialization preserves the scenario contract used by `luvoire run`.
- Replay summaries can be restored from JSONL without the original simulator object.
- Public artifacts can be scanned for entity separation and encoding issues independently of ignored private planning files.

## Limits

External LLM providers can change outputs, latency, and tokenization. For provider-backed reproducibility, record provider name, model name, prompt language, config hash, request parameters, dependency versions, and raw JSONL output. The current guarantee is strongest for deterministic local runs and offline replay.
