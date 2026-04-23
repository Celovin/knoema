# Night Report - Luvoire Research Hardening v1 - 2026-04-23

Status: interim report after Slot C. Slot D remains pending and this file should be updated again after Slot D closes.

Baseline:

- v7 code merge prerequisite satisfied by descendant history from `a667d7249219e1960775c0a60ea770cb1dee3143`.
- v7 Slot E HF Space runtime rebuild remains an external waived blocker for this handoff only.
- Working directory: `C:\Users\admin\Projects\knoema`.

## Slot A - Response-cache layer in core

Status: closed and pushed.

Commits:

- `52e365ed2e3a4bcbb5cdc090c309f9d6aac6ad1a` - `feat(core): add replay cache for deterministic LLM side-effects`
- `588fbc5` - `docs(planning): record slot a replay cache completion`

Verification summary:

- Full pytest: 694 passed, 5 skipped.
- Ruff, mypy, encoding guard, Gradio compatibility, Plotly enum safety, mkdocs strict, replay SHA verification, and replay-cache inspect all passed.
- Replay SHA baselines remained unchanged.

## Slot B - Mesa 3 adapter + ODD markdown exporter

Status: closed and pushed.

Commits:

- `baa9418a83d7760dcf5bba01883e6595d6f01a05` - `feat(adapters+export): add Mesa 3 adapter and ODD protocol exporter`
- `3171c25` - `docs(planning): record slot b mesa odd completion`

Verification summary:

- Full pytest: 700 passed, 5 skipped.
- `pytest tests/test_mesa_adapter.py tests/test_odd_exporter.py --no-cov`: 6 passed.
- Ruff, mypy, encoding guard, Gradio compatibility, Plotly enum safety, mkdocs strict, replay SHA verification, and ODD CLI export all passed.
- `pip install -e ".[mesa]"` passed after removing a duplicate Hatch package entry for `src/luvoire`.
- Replay SHA baselines remained unchanged.

## Slot C - Civilian-only use policy

Status: closed; implementation commit recorded and this report commit follows.

Commit:

- `001f71c63b3175a350c63f849c6e7d5fa086fef2` - `feat(policy): publish Civilian Use Policy v1.0`

Verification summary:

- Full pytest: 700 passed, 5 skipped.
- Ruff, mypy, encoding guard, Gradio compatibility, Plotly enum safety, mkdocs strict, and replay SHA verification all passed.
- `POLICIES/` contains exactly `civilian_use.md` and `civilian_use.ko.md`.
- `Civilian Use` links are present in `README.md`, `README.ko.md`, `site-snapshot/index.html`, and `website/components/LuvoireLanding.tsx`.
- `website/public/pricing.html` has no mirrored Company footer column, so no edit was required.
- User approved the KO translation in session before commit.
- Replay SHA baselines remained unchanged.

## Slot D

Status: pending.

Next required slot: Nemotron-Personas multi-country loader + Luvoire Persona Interface v1.

## Dirty State Preserved

The following pre-existing user dirty/untracked state was left untouched:

- `planning/codex_blockers.md`
- `sdk/ios/KnoemaMobile/`
