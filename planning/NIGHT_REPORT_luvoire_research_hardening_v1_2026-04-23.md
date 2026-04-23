# Night Report - Luvoire Research Hardening v1 - 2026-04-23

Status: final report after Slot D. Slots A-D are closed; this report commit follows the Slot D implementation commit.

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

## Slot D - Nemotron-Personas multi-country loader + LPI v1

Status: closed; implementation commit recorded and this report commit follows.

Commit:

- `04177d34aff36db2262c47b864a0f46d8dc43349` - `feat(personas): add multi-country Nemotron loader and Luvoire Persona Interface v1`

Files changed:

- `CHANGELOG.md`, `README.md`, `mkdocs.yml`, `pyproject.toml`
- `docs/personas/countries.md`, `docs/personas/lpi.md`
- `src/luvoire/cli.py`
- `src/luvoire/persona/nemotron_loader.py`
- `src/luvoire/personas/` including LPI v1, JSON schema, registry, shared Nemotron loader, and seven country mapping modules
- `tests/fixtures/personas/` synthetic parquet fixtures and LPI golden fixture
- `tests/test_personas_lpi.py`, `tests/test_personas_loaders.py`, `tests/test_personas_hf_smoke.py`

Verification summary:

- `pip install -e ".[personas]"` passed.
- Full pytest: 708 passed, 6 skipped.
- Persona tests: 8 passed.
- HF live smoke: 1 skipped by default with `LUVOIRE_HF_LIVE` skip reason.
- Ruff, mypy, encoding guard, Gradio compatibility, Plotly enum safety, mkdocs strict, replay SHA verification, LPI schema export, CLI list, and fixture-backed CLI sample all passed.
- `python scripts/verify_replay_shas.py`: verified 5 replay SHA256 baselines.
- `rg -n "Nemotron-Personas-" src/luvoire`: found attribution strings for all seven countries.
- Staged added-line forbidden-token sweep found no new legacy brand-token hits; broad staged-path grep only returned pre-existing historical `CHANGELOG.md` allowlist hits.
- Replay SHA baselines remained unchanged.

Final LPI v1 field list:

`persona_id`, `country_iso`, `language_locale`, `age`, `sex`, `region_l1`, `region_l2`, `education_isced`, `occupation_isco08`, `income_bracket_oecd`, `household_size`, `marital_status`, `big5`, `narrative_text`, `grounding_source`, `grounding_version`, `distortion_flags`, `extras`.

Notes:

- The Korea-only legacy path remains callable and now carries a deprecation marker for new cross-country callers.
- No upstream persona data was vendored; test fixture shards are hand-crafted synthetic rows.
- Loader and LPI code do not call an LLM.

## Handoff Close

All four research-hardening slots are implemented in repository code, gated locally, committed, and ready to push.

Suggested next-handoff candidates:

- Slot E: C2PA 2.2 manifest emission on replay artifacts before the 2026-08-02 EU AI Act transparency deadline.
- Slot F: PIPA re-identification-risk evaluator for persona pipelines before the 2026-09-11 enforcement change.
- Slot G: A-MEM optional plugin behind `luvoire[amem]`, now safer because Slot A replay cache exists.
- Slot H: LongMemEval-S run with gpt-4o reader, target 80-85% overall for publication collateral.
- Slot I: HugAgent cross-domain belief-transfer experiment after Slot G.
- Slot J: Nemotron-Personas-Germany custom build using ALLBUS + Destatis.
- Slot K: cross-country migration-scenario reference simulation using LPI as input.

## Dirty State Preserved

The following pre-existing user dirty/untracked state was left untouched:

- `planning/codex_blockers.md`
- `sdk/ios/KnoemaMobile/`
