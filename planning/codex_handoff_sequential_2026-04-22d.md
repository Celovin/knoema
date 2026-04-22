# Codex Sequential Handoff v4 - CAT-28 Full Expansion + Nemotron Integration

Author: Celovin (Choi Jihwan)
Date: 2026-04-22 (fourth handoff, bundled two-slot)
Working directory: `C:\Users\admin\Projects\knoema`
Deadline anchors: 황태정 대면 미팅 2026-04-23 (목) / 2026-04-27 (월); Didimdol grant 2026-04-29 18:00 KST (D-7).

Previous handoffs (all closed):
- `planning/codex_handoff_sequential_2026-04-21.md` - Slots 1-5 (arXiv / Bench / 1K PoC / Unity SDK / TTS) + CAT-28 pilot (8 archetypes).
- `planning/codex_handoff_sequential_2026-04-22.md` - Slots A-D (CAT-28 viewer grouping / HF Space warmup / grant one-pager / multilingual parity).
- `planning/codex_handoff_sequential_2026-04-22b.md` - 5K replay (commit `6f3ac76`).
- `planning/codex_handoff_sequential_2026-04-22c.md` - 10K replay (commit `c262c8f`).

Scope of v4: finish the CAT-28 personality taxonomy (20 remaining archetypes) and integrate Nemotron-Personas-Korea as an optional agent-seed source. Both slots are pre-Didimdol-submission with margin.

Reference URL for Nemotron orientation (not a citation target; Codex must verify via HF Hub): `https://huggingface.co/blog/nvidia/build-korean-agents-with-nemotron-personas`.

---

## 0. Execution Contract

### 0.1 Sequential Only

Slot A MUST close fully (all gates green, merged) before Slot B starts. No parallel.

### 0.2 Scope Guard

Inside `C:\Users\admin\Projects\knoema` only. Never touch:

- `C:\Users\admin\Projects\seizn*`
- `C:\Users\admin\Projects\knot`
- `C:\Users\admin\Projects\thelabforge`
- `C:\Users\admin\Projects\milkypix`
- `.codex/`, `.claude/`, Dendron vaults

Forbidden strings in any tracked file: `Litheon`, `Seizn`, `Ovriel`, `Fangden`, `Notrivo`, `Milkypix`, `Yami`, `Qwen3.5-35B-A3B`.

### 0.3 Environment Bootstrap

```bash
cd /c/Users/admin/Projects/knoema
export $(grep -v '^#' .env.local | xargs)
.venv/Scripts/python.exe -m pip install -e .[dev]
.venv/Scripts/python.exe -m pip install 'datasets>=2.18,<4.0'
```

Required env vars: `HF_TOKEN` (present in `.env.local`).

### 0.4 Hard Credential and Config Rules

Same as prior handoffs:

- Codex MUST NOT run `git remote set-url`, `gh auth switch`, `gh auth login`, `gh auth logout`.
- Codex MUST NOT modify `credential.*` keys in any git config scope.
- Codex MUST NOT add or modify files under `.git/`.
- Codex MUST NOT hand-type git SHAs. Use `git rev-parse HEAD` and verify with `git cat-file -e <sha>`.
- If `git push origin main` is denied, halt with `Slot X BLOCKED: git push denied despite permanent credential fix`.

### 0.5 Standard Verification Gate (runs at the end of each slot)

1. `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py` - all green.
2. `ruff check .` - clean.
3. `mypy src` - clean.
4. `python -m pytest tests/test_playground_encoding_guard.py` - pass.
5. `python scripts/check_gradio_compat.py` - pass.
6. `python -m pytest tests/test_plotly_enum_safety.py` - pass.
7. `git add <slot paths>` + `git commit -m "<slot commit message>"` + `git push origin main`.

Neither slot touches `playground/`. Skip HF Space gates.

### 0.6 Forbidden Regression

The following msgpack files MUST remain byte-identical at the end of v4. Any change = halt.

- `replay_100agents_gangnam_7pm.msgpack`: `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab`
- `replay_1000agents_gangnam_7pm.msgpack`: `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b`
- `replay_5000agents_gangnam_7pm.msgpack`: `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01`
- `replay_10000agents_gangnam_7pm.msgpack`: `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2`

### 0.7 Actions Reserved for the User

- Legal review beyond the §2.0 Nemotron license gate.
- Demo presentation to external stakeholders.
- Any communications with NVIDIA or Naver Cloud representatives.

### 0.8 Slot Completion Report

After each slot, append a section to `planning/codex_session_report_2026-04-22.md`. After the final slot, create `planning/NIGHT_REPORT_knoema_sequential_v4_2026-04-22.md`.

---

## 1. Slot A - CAT-28 Full Expansion (20 remaining archetypes)

Effort estimate: 1-2 hours.
Rationale: Session 1 shipped 8 CAT-28 Tier 5 archetypes (tsundere, kuudere, dandere, genki, chuunibyou, oneesan, yankee, intellectual). CAT-28 as a named set claims 28 entries (22 single + 6 composite). Completing the set before Didimdol lets the grant narrative claim "full CAT-28 taxonomy implemented as pedagogical personality overlays."

### 1.1 Inputs

- `demo/replay/profiles/personality_cat28/README.md` - namespace policy.
- `demo/replay/profiles/personality_cat28/CITATION.md` - bibliographic source file; extend with new citations where the existing 8 sources do not cover an added archetype.
- `demo/replay/profiles/personality_cat28/single/*.yaml` - 8 committed profiles (pattern and schema reference).
- `demo/replay/profiles/schema.yaml` - already accepts tier 5.
- `scripts/validate_profile.py` - already routes tier 5 to the CAT-28 CITATION.md lookup.

### 1.2 Archetypes to Add

**Remaining 14 single archetypes** (`demo/replay/profiles/personality_cat28/single/`):

1. `yandere.yaml` - obsessively devoted persona, possessive in-group protection pattern
2. `deredere.yaml` - openly affectionate, high-density sociability with low aggression
3. `undere.yaml` - compliant-agreement pattern, accommodation bias
4. `bakadere.yaml` - lovable-fool pattern, high error-tolerance recovery
5. `bokodere.yaml` - affection-via-roughness pattern, paradoxical proximity
6. `sadodere.yaml` - teasing-dominance pattern, status-play behavior
7. `himedere.yaml` - princess-complex pattern, status-demand behavior
8. `imouto.yaml` - younger-sibling-clinging pattern, dependency-seeking
9. `prince.yaml` - chivalric-charm pattern, gallant mediating behavior
10. `ojou.yaml` - refined-lady pattern, high-status register behavior
11. `trickster.yaml` - playful-mischief pattern, unpredictable path routing
12. `tomboy.yaml` - casual-direct pattern, high-mobility low-hierarchy behavior
13. `megane.yaml` - glasses-archetype pattern, analytical low-social-skill behavior
14. `bocchi.yaml` - extreme-introvert pattern, mediated-social behavior

**6 composite archetypes** (`demo/replay/profiles/personality_cat28/composite/`):

15. `bright_cheerful.yaml` - energy-positive gestalt
16. `cool_reliable.yaml` - composed-dependable gestalt
17. `shy_gentle.yaml` - considerate-retreating gestalt
18. `playful_teasing.yaml` - witty-provocative gestalt
19. `mature_mysterious.yaml` - reflective-enigmatic gestalt
20. `passionate_intense.yaml` - emotional-direct gestalt

### 1.3 Deliverables

1. **20 new profile yaml files** under the appropriate subdirectory. Each file MUST:
   - Follow the exact schema used by `tsundere.yaml` (archetype_id, tier=5, display_name, inspired_by, literature_sources, mo_rules, routine_patterns, target_criteria, geographic_behavior, ethical_disclaimer, contemporary_grid_translation).
   - Use the verbatim Tier 5 disclaimer: `This profile is a pedagogical personality overlay for replay scenarios. It does not model any real individual, group, or proprietary character. It must not be used for trait assignment to identifiable populations.`
   - Reference at least 2 literature sources per archetype, each with DOI / ISBN / ISSN; at least one identifier per archetype MUST already be listed in `CITATION.md` (extend `CITATION.md` if new sources are needed).
   - Never reference any Milkypix character, dataset, LoRA, training product, or any forbidden entity string.
   - Behavioral rules (`mo_rules`, `routine_patterns`, `geographic_behavior`) must be written independently from any proprietary character bible.

2. **`demo/replay/profiles/manifest.json`** - append 20 entries following the existing tier 5 format; preserve the existing 15 entries verbatim.

3. **`demo/replay/profiles/personality_cat28/CITATION.md`** - extend with any additional academic sources needed. Keep the same Monographs / Book Chapters / Journal Articles / Exclusions structure. Sources must be peer-reviewed or university-press monographs; no fan wikis, no AI-generated summaries.

4. **`demo/replay/profiles/personality_cat28/README.md`** - update the "Scope" section: the directory now ships 28 archetypes (22 single + 6 composite). Keep all Ethical Boundaries bullets unchanged.

5. **`demo/replay/viewer.html`** - scenario switcher / archetype injection dropdown:
   - Tier 5 group now shows 28 entries grouped into Single (22) and Composite (6) subheaders.
   - Ethics modal wording does not change.

6. **`tests/test_replay_viewer_groupings.py`** - update the expected Tier 5 count from 8 to 28 (22 single + 6 composite).

7. **`demo/replay/CHANGELOG.md`** - append a dated entry describing the CAT-28 full expansion.

### 1.4 Acceptance Criteria

- `python scripts/validate_profile.py "demo/replay/profiles/**/*.yaml"` exits 0 with 35 archetype files total (4 Tier 1 + 3 Tier 2 + 22 Tier 5 single + 6 Tier 5 composite).
- Every new profile has at least 2 `literature_sources` entries, each with DOI / ISBN / ISSN resolvable against `personality_cat28/CITATION.md`.
- No new profile yaml contains any forbidden-entity string.
- Forbidden-name scan continues to return 0 matches for the Tier 3/4 forbidden-name list (`Bundy`, `Kemper`, etc.).
- Replay viewer dropdown shows 28 Tier 5 entries correctly grouped.
- The four existing replay msgpack files remain byte-identical per §0.6.
- `mkdocs build --strict` passes.

### 1.5 Git

Commit message: `feat(profiles): complete CAT-28 tier 5 expansion (22 single + 6 composite)`
Paths: `demo/replay/profiles/personality_cat28/`, `demo/replay/profiles/manifest.json`, `demo/replay/viewer.html`, `tests/test_replay_viewer_groupings.py`, `demo/replay/CHANGELOG.md`, `CHANGELOG.md`.

---

## 2. Slot B - Nemotron-Personas-Korea Integration

Effort estimate: 2-4 hours.
Rationale: NVIDIA and Naver Cloud published `Nemotron-Personas-Korea` on HuggingFace Hub - 7M fully synthetic Korean personas grounded in KOSIS, 대법원, 국민건강보험공단, and 한국농촌경제연구원 public statistics. Integrating this as an optional agent-seed source lets Knoema claim "KOSIS-grounded demographic distribution" in the Didimdol narrative without breaking determinism, entity separation, or reproducibility of the existing deterministic-stub replays.

### 2.0 License Gate (REQUIRED before any use)

Before loading any Nemotron data or committing derived artifacts, Codex MUST:

1. Resolve the canonical dataset repo ID on HuggingFace Hub. Primary candidate: `nvidia/Nemotron-Personas-Korea`. If not found, search `HfApi().list_datasets(search='Nemotron-Personas-Korea')` and pick the official NVIDIA-owned one.
2. Fetch the dataset card via `HfApi().dataset_info(repo_id).card_data` and read the license field.
3. Record the exact license identifier (e.g., `cc-by-4.0`, `apache-2.0`, `nvidia-open-model-license`) into `docs/persona_seeding.md` §License.
4. If the license is NOT one of {`cc-by-4.0`, `cc-by-sa-4.0`, `apache-2.0`, `mit`, `odc-by`, any NVIDIA open-model variant that explicitly permits redistribution of derivatives}, halt with `Slot B BLOCKED: Nemotron license <x> requires manual legal review`. Do not ship derived artifacts.
5. If permissive, write `LICENSE-NEMOTRON.md` at repo root containing the dataset license text verbatim as published, plus a one-line attribution pointing to the dataset card URL and authors (NVIDIA, Naver Cloud).

### 2.1 Inputs

- `src/knoema/scaling/city_scale.py` - existing `CityScaleRunner`.
- `src/knoema/agents/` - canonical place demographics are stored; match its field names in the Nemotron mapping.
- `demo/replay/generate_replay.py` - existing replay generator with `--scenario {100,1k,5k,10k}`.
- `demo/replay/scenario_config_60x60.yaml` - 10K grid config.
- `demo/replay/replay_10000agents_gangnam_7pm.msgpack` - 10K deterministic-stub baseline (SHA `af326a00...`) which MUST NOT change.

### 2.2 Deliverables

1. `src/knoema/persona/__init__.py` + `src/knoema/persona/nemotron_loader.py`:
   - `NemotronPersonaSource(repo_id, cache_dir, hf_token)` class with:
     - `load(streaming=True)` - returns a HuggingFace streaming Dataset handle; never loads all 7M rows into memory.
     - `sample(n, seed, filters=None)` - returns exactly `n` persona dicts deterministically (same seed -> same persona IDs in same order). `filters` is an optional dict like `{region: 'Seoul', region_contains: 'Gangnam'}` applied via dataset `.filter(...)` before reservoir-sampling.
     - `to_agent_attributes(persona)` - maps Nemotron fields (age, gender, occupation, region, income) to Knoema agent attribute names. Map unknown / missing fields to existing defaults; do not invent values.
   - Pure-python, no Gradio import, no Plotly import. Must be mypy-clean and ruff-clean.

2. `src/knoema/persona/fixtures/nemotron_sample_512.jsonl` - a 512-row offline fixture snapshot captured from the live dataset at slot time, committed for:
   - Unit tests that don't need a live HF download.
   - Demo reproducibility in airgapped environments.
   - Size bound: ≤2 MB raw.

3. `demo/replay/generate_replay.py` updates:
   - Add `--persona-source {stub,nemotron}` argument (default `stub` to preserve existing byte-identical replays).
   - When `nemotron` is selected, fetch personas via `NemotronPersonaSource.sample(n, seed=<scenario_seed>, filters={region_contains: 'Gangnam'})` and attach them to each agent. The deterministic-stub path MUST remain untouched when `stub` is selected.
   - `--verify-existing` mode extended: for `stub`, assert existing SHAs (see §0.6). For `nemotron`, assert the new Nemotron-variant SHA recorded in the Slot B completion report.

4. `demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack` - new committed artifact:
   - 10000 agents, 30 simulated minutes, 60x60 grid, seeded from Nemotron personas filtered to Gangnam-region residents.
   - Same format as prior replays plus `metadata.persona_source = "nemotron"` and `metadata.persona_dataset_revision = "<HF dataset commit hash>"` (obtained via `HfApi().dataset_info(repo_id).sha`).
   - Size target: ≤25 MB.

5. `demo/replay/viewer.html` updates:
   - Scenario switcher gains a second axis: scale (100/1K/5K/10K) and persona source (stub/nemotron). For this slot, only `10K + nemotron` needs to be wired; other combinations remain stub-only.
   - When a Nemotron-seeded replay is loaded, the agent drill-down panel shows an additional `Persona source: Nemotron-Personas-Korea (sample from <revision>)` line (with `<revision>` replaced by the dataset commit hash at generation time).
   - The existing archetype injection, ethics modal, and hot-spot heatmap continue to work unchanged.

6. `tests/test_nemotron_persona_loader.py`:
   - Uses the committed `nemotron_sample_512.jsonl` fixture (no live HF download during CI).
   - Asserts deterministic sampling: `sample(n=50, seed=1234)` returns identical persona IDs across 3 runs.
   - Asserts field mapping: `to_agent_attributes(persona)` returns a dict with exactly the expected keys and no raw Nemotron field names leaked.
   - Asserts filter correctness: `filters={region_contains: 'Gangnam'}` yields only Gangnam-region rows from the fixture.
   - Asserts no forbidden-entity strings appear in any Nemotron-derived output.

7. `tests/integration/test_nemotron_live.py` (marked `@pytest.mark.slow` and skipped unless `KNOEMA_ENABLE_HF_NETWORK=1`):
   - Actually pulls a handful of rows from the live dataset.
   - Skipped in normal CI but runnable locally on demand.

8. `docs/persona_seeding.md` - user-facing doc:
   - §Overview - what Nemotron-Personas-Korea is.
   - §License - exact license identifier from the dataset card (§2.0 gate output).
   - §Citation - recommended citation block (Nemotron + KOSIS + Naver Cloud attribution).
   - §How to regenerate - CLI invocation.
   - §Scope and Limits - explicit note that this integration is for synthetic demographic seeding only; Knoema does NOT use Nemotron for any LLM fine-tuning or downstream model training in this repository.

9. `LICENSE-NEMOTRON.md` - per §2.0 step 5.

10. `README*.md` (all 8 locales) - append a one-line feature bullet referencing Nemotron integration. Translations must be in the target language, not English stubs.

11. `docs/scaling.md` - append a "Nemotron-seeded 10K demo" subsection.

12. `mkdocs.yml` - add `docs/persona_seeding.md` to the Reference section between `Playground Deploy` and `Didimdol One-Pager` entries.

### 2.3 Acceptance Criteria

- `python demo/replay/generate_replay.py --scenario 10k --persona-source stub --verify-existing` exits 0 (stub baseline byte-identical per §0.6).
- `python demo/replay/generate_replay.py --scenario 10k --persona-source nemotron --verify-existing` exits 0 against the newly committed Nemotron-variant SHA256.
- `replay_10000agents_nemotron_gangnam_7pm.msgpack` size ≤25 MB.
- Deterministic Nemotron sampling: regenerating the Nemotron-variant replay 3 times with the same seed produces byte-identical msgpack output (SHA256 compare).
- Existing replay SHA256 values unchanged per §0.6.
- `pytest tests/test_nemotron_persona_loader.py` passes offline (no network).
- `LICENSE-NEMOTRON.md` present and contains the verbatim dataset license text.
- `docs/persona_seeding.md` §License field matches the license Codex recorded at §2.0 step 3.
- Forbidden-entity scan on the diff: 0 matches.
- `mkdocs build --strict` passes with the new doc registered in nav.

### 2.4 Git

Commit message: `feat(persona): integrate nemotron-personas-korea as optional agent seed`
Paths: `src/knoema/persona/`, `demo/replay/generate_replay.py`, `demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack`, `demo/replay/viewer.html`, `tests/test_nemotron_persona_loader.py`, `tests/integration/test_nemotron_live.py`, `docs/persona_seeding.md`, `docs/scaling.md`, `LICENSE-NEMOTRON.md`, `mkdocs.yml`, `README.md`, `README.de.md`, `README.es.md`, `README.fr.md`, `README.ja.md`, `README.ko.md`, `README.zh-CN.md`, `README.zh-TW.md`, `CHANGELOG.md`.

---

## 3. Global Completion Report

After Slot B passes, create `planning/NIGHT_REPORT_knoema_sequential_v4_2026-04-22.md` with:

```markdown
## Handoff v4 - Completion (YYYY-MM-DD)

### Slot A: CAT-28 full expansion
- Commit: <sha>
- Profile count: 28 (22 single + 6 composite)
- Validator exit: 0

### Slot B: Nemotron persona integration
- Commit: <sha>
- License recorded: <license identifier>
- Dataset revision pinned: <HF dataset commit hash>
- Nemotron-variant 10K replay SHA256: <sha>

### Full gates
- pytest final: N passed, M skipped
- Ruff: clean
- Mypy: clean
- Forbidden-entity scan: 0 matches
- Regression baseline SHAs (§0.6): all 4 unchanged
```

---

## 4. What This Handoff Does NOT Include

- Regeneration of existing 100 / 1K / 5K / 10K replays (byte-identical per §0.6).
- LLM fine-tuning on Nemotron data (explicitly excluded in `docs/persona_seeding.md`).
- Uploading Nemotron-derived artifacts to any third-party platform.
- HF Space upload (Nemotron replay is local demo only).
- 10K was completed in prior handoff `codex_handoff_sequential_2026-04-22c.md`; not re-done here.

---

## 5. Stop Conditions

Halt immediately if:

1. §2.0 License gate fails (license not in the permissive allowlist, or dataset card unreadable).
2. Standard gate fails non-transient.
3. `git push origin main` denied despite permanent credential fix.
4. Nemotron-variant 10K msgpack exceeds 25 MB.
5. Nemotron sampling is non-deterministic.
6. Any §0.6 forbidden-regression SHA changes.
7. Forbidden-entity scan returns any match.
8. `.env.local` missing or `HF_TOKEN` unset.
9. Any CAT-28 new profile fails schema validation (tier, disclaimer, or citation rules).
10. Effort per slot exceeds 6 hours.

On halt: write reason, current slot (A or B), reproduction command, last-good SHA, and observed dataset revision (if Slot B) to `planning/codex_blockers.md` and return to the user.
