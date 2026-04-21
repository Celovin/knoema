# Codex Sequential Handoff - Demo Readiness + Didimdol Artifacts

Author: Celovin (Choi Jihwan)
Date: 2026-04-22
Working directory: `C:\Users\admin\Projects\knoema`
Deadline anchors: 황태정 대면 미팅 2026-04-23 (목) 또는 2026-04-27 (월); Didimdol grant 2026-04-29 18:00 KST (D-7).
Previous handoff: `planning/codex_handoff_sequential_2026-04-21.md` (all 5 slots closed; see `planning/NIGHT_REPORT_knoema_sequential_2026-04-21.md`).

---

## 0. Execution Contract

### 0.1 Sequential Only - No Parallel Dispatch

Slots MUST be executed one at a time, in the order listed in §1-§4. Do NOT start Slot N+1 until Slot N has passed every acceptance gate and been merged. Parallel Codex runs have produced cross-task contamination in this repository; this is a hard constraint, not a preference.

If a slot blocks, stop the entire pipeline, write the blocker to `planning/codex_blockers.md`, and return to the user. Do not skip ahead.

### 0.2 Scope Guard

This handoff operates only inside `C:\Users\admin\Projects\knoema`. Never touch:

- `C:\Users\admin\Projects\seizn*`
- `C:\Users\admin\Projects\knot`
- `C:\Users\admin\Projects\thelabforge`
- `C:\Users\admin\Projects\milkypix`
- `.codex/`, `.claude/`, Dendron vaults

Forbidden strings in any tracked file: `Litheon`, `Seizn`, `Ovriel`, `Fangden`, `Notrivo`, `Milkypix`, `Yami`, `Qwen3.5-35B-A3B`.

### 0.3 Environment Bootstrap

Run once before the first slot, and re-verify before each subsequent slot:

```bash
cd /c/Users/admin/Projects/knoema
export $(grep -v '^#' .env.local | xargs)
.venv/Scripts/python.exe -m pip install -e .[dev,paper,release]
```

Required env vars: `HF_TOKEN`, `OPENAI_API_KEY`. `PYPI_TOKEN` is only needed for release tags (out of scope here).

### 0.4 Hard Credential and Config Rules

The user applied a permanent credential fix on 2026-04-22. See `planning/codex_blockers.md` "Policy Note - Codex Must Not Change Credential Config". Summary:

- Codex MUST NOT run `git remote set-url`, `git remote add`, or otherwise rewrite the origin remote.
- Codex MUST NOT run `gh auth switch`, `gh auth login`, `gh auth logout`.
- Codex MUST NOT modify `credential.*` keys in any git config scope.
- Codex MUST NOT add or modify files under `.git/`.
- Codex MUST NOT hand-type git SHAs. Any SHA written into a file must be obtained via `git rev-parse HEAD` or `git log --format=%H -1` and verified with `git cat-file -e <sha>` before the file is committed.
- If `git push origin main` is denied, halt with `Slot N BLOCKED: git push denied despite permanent credential fix`. Do not attempt credential workarounds.

### 0.5 Standard Verification Gate (applies to every slot)

After finishing a slot's implementation, run the full 11-step gate before moving on:

1. `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py` - all green.
2. `ruff check .` - clean.
3. `mypy src` - clean.
4. `python -m pytest tests/test_playground_encoding_guard.py` - pass.
5. `python scripts/check_gradio_compat.py` - pass.
6. `python -m pytest tests/test_plotly_enum_safety.py` - pass.
7. `git add <slot paths>` + `git commit -m "<scoped message>"` + `git push origin main`.
8. For playground changes only: `python scripts/deploy_playground_space.py`.
9. Wait 90-120s, then assert `HfApi().space_info('celovin/knoema-playground').runtime.stage == 'RUNNING'`.
10. `curl -sI https://huggingface.co/spaces/celovin/knoema-playground | head -1` -> `HTTP/... 200`.
11. `python -m pytest tests/integration/test_live_space_smoke.py` - pass, and HF Space `/api/spaces/.../logs/run` last 50 lines grep `Traceback|Error|gradio.exceptions|TypeError|ValueError` -> 0 matches.

Skip steps 8-11 for slots that do not touch `playground/`.

### 0.6 Slot Completion Report

After each slot passes all gates, append a section to `planning/codex_session_report_2026-04-22.md` (create if it does not exist) with:

- Slot name and scope.
- GitHub commit SHA(s).
- HF Space SHA + stage (if applicable).
- Full-gate pytest / ruff / mypy results.
- One-line proof of the slot's acceptance criterion.

Then immediately proceed to the next slot. Do not wait for user confirmation between slots.

### 0.7 Actions Reserved for the User (Do Not Attempt)

- arXiv submission button and endorsement request email.
- Actually uploading the generated didimdol-onepager PDFs to the grant portal.
- Scheduling / sending messages to 황태정 or any other faculty member.
- Legal / trademark / patent filings.
- Modifying `portfolio-entity-mapping.md` or any Celovin/Litheon/Ovriel entity documents.

Prepare artifacts for these, but do not submit on the user's behalf.

---

## 1. Slot A - CAT-28 Viewer Integration

Effort estimate: 2-3 hours.
Rationale: On 2026-04-22, 8 CAT-28 tier 5 profiles were added under `demo/replay/profiles/personality_cat28/single/` and validated against an updated schema. The replay viewer's "Inject archetype" dropdown must render these under a visually distinct section so demo operators can separate criminology overlays from personality overlays during the 황태정 meeting.

### 1.1 Inputs

- `demo/replay/viewer.html` - existing archetype injection UI.
- `demo/replay/profiles/manifest.json` - archetype registry with tier field.
- `demo/replay/profiles/personality_cat28/README.md` - namespace documentation.
- `demo/replay/profiles/personality_cat28/single/*.yaml` - 8 profile files already committed.
- Commit `8b558b008286ebcd4e1f3f41558f27c2442453c4` - CAT-28 introduction reference.

### 1.2 Deliverables

1. `demo/replay/viewer.html` - dropdown rendering update:
   - Three grouped sections rendered as `<optgroup>` or equivalent, in this order: (a) `Criminology - Tier 1`, (b) `Criminology - Tier 2 Historical`, (c) `Personality - CAT-28 (Tier 5)`.
   - Visual separator between criminology groups and personality group (hairline rule or heavier label).
   - Tier 5 entries append `(pedagogical)` suffix to display_name in the dropdown.
   - Ethics modal text extended: when a tier 5 archetype is selected for the first time in a session, the modal includes an additional paragraph distinguishing personality overlays from criminology overlays.
2. `demo/replay/viewer_test.html` - a minimal self-test page that opens `viewer.html` in an iframe and asserts all 15 archetypes (4 Tier 1 + 3 Tier 2 + 8 Tier 5) appear in the dropdown.
3. `tests/test_replay_viewer_groupings.py` - headless Playwright test that loads `viewer.html` via `file://`, reads the dropdown DOM, and verifies group labels and per-group counts.
4. `demo/replay/CHANGELOG.md` - append a dated entry describing the tier 5 rollout.

### 1.3 Acceptance Criteria

- Opening `demo/replay/viewer.html` in Chrome via `file://` (no network) shows the three groups with correct counts (4, 3, 8).
- Selecting any tier 5 archetype triggers the ethics modal with the personality-specific paragraph; dismissing the modal enables the "Inject" button.
- Playwright test passes locally.
- Forbidden-entity scan on the diff: 0 matches for the forbidden string list in §0.2.

### 1.4 Git

Commit message: `feat(replay-viewer): group CAT-28 tier 5 archetypes in inject dropdown`
Paths: `demo/replay/viewer.html`, `demo/replay/viewer_test.html`, `tests/test_replay_viewer_groupings.py`, `demo/replay/CHANGELOG.md`.

---

## 2. Slot B - HF Space Cold-Start Warmup and Cache Bust

Effort estimate: 3-4 hours.
Rationale: Slot 5 (OpenAI TTS) failed twice on HF Space deploy because the HF pip cache returned a stale `knoema-engine` build missing the newly added `knoema.multimodal` module. The user-side resolution was a manual SHA repin. This slot replaces the manual step with a scripted cache-bust plus runtime warmup, so future `playground/` changes deploy cleanly on the first attempt.

### 2.1 Inputs

- `scripts/deploy_playground_space.py` - existing deploy wrapper.
- `playground/requirements.txt` - current dependency pins.
- `tests/integration/test_live_space_smoke.py` - existing smoke test.
- `planning/codex_blockers.md` Slot 5 RESOLVED entry (root cause narrative).

### 2.2 Deliverables

1. `scripts/warm_space.py` - new script that:
   - Accepts `--repo-id celovin/knoema-playground` argument.
   - Polls `HfApi().space_info(repo_id).runtime.stage` every 10 seconds until `RUNNING`, `RUNTIME_ERROR`, or `BUILD_ERROR`, with a 10-minute hard cap.
   - On `RUNNING`, fires a single `GET` against the Space URL root and asserts HTTP 200.
   - On any error stage, fetches last 50 lines of `/api/spaces/<repo_id>/logs/run`, prints them, and exits non-zero.
   - On timeout, exits non-zero with the last observed stage and transition history.
2. `scripts/deploy_playground_space.py` - augment with:
   - `--ensure-fresh-install` flag. When set, before uploading, read the current HEAD SHA via `git rev-parse HEAD`, verify it with `git cat-file -e`, and rewrite `playground/requirements.txt` to pin `knoema-engine` to that SHA. Fail loudly if the SHA cannot be verified.
   - `--factory-reboot-on-pyproject-change` flag. When set, if the current deploy changes `pyproject.toml` or `playground/requirements.txt` versus the previous HF Space SHA's snapshot, call `HfApi().restart_space(repo_id, factory_reboot=True)` immediately after the upload.
   - Call `scripts/warm_space.py` at the end of every deploy and propagate its exit code.
3. `tests/test_warm_space.py` - unit tests using mocked `HfApi` that verify the state machine (BUILDING -> APP_STARTING -> RUNNING, and each error path).
4. `docs/playground-deploy.md` - user-facing doc describing the new flags, the cache-bust rationale (short narrative), and the two exit codes.

### 2.3 Acceptance Criteria

- Running `python scripts/deploy_playground_space.py --ensure-fresh-install --factory-reboot-on-pyproject-change` on a clean working tree succeeds end-to-end: uploads, reboots if needed, polls until `RUNNING`, hits HTTP 200, and exits 0.
- `python scripts/warm_space.py --repo-id celovin/knoema-playground` exits 0 within 10 minutes against the live Space.
- Unit tests pass with 100% coverage of the three terminal states.
- `playground/requirements.txt` SHA after deploy matches `git rev-parse HEAD` at deploy time.
- No hand-typed SHA appears anywhere in the diff (SHAs come from `git rev-parse` only).

### 2.4 Git

Commit message: `feat(playground-deploy): add warmup, cache-bust, and factory-reboot flags`
Paths: `scripts/warm_space.py`, `scripts/deploy_playground_space.py`, `tests/test_warm_space.py`, `docs/playground-deploy.md`, `CHANGELOG.md`.

---

## 3. Slot C - Didimdol One-Pager Generation

Effort estimate: 4-6 hours.
Rationale: Didimdol submission on 2026-04-29 requires a bilingual one-page summary suitable for a grant reviewer's first-page glance. The 2026-04-23 faculty meeting also benefits from a paper handout. This slot automates the one-pager build from existing repository sources so it stays in sync with paper / benchmarks / release notes.

### 3.1 Inputs

- `paper/main.tex` - abstract, introduction, contributions.
- `paper/references.bib` - preprint metadata.
- `benchmarks/memory_benchmark_integration/results/summary.json` - latest benchmark numbers.
- `benchmarks/city_scale_1k_report.md` - 1K-agent proof of concept report.
- `docs/bench/leaderboard.md` - Knoema Bench first-row metrics.
- `README.md` - feature bullets, architecture overview.

### 3.2 Deliverables

1. `scripts/build_grant_summary.py` - emits two PDFs into `dist/`:
   - `dist/didimdol_onepager_ko.pdf`
   - `dist/didimdol_onepager_en.pdf`
   - Single page each, A4, 10 mm margins.
   - Sections: (a) title + one-line product description, (b) triple-use narrative block (pedagogical criminology / reproducibility research / game-studio demo), (c) top 3 benchmark numbers with source citation, (d) 1K-agent scale proof one-liner, (e) HF Space URL (QR code encoded), (f) arXiv placeholder line reading `arXiv:<pending>` until the user fills it.
2. `scripts/grant_summary_templates/` - Jinja2 templates for the Korean and English outputs, plus a shared typography and color-palette include.
3. `tests/test_build_grant_summary.py` - verifies the script runs, both PDFs are produced, each has exactly 1 page, and the filesize is within 50-400 KB (sanity bound).
4. `docs/didimdol-onepager.md` - short user doc: how to rebuild, how to fill the arXiv placeholder, how to swap the HF Space URL if the Space is re-hosted.

### 3.3 Acceptance Criteria

- `python scripts/build_grant_summary.py` produces both PDFs with `PyPDF2.PdfReader` reporting `len(pages) == 1` for each.
- All claimed benchmark numbers on the one-pager trace back to a specific file path and line/JSON key committed in this repository; no fabricated numbers.
- Bilingual content parity: the KO and EN one-pagers cover the same five sections with matching numeric values.
- Running the script twice on an unchanged tree produces byte-identical PDFs when `SOURCE_DATE_EPOCH` is fixed (deterministic output).
- Forbidden-entity scan on `dist/*.pdf` text extraction and on `scripts/grant_summary_templates/`: 0 matches.

### 3.4 Git

Commit message: `feat(grant): auto-build didimdol bilingual onepager`
Paths: `scripts/build_grant_summary.py`, `scripts/grant_summary_templates/`, `dist/didimdol_onepager_ko.pdf`, `dist/didimdol_onepager_en.pdf`, `tests/test_build_grant_summary.py`, `docs/didimdol-onepager.md`, `CHANGELOG.md`.

---

## 4. Slot D - Multilingual Locale Parity

Effort estimate: 2-3 hours.
Rationale: The repository ships README.de / es / fr / ja / ko / zh-CN / zh-TW alongside the English README. Recent Slot 3-5 work added feature bullets in English only and let a few locales drift. This slot detects drift and synchronizes.

### 4.1 Inputs

- `README.md` - canonical English.
- `README.de.md`, `README.es.md`, `README.fr.md`, `README.ja.md`, `README.ko.md`, `README.zh-CN.md`, `README.zh-TW.md` - localized siblings.

### 4.2 Deliverables

1. `scripts/check_readme_parity.py` - compares top-level heading counts, feature bullet counts, and the presence of: CAT-28 mention (tier 5 personality), Unity SDK preview, Knoema Bench leaderboard link, city-scale 1k benchmark mention, OpenAI TTS voice playback mention. Prints a table of which locales are missing which features.
2. Updated locale READMEs - every locale should include the five feature mentions above. Translations must be written in the target language; do NOT leave English strings in non-English files.
3. `.github/workflows/readme-parity.yml` - GitHub Action that runs `scripts/check_readme_parity.py` on every push touching any `README*.md` and fails CI on drift.
4. `tests/test_readme_parity.py` - local test that runs the same check offline.

### 4.3 Acceptance Criteria

- `python scripts/check_readme_parity.py` exits 0 against the current working tree.
- Every non-English README contains the five required feature mentions translated into the target language.
- GitHub Action is wired and passes on the commit that introduces it.

### 4.4 Git

Commit message: `feat(readme): enforce multilingual locale parity for recent features`
Paths: `scripts/check_readme_parity.py`, `.github/workflows/readme-parity.yml`, `tests/test_readme_parity.py`, `README.de.md`, `README.es.md`, `README.fr.md`, `README.ja.md`, `README.ko.md`, `README.zh-CN.md`, `README.zh-TW.md`.

---

## 5. Global Completion Report

After Slot D passes, append a consolidated summary to `planning/codex_session_report_2026-04-22.md`:

```markdown
## Sequential Slots Session 2 - Completion (YYYY-MM-DD)

### Slot A: CAT-28 viewer integration
- Commit: <sha>
- Acceptance proof: dropdown group counts (4/3/8), ethics-modal trigger verified

### Slot B: HF Space warmup and cache bust
- Commit: <sha>
- Acceptance proof: deploy succeeded end-to-end with the new flags; warm_space exit 0

### Slot C: Didimdol one-pager generator
- Commit: <sha>
- Acceptance proof: PDFs are 1 page each, deterministic rebuild matches SHA256

### Slot D: Multilingual README parity
- Commit: <sha>
- Acceptance proof: check_readme_parity.py exit 0 on all 7 locales

### Full gates across all slots
- pytest final: N passed, M skipped
- ruff: clean
- mypy: clean
- Forbidden-entity scan: 0 matches
```

Then create `planning/NIGHT_REPORT_knoema_sequential_2026-04-22.md` following the template used by the 2026-04-21 night report.

---

## 6. What This Handoff Does NOT Include

Intentionally deferred - require product/strategy decisions the user has not made yet:

- CAT-28 expansion beyond the initial 8 (14 remaining single + 6 composite). Reopen after 2026-04-29 Didimdol submission.
- Seizn, Milkypix, Notrivo, Fangden, Ovriel integration surfaces. Permanently excluded from this repository per entity separation policy.
- Qwen3.5 LoRA or any third-party fine-tuned weights. Permanently excluded.
- Archetype -> real-person mapping of any kind. Permanently excluded.
- Tier 3 or Tier 4 criminology archetypes. Still manual / user-only.
- Enterprise tier, usage billing, fine-tune dataset export, marketplace - all outside this week's scope.

---

## 7. Stop Conditions

Halt the sequential pipeline immediately if any of the following occur:

1. A slot's standard gate fails and the failure is not a transient network issue.
2. `git push origin main` is denied by the remote (even with the permanent credential fix). Document in `planning/codex_blockers.md` and stop.
3. HF Space fails to reach `RUNNING` within `scripts/warm_space.py`'s 10-minute window, twice in a row, on the same slot.
4. A forbidden-entity scan returns any match (see §0.2 full list).
5. `.env.local` is missing or `HF_TOKEN` / `OPENAI_API_KEY` are unset.
6. A slot attempts to hand-type a git SHA rather than read one via `git rev-parse HEAD`.
7. A slot attempts to modify credential config, gh auth state, or anything under `.git/`.
8. Any slot's effort estimate is exceeded by more than 2x.

On halt: write the reason, current slot, reproduction command, and last-good commit SHA to `planning/codex_blockers.md` and return to the user.
