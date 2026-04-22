# Codex Sequential Handoff v7 - Rebrand: Knoema -> Luvoire

Author: Celovin (Choi Jihwan)
Date: 2026-04-22 (seventh handoff, six-slot sequential, project rename)
Working directory: `C:\Users\admin\Projects\knoema` (renaming to `luvoire` is a user-reserved action; stays at current path throughout v7)
Deadline anchors: Didimdol grant 2026-04-29 18:00 KST; commercial PoC readiness target 2026-05-31.

Prerequisite: v6 (`planning/codex_handoff_sequential_2026-04-22f.md`) MUST be closed before any slot of this handoff starts. No v6 slot depends on v7; all v7 slots assume the v5+v6 commercial stack is fully merged.

Scope of v7: rebrand the project from `Knoema` to `Luvoire`. This touches Python packages, environment variables, CI/CD, documentation, legal drafts, README locales, adapters, UI surfaces, and site-snapshot assets. The rebrand is cross-cutting by definition; playground exception from v5/v6 is lifted for this handoff only.

Context:
- Trademark conflict driver: existing `Knoema Corp` (data SaaS, Eldridge acquisition) occupies the name in an adjacent commercial category; rebrand cost is minimal only while traction is near zero.
- Target name selection: `Luvoire` (pronounced `/luː.vwɑːr/`, Korean `루부아르`). Constructed from the French `-oire` suffix family (`mémoire`, `histoire`, `répertoire`) that matches the engine's memory + replay + persona-library stack.
- Domain already owned: `luvoire.com`. No TM search cost required.
- Landing page for `luvoire.com` is being built separately by Claude Designer (see `planning/luvoire-landing-brief-v1.md`); v7 Slot F produces only the placeholder `site-snapshot/index.html` stub plus brand tokens.

Hard principle: v7 rewrites forward-looking active code and docs only. Historical artifacts (all of `planning/`, `CHANGELOG.md` entries that predate the v7 merge, every prior `codex_session_report_*.md` and `NIGHT_REPORT_*.md`) are preserved verbatim so the engineering record stays intact.

---

## 0. Execution Contract

### 0.1 Sequential Only

Slots run in order: A -> B -> C -> D -> E -> F. Each slot closes fully (gates green, merged) before the next starts. Parallel slot execution is forbidden.

### 0.2 Scope Guard

Inside `C:\Users\admin\Projects\knoema` only. Never touch:

- `C:\Users\admin\Projects\seizn*`
- `C:\Users\admin\Projects\knot`
- `C:\Users\admin\Projects\thelabforge`
- `C:\Users\admin\Projects\milkypix`
- `.codex/`, `.claude/`, Dendron vaults

Forbidden strings in any tracked file: `Litheon`, `Seizn`, `Ovriel`, `Fangden`, `Notrivo`, `Milkypix`, `Yami`, `Qwen3.5-35B-A3B`.

Playground exception lift: v5 and v6 declared `playground/` off-limits. v7 lifts that exception for rename purposes only. Slot A, B, C, D may modify `playground/app.py`, `playground/requirements.txt`, `playground/README.md`, and `playground/static/` if and only if the change is a direct rename of `knoema` / `Knoema` / `KNOEMA` tokens, package imports, or environment variable references. No functional behavior in `playground/` may change. Every playground edit must be accompanied by an HF Space cold-start verification at slot close.

### 0.3 Environment Bootstrap

```bash
cd /c/Users/admin/Projects/knoema
export $(grep -v '^#' .env.local | xargs)
.venv/Scripts/python.exe -m pip install -e .[dev]
```

Required env vars (old and new must both be set during v7 transition):

- Old prefix (still required): `HF_TOKEN`, `OPENAI_API_KEY`
- New prefix introduced by Slot B: `LUVOIRE_RATE_LIMIT_TOKENS_PER_SECOND`, `LUVOIRE_RATE_LIMIT_BURST`, `LUVOIRE_METRICS_ENABLED`, `LUVOIRE_OTEL_EXPORTER`.
- Legacy `KNOEMA_*` names continue to work through one release cycle via Slot B's compatibility shim (logs a deprecation warning on first use per process).

### 0.4 Hard Credential and Config Rules

Same as prior handoffs:

- Codex MUST NOT run `git remote set-url`, `gh auth switch`, `gh auth login`, `gh auth logout`.
- Codex MUST NOT modify `credential.*` keys in any git config scope.
- Codex MUST NOT add or modify files under `.git/`.
- Codex MUST NOT hand-type git SHAs. Use `git rev-parse HEAD` and verify with `git cat-file -e <sha>`.
- Codex MUST NOT embed any raw API key, PAT, or secret in any committed file. Tests must use environment variables with graceful skip.
- If `git push origin main` is denied, halt with `Slot X BLOCKED: git push denied despite permanent credential fix`.

### 0.5 Standard Verification Gate (runs at the end of each slot)

1. `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py` - all green.
2. `ruff check .` - clean.
3. `mypy src` - clean.
4. `python -m pytest tests/test_playground_encoding_guard.py` - pass.
5. `python scripts/check_gradio_compat.py` - pass.
6. `python -m pytest tests/test_plotly_enum_safety.py` - pass.
7. `python -m mkdocs build --strict` - pass (slots that touch `docs/`).
8. Slot A, B, C, D, E MUST include a pre-commit sweep: `git grep -E 'knoema|Knoema|KNOEMA'` with an explicit allowlist (see §0.7).
9. `git add <slot paths>` + `git commit -m "<slot commit message>"` + `git push origin main`.

Slots that touch `playground/`: also run the HF Space cold-start verification per v6 Slot B's existing deploy wrapper.

### 0.6 Forbidden Regression

The following msgpack files MUST remain byte-identical through all of v7. The `knoema` string is NOT embedded in these artifacts (verified 2026-04-22), so rebrand preserves the SHAs automatically. Any change = halt.

- `replay_100agents_gangnam_7pm.msgpack`: `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab`
- `replay_1000agents_gangnam_7pm.msgpack`: `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b`
- `replay_5000agents_gangnam_7pm.msgpack`: `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01`
- `replay_10000agents_gangnam_7pm.msgpack`: `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2`
- `replay_10000agents_nemotron_gangnam_7pm.msgpack`: `9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9`

### 0.7 Historical Preservation (do NOT rewrite)

These paths are engineering history. Any token match against `knoema` inside these paths is ALLOWED and MUST NOT be rewritten:

- All of `planning/` (handoff docs, blockers, session reports, night reports, addenda, grant narrative drafts, print packs, submission packs, LaTeX drafts under `planning/academic_submissions/`).
- `CHANGELOG.md` entries that predate the v7 merge (v7 APPENDS a new entry; prior entries are verbatim).
- `.github/workflows/*.yml` git-log messages are not in scope (workflows themselves are rewritten in Slot C; past workflow runs on GitHub Actions are not touched).
- Prior release tags (e.g. `v0.2.0`) reference the old name; tags are immutable and not retouched.
- `benchmarks/*_report.md` files dated before the v7 merge (they are run logs; a new entry is added for the Luvoire rename, prior entries stay).
- Any test fixture under `tests/fixtures/` that asserts historical payload content (if any).

The pre-commit sweep script from §0.5 step 8 MUST accept `planning/`, `CHANGELOG.md` (lines predating the v7 merge commit), and the above allowlist. The sweep fails the slot on any `knoema` token found outside the allowlist.

### 0.8 Actions Reserved for the User

- Actually renaming the GitHub repository (`Celovin/knoema` -> `Celovin/luvoire`). GitHub preserves redirects automatically, but the user must click Settings -> Rename.
- Reserving `luvoire-engine` on PyPI (the name is currently free; user decides when to squat).
- Pointing `luvoire.com` DNS to a hosting target (Vercel, Cloudflare Pages, or HF Space).
- Approving the Claude Designer landing page before it replaces the v7 Slot F placeholder.
- Any trademark filing (USPTO/KIPO) for Luvoire as a registered mark.

### 0.9 Slot Completion Report

After each slot, append a section to `planning/codex_session_report_2026-04-22.md`. After Slot F, create `planning/NIGHT_REPORT_knoema_sequential_v7_2026-04-22.md` (the filename keeps `knoema` because the file is a historical record; this is the allowed exception mirroring §0.7).

---

## 1. Slot A - Python Package Rename

Effort estimate: 4-6 hours.
Rationale: `src/knoema/` is the primary Python package; `src/knoema_mcp/` is the MCP server sibling. All downstream code depends on these identifiers. This slot renames the directories, rewrites every import in `src/` and `tests/`, updates `pyproject.toml`, and ensures the full test suite stays green.

### 1.1 Inputs

- `src/knoema/**`, `src/knoema_mcp/**`
- `tests/**/*.py`
- `pyproject.toml` (name, entry points, console_scripts)
- `scripts/**/*.py` (import references)

### 1.2 Deliverables

1. Directory renames (use `git mv` to preserve history):
   - `src/knoema/` -> `src/luvoire/`
   - `src/knoema_mcp/` -> `src/luvoire_mcp/`

2. Token rewrite across `src/**/*.py`, `tests/**/*.py`, `scripts/**/*.py`:
   - `import knoema` -> `import luvoire`
   - `from knoema.x` -> `from luvoire.x`
   - `from knoema_mcp` -> `from luvoire_mcp`
   - `"knoema"` string literals -> `"luvoire"` (context-sensitive; exclude strings in audit-log event names, CC-BY attribution, legacy env-var backward-compat path, and any historical SHA references in comments)

3. `pyproject.toml` edit:
   - `[project]` table: `name = "luvoire-engine"`
   - `[project.scripts]`: `luvoire = "luvoire.cli:main"` (rename from `knoema = "knoema.cli:main"`)
   - Any `knoema_mcp` script entries: `luvoire-mcp`
   - Keywords list: add `"luvoire"`, keep academic keywords unchanged.
   - `description` field: update to "Luvoire: deterministic multi-agent simulation engine with replay, memory stack, and persona library."
   - `[tool.hatch.build.targets.wheel]` package paths: `src/luvoire`, `src/luvoire_mcp`.

4. `src/luvoire/__init__.py`:
   - Rename `__version__` bump to `0.3.0` (signals breaking API change).
   - Add `__pronounces__ = "/luː.vwɑːr/"` and `__korean_name__ = "루부아르"` as documented module metadata.

5. `src/luvoire/__main__.py`: rename module references.

6. Compatibility shim `src/knoema_compat/__init__.py` (new, minimal):
   - Re-exports `luvoire` namespace under the old `knoema` name for one release cycle.
   - Emits a `DeprecationWarning` on first import per process.
   - Test coverage in `tests/test_knoema_compat_shim.py` confirming both `import knoema` and `from knoema.api import ...` still resolve to the renamed modules.

7. Tests:
   - All existing tests updated to new imports.
   - `tests/test_v7_rename_sweep.py` (new): asserts that no `knoema` token survives outside the allowlist (`src/knoema_compat/`, `planning/`, `CHANGELOG.md` pre-v7 lines, historical reports).

### 1.3 Completion Report

Commit message: `feat(rename)!: rename python package knoema -> luvoire (v0.3.0)`.

Note the `!` flag per Conventional Commits for the breaking change.

Acceptance evidence:
- Full `pytest` green with renamed imports.
- `python -c "import luvoire; print(luvoire.__version__)"` prints `0.3.0`.
- `python -c "import knoema"` prints a DeprecationWarning and still works.
- `git grep -E '\bknoema\b' src/` returns only the `src/knoema_compat/` shim.

---

## 2. Slot B - Environment Variables and CLI

Effort estimate: 2-3 hours.
Rationale: v5 and v6 introduced `KNOEMA_*` environment variables across rate-limit, observability, and billing surfaces. Rebrand shifts them to `LUVOIRE_*` with a one-cycle compatibility shim so existing deployment scripts do not break on upgrade.

### 2.1 Inputs

- `src/luvoire/config.py` (renamed from `src/knoema/config.py` in Slot A)
- `src/luvoire/api/rate_limit.py`, `src/luvoire/api/tier_rate_limit.py`
- `src/luvoire/observability/*.py`
- `src/luvoire/telemetry/client.py`
- `src/luvoire/cli.py`, `src/luvoire/customer_cli.py`
- `.env.local.example`

### 2.2 Deliverables

1. Env-var rename map (apply everywhere):
   - `KNOEMA_RATE_LIMIT_TOKENS_PER_SECOND` -> `LUVOIRE_RATE_LIMIT_TOKENS_PER_SECOND`
   - `KNOEMA_RATE_LIMIT_BURST` -> `LUVOIRE_RATE_LIMIT_BURST`
   - `KNOEMA_METRICS_ENABLED` -> `LUVOIRE_METRICS_ENABLED`
   - `KNOEMA_OTEL_EXPORTER` -> `LUVOIRE_OTEL_EXPORTER`
   - `KNOEMA_SKIP_PERF_TESTS` -> `LUVOIRE_SKIP_PERF_TESTS`
   - `KNOEMA_API_KEY` (playground) -> `LUVOIRE_API_KEY`
   - Any other `KNOEMA_*` surfaced by `git grep`.

2. Backward-compat shim in `src/luvoire/config.py`:
   - `get_env(new_name, old_name=None, default=None)` helper that:
     - First reads `new_name` from `os.environ`.
     - If missing and `old_name` is provided: reads `old_name`, emits a one-time `DeprecationWarning(f"{old_name} is deprecated; use {new_name}")`.
     - Returns `default` if both missing.
   - Every `LUVOIRE_*` read path uses this helper with the old name as fallback.

3. CLI rename:
   - Console script entry point `knoema customer` -> `luvoire customer`.
   - CLI help text: product name references updated.
   - No behavioral change; only name surface.

4. `.env.local.example` rewritten with both old and new names (commented old, active new, and a migration note).

5. Tests:
   - `tests/test_env_var_compat_shim.py` (new):
     - New var set -> returns new value, no warning.
     - Old var set, new var unset -> returns old value, emits DeprecationWarning.
     - Both set -> new wins, no warning.
     - Neither set -> returns default.
   - Existing `test_observability.py`, `test_api_commercial_gating.py`, and `test_bench_replay_perf.py` edited to parametrize on both env-var names and assert the shim path works.

### 2.3 Completion Report

Commit message: `feat(config): rename env vars knoema_* -> luvoire_* with compat shim`.

Acceptance evidence:
- With only `KNOEMA_METRICS_ENABLED=1` set, `/metrics` endpoint still serves metrics AND emits a single DeprecationWarning in logs.
- With only `LUVOIRE_METRICS_ENABLED=1` set, `/metrics` serves metrics with no warning.

---

## 3. Slot C - Build, CI/CD, Distribution Config

Effort estimate: 2-3 hours.
Rationale: GitHub Actions workflows, Docker builds, release-please config, CITATION, and Zenodo metadata all embed the old name. A customer cloning the repo post-rename should get a consistent build.

### 3.1 Inputs

- `.github/workflows/*.yml` (all 14 or so workflows)
- `Dockerfile`, `docker-compose.yml`, `deploy/docker/**`
- `.github/release-please-config.json`
- `CITATION.cff`, `.zenodo.json`
- `scripts/deploy_playground_space.py`, `scripts/build_leaderboard.py`, `scripts/verify_replication.py`, others surfaced by `git grep`.
- `bench/submissions/knoema-0.2.0.yaml` (file rename)

### 3.2 Deliverables

1. GitHub Actions workflow rewrite:
   - Job names, step names, cache keys with `knoema` -> `luvoire`.
   - Image registry references (`ghcr.io/celovin/knoema` -> `ghcr.io/celovin/luvoire`).
   - Keep workflow file paths stable (do NOT rename `.github/workflows/ci.yml` -> `.github/workflows/ci-luvoire.yml`) so Actions history stays linked.

2. Docker:
   - `Dockerfile` LABEL fields updated (`org.opencontainers.image.title`, `.source`, `.url`, `.description`).
   - `docker-compose.yml` service name `knoema-api` -> `luvoire-api`; network name unchanged.
   - `deploy/docker/Dockerfile.api` LABEL fields updated.

3. `.github/release-please-config.json`:
   - `packages["."].package-name`: `knoema-engine` -> `luvoire-engine`.
   - Release type stays `python`.
   - Next version anchor: `0.3.0`.

4. `CITATION.cff`:
   - `title: Knoema Engine` -> `title: Luvoire`.
   - `identifiers[].value` references updated if present.
   - Authors, orcid, keywords remain.

5. `.zenodo.json`:
   - `title` and `description` updated.
   - `keywords` list: add `luvoire`, keep academic keywords.

6. File rename: `bench/submissions/knoema-0.2.0.yaml` -> `bench/submissions/luvoire-0.3.0.yaml`. Content rewritten: system name `Luvoire`, version `0.3.0`. A stub `knoema-0.2.0.yaml` staying present would be historical; instead, rename the file (git mv preserves history) and add a row to `bench/README.md` noting the rename.

7. Scripts:
   - `scripts/deploy_playground_space.py`: Space repo slug reference (if the HF Space is named `celovin/knoema`, user must rename it manually; the script is updated to accept both old and new slugs via env var; document this in `docs/playground-deploy.md`).
   - `scripts/build_leaderboard.py`, `scripts/verify_replication.py`: brand string updates only.
   - `scripts/fetch_status.py` title field update (Slot F also touches this).

8. Tests:
   - `tests/test_phase29_mkdocs.py` (or equivalent nav check): confirm new nav entries.
   - `tests/test_workflow_brand_sweep.py` (new): asserts every `.github/workflows/*.yml` contains no `knoema` token outside `# noqa: rename` comments.

### 3.3 Completion Report

Commit message: `feat(ci): rename build/ci/distribution configs knoema -> luvoire`.

Acceptance evidence:
- Every workflow run triggered by the rename commit (CI, release-please, sbom-drift, attribution-drift, status-page) completes green.
- `docker compose up` on the renamed compose file starts with the new service name.

---

## 4. Slot D - Documentation, Legal, and README Locales

Effort estimate: 4-5 hours.
Rationale: `docs/`, `legal/`, the 7 README locale mirrors, and the grant / academic LaTeX drafts all embed the old name. Attribution and SBOM need regeneration after rename. MkDocs strict build must pass.

### 4.1 Inputs

- `docs/**/*.md`
- `legal/**/*.md`
- `README.md`, `README.ko.md`, `README.ja.md`, `README.zh.md`, `README.de.md`, `README.fr.md`, `README.es.md`
- `ATTRIBUTIONS.md` (regenerated via `scripts/build_attributions.py`)
- `sbom.cdx.json` (regenerated via `scripts/build_sbom.py`)
- `docs/examples/*.ipynb` (Jupyter notebooks)
- Any `.tex` under `docs/` (if present; LaTeX grant drafts under `planning/academic_submissions/` are historical per §0.7 and NOT rewritten)
- `mkdocs.yml` site_name and related metadata

### 4.2 Deliverables

1. Global token rewrite inside `docs/**/*.md`, `legal/**/*.md`, `README*.md`:
   - `Knoema Engine` -> `Luvoire`
   - `Knoema` -> `Luvoire` (in running prose)
   - `knoema-engine` -> `luvoire-engine` (in pip install examples)
   - `knoema` Python package references updated in code samples
   - Preserve any `knoema` string inside: inline code that refers to the historical shim (e.g., `import knoema  # deprecated`), pronunciation guide, and rename-notice blocks.

2. `docs/index.md` gets a new Pronunciation + Etymology block:

   ```markdown
   ## Pronunciation
   **Luvoire** — `/luː.vwaʁ/` (English: "Loo-VWAR"). Korean: 루부아르.

   ## Etymology
   Luvoire follows the French `-oire` suffix family (mémoire, histoire, répertoire),
   chosen to echo the three concepts at the engine's core: memory, history, and a
   replayable repertoire of agent behavior.
   ```

3. `mkdocs.yml`:
   - `site_name: Luvoire`.
   - `site_description: Luvoire - deterministic multi-agent simulation engine.`
   - `site_url`: placeholder for now (`https://luvoire.com/docs/` once DNS is live).

4. Legal drafts: every occurrence of `Knoema Engine` / `Knoema` in the 10 legal files under `legal/` gets rewritten to `Luvoire`. Korean privacy policy retains its Korean section labels (`개인정보처리방침` stays). Draft status banners (`STATUS: DRAFT - LEGAL REVIEW PENDING`) stay.

5. README locale parity: run `scripts/check_readme_parity.py` after edits; fix any bullet-count drift. The parity checker from v6 must pass.

6. Attribution + SBOM regeneration:
   - `python scripts/build_attributions.py --write` produces a new `ATTRIBUTIONS.md` with `Luvoire` in the header and its bibliography. Drift check expected to update once.
   - `python scripts/build_sbom.py --write` produces a new `sbom.cdx.json` with component name `luvoire-engine`. Drift check expected to update once.

7. Pricing, status, landing (site-snapshot):
   - `site-snapshot/pricing.html` H1: `Luvoire pricing`. Title: `Pricing | Luvoire`.
   - `site-snapshot/status.html` Title: `Status | Luvoire`.
   - `site-snapshot/index.html` is created in Slot F; Slot D does not touch it.

8. Notebooks (`docs/examples/*.ipynb`): rewrite any `import knoema` cells and text-cell references. Outputs that show the old name in printed logs should be cleared so re-running produces clean new-name output.

9. Tests:
   - `scripts/check_readme_parity.py` passes.
   - `python -m mkdocs build --strict` passes.
   - `tests/test_doc_brand_sweep.py` (new): asserts docs/, legal/, and README*.md have no `knoema` token outside the pronunciation/etymology shim note and the explicit `import knoema  # deprecated` examples.
   - Attribution and SBOM CI drift checks pass against the regenerated artifacts.

### 4.3 Completion Report

Commit message: `docs(rename): rewrite docs, legal, and readme locales for luvoire`.

Acceptance evidence:
- `python -m mkdocs build --strict` pass.
- All 7 locale parity checks green.
- `ATTRIBUTIONS.md` and `sbom.cdx.json` regenerated and committed; drift checks green.

---

## 5. Slot E - Adapters, UI Surfaces, and Non-Python Code

Effort estimate: 3-4 hours.
Rationale: `adapters/` (Unity C#, WASM JS, iOS Swift, Android Kotlin, native C++), `dashboard/` (React/tsx), and various auxiliary artifacts (SVG logos, `.asmdef` files, Godot `.gd` scripts) reference the old name. These surfaces must stay consistent for downstream consumers.

### 5.1 Inputs

- `adapters/**` (Unity, WASM, iOS, Android, cpp)
- `dashboard/**` (tsx, css, public)
- SVG assets under `assets/`, `docs/assets/`, `dashboard/public/`
- Godot `.gd` scripts under `adapters/godot/` (if present)
- `playground/**` (rename-only edits allowed this slot per §0.2 exception)

### 5.2 Deliverables

1. Unity adapter (`adapters/unity/**`):
   - `.asmdef` file `rootNamespace` and `name` fields: `Knoema.Runtime` -> `Luvoire.Runtime`.
   - C# namespace declarations: `namespace Knoema` -> `namespace Luvoire`.
   - Prefabs or serialized `.asset` files referencing old namespace strings are rewritten if tracked.

2. WASM adapter (`adapters/wasm/**`):
   - `package.json` `name` field: `@celovin/knoema-wasm` -> `@celovin/luvoire-wasm`.
   - TypeScript/JS import paths.
   - Test files (`*.test.mjs`) updated.

3. iOS (Swift) adapter:
   - Swift module name `Knoema` -> `Luvoire`.
   - `Package.swift` product and target names.

4. Android (Kotlin) adapter:
   - Kotlin package `com.celovin.knoema` -> `com.celovin.luvoire`.
   - `build.gradle.kts` module name.

5. Native C++ adapter:
   - Header `knoema.h` -> `luvoire.h` (git mv).
   - `#include` references in .cpp files.
   - Namespace `knoema::` -> `luvoire::`.

6. Dashboard (`dashboard/**`):
   - `package.json` `name`: `@celovin/luvoire-dashboard`.
   - Title `<title>` element and meta tags.
   - Logo SVG references.

7. Godot `.gd` scripts:
   - `class_name` declarations, `extends` references, and any string literals referencing the old name.

8. SVG assets:
   - Any `<text>` content in logo SVGs reading `Knoema` becomes `Luvoire`.
   - File names: `knoema-logo.svg` -> `luvoire-logo.svg` (git mv).
   - References to these files in docs / dashboard / assets are updated simultaneously to preserve strict mkdocs and dashboard build.

9. Playground rename-only edits:
   - `playground/app.py`: gradio tab titles, model metadata, `KNOEMA_*` env var references (via Slot B shim).
   - `playground/README.md`: brand references.
   - `playground/requirements.txt`: if any dependency uses the old package name, update. (None expected; double-check.)
   - Slot close gate: HF Space cold-start verification per v6 Slot B wrapper. Pre-existing `scripts/deploy_playground_space.py --ensure-fresh-install --factory-reboot-on-pyproject-change` runs and returns healthy.

10. Tests:
    - `tests/test_adapter_brand_sweep.py` (new): asserts no `knoema` token in `adapters/`, `dashboard/`, `assets/` outside explicit allowlist comments.
    - Unity tests, WASM tests, dashboard vitest/jest runners green where CI exercises them.
    - Playground encoding guard and Gradio compat pass post-rename.

### 5.3 Completion Report

Commit message: `feat(adapters): rename adapters, dashboard, and playground surfaces to luvoire`.

Acceptance evidence:
- Unity, WASM, iOS, Android, Cpp adapter tests green.
- Dashboard builds.
- Playground Space cold-starts clean at new Space-repo reference (if user has not yet renamed the Space slug, document the blocker in `planning/codex_blockers.md` and proceed with local-mode verification; full HF Space rename is user action).

---

## 6. Slot F - Brand Token Scaffold (Landing Already Shipped)

Effort estimate: 1-2 hours.
Rationale: The Claude Designer final landing landed ahead of v7 dispatch as `site-snapshot/{index.html, styles.css, app.js, hero.js}` (total ~69 KB, multi-file, Luvoire branded, Korean + English toggle, H1 = 'Replayable city-scale simulation.'). Slot F's originally-planned placeholder stub is therefore obsolete. Slot F now only ships the `brand/` token scaffold and the landing-deploy documentation; it MUST NOT overwrite the live landing files.

### 6.1 Inputs

- `brand/tokens.json` (new)
- `brand/README.md` (new)
- `brand/logo-placeholder.svg` (new)
- `docs/landing-deploy.md` (new)
- `site-snapshot/{index.html, styles.css, app.js, hero.js}` (already present; READ ONLY in Slot F)
- `site-snapshot/pricing.html`, `site-snapshot/status.html` (touched in Slot D for title/H1; Slot F may add footer cross-link to `index.html` if missing)

### 6.2 Deliverables

1. `site-snapshot/index.html` + siblings (already present):
   - Codex MUST NOT modify, overwrite, or delete these files. They were shipped via the Claude Designer handoff bundle before v7 dispatch.
   - Codex MUST verify the files exist at slot-close and include their byte sizes in the completion report.

2. `brand/tokens.json` (design tokens, deterministic JSON, sorted keys):
   ```json
   {
     "color": {
       "base_cream": "#F7F3EC",
       "text_primary": "#141414",
       "text_secondary": "#5C5148",
       "accent_bronze": "#A8753A",
       "accent_ink_navy": "#1E293B",
       "accent_sage": "#7A8F7B",
       "error_oxblood": "#7F1D1D",
       "code_bg_dark": "#1A1815"
     },
     "typography": {
       "display_serif": "Source Serif 4 Variable",
       "body_sans_kr": "Pretendard Variable",
       "body_sans_latin": "Inter Variable",
       "mono": "JetBrains Mono"
     },
     "pronunciation": {
       "ipa": "/luː.vwaʁ/",
       "korean": "루부아르",
       "english_approx": "Loo-VWAR"
     }
   }
   ```

3. `brand/README.md`:
   - How to use tokens: reference from landing HTML, from dashboard, from future marketing.
   - Entity-separation reminders: avoid terracotta (TheLabForge), mint/emerald (Seizn/Praxiqa).
   - Pronunciation guide.

4. `brand/logo-placeholder.svg`:
   - Simple wordmark placeholder using `Source Serif 4`-like generic serif fallback.
   - Two variants: light-on-cream and light-on-dark.
   - Marked with `<!-- placeholder; replace with Claude Designer final -->` comment.

5. `docs/landing-deploy.md` (new):
   - How the shipped landing (`site-snapshot/{index.html, styles.css, app.js, hero.js}`) is hosted at `luvoire.com` once DNS is wired.
   - Routing map: `/` -> index.html, `/pricing` -> pricing.html, `/status` -> status.html.
   - Replacement procedure if the landing needs to be reissued from a fresh Claude Designer bundle.
   - Rollback procedure via git revert on the landing commit.

6. `site-snapshot/pricing.html`, `site-snapshot/status.html`:
   - Footer gains a `Home -> index.html` link.
   - Total file size budget: `pricing.html` ≤ 10 KB (was 8,489 bytes), `status.html` ≤ 8 KB (v6 target).

7. Tests:

   - `tests/test_landing_shipped.py` (new):
     - Asserts `site-snapshot/{index.html, styles.css, app.js, hero.js}` all exist.
     - Records their byte sizes (no upper bound — landing is a real design, not a stub).
     - No emoji in `index.html` (regex scan).
     - No forbidden entity strings in any of the 4 files (regex scan for Litheon, Seizn, Ovriel, Fangden, Notrivo, Milkypix, Yami, Qwen3.5-35B-A3B).
     - Pronunciation string `/luː.vwɑːr/` present in `index.html`.
     - Post-Slot-D: `knoema` / `Knoema` token count in the 4 files is zero (allowlist has NO entries for `site-snapshot/`).
     - Internal link targets (`pricing.html`, `status.html`) resolve to existing siblings.
   - `tests/test_brand_tokens.py` (new):
     - `brand/tokens.json` parses and contains all expected keys.
     - Colors are valid hex.
     - Pronunciation matches `/luː.vwɑːr/` exactly (note: the actually-shipped landing uses `ɑ` not `a`; tokens MUST match the landing so the two sources do not drift).

### 6.3 Completion Report

Commit message: `feat(brand): ship brand token scaffold and landing-deploy docs (landing pre-shipped)`.

Acceptance evidence:
- `site-snapshot/{index.html, styles.css, app.js, hero.js}` exist, unmodified from pre-v7 state, with byte sizes recorded.
- `brand/tokens.json` parses and tests green; `ipa` field matches the landing's pronunciation glyph exactly.
- `docs/landing-deploy.md` rendered under mkdocs strict with the routing map.
- Pricing and status footer cross-links to landing work locally.

---

## 7. Global Completion Report (after Slot F)

Create `planning/NIGHT_REPORT_knoema_sequential_v7_2026-04-22.md` (filename retains `knoema` as a historical marker) with:

1. Execution summary table of all 6 slot commits (A through F).
2. Final verification gate output: pytest, ruff, mypy, encoding guard, gradio compat, plotly enum safety, mkdocs strict, workflow brand sweep, doc brand sweep, adapter brand sweep, landing placeholder, brand tokens.
3. Replay SHA invariance confirmation for all 5 artifacts listed in §0.6.
4. `git grep -E '\bknoema\b'` final tally with allowlist breakdown (expected locations: `src/knoema_compat/`, `planning/`, `CHANGELOG.md` pre-v7 lines, historical reports, the landing pronunciation-context example if any).
5. Secret-pattern and forbidden-entity scan results on the cumulative v7 diff: 0 / 0.
6. Attribution + SBOM regenerated content showing `Luvoire` component name.
7. `site-snapshot/{index.html, styles.css, app.js, hero.js}` final byte sizes (all untouched by v7 post-landing-ship) + `brand/tokens.json` IPA string + docs/landing-deploy.md presence.
8. Deprecation warning trace: one sample log line showing the old env var fallback emitting its warning correctly.
9. User-action checklist (GitHub repo rename, PyPI squat, DNS, landing replacement) with status.

---

## 8. What This Handoff Does NOT Include

- Renaming the GitHub repository (`Celovin/knoema` -> `Celovin/luvoire`). ALREADY COMPLETED before v7 dispatch; Slot F completion report MUST confirm the current `origin` URL points at `Celovin/luvoire`.
- Registering `luvoire-engine` on PyPI. User decides timing.
- Pointing `luvoire.com` DNS. User action.
- The Claude Designer final landing. ALREADY SHIPPED pre-dispatch at `site-snapshot/{index.html, styles.css, app.js, hero.js}`. Slot F MUST NOT modify these files.
- Renaming the HF Space slug. User action; Slot E script accepts both old and new slugs via env var.
- Trademark filings with USPTO or KIPO.
- Rewriting historical artifacts under `planning/`, old session reports, old night reports, pre-v7 CHANGELOG entries, prior release tags.
- Rewriting git log history. The commit history stays on the old name for pre-v7 commits; the new name applies from v7 onward.

---

## 9. Stop Conditions (halt and report, do not push through)

1. Any replay msgpack SHA from §0.6 changes.
2. `git push origin main` denied despite permanent credential fix.
3. Any file under `planning/` gets rewritten (historical preservation violated).
4. Any CHANGELOG line predating the v7 merge gets retroactively modified.
5. `git grep -E '\bknoema\b'` returns a match outside the §0.7 allowlist at slot close.
6. Any raw secret or PAT appears in a staged diff.
7. Any forbidden entity string from §0.2 appears in a staged diff.
8. `mkdocs build --strict` fails.
9. Python 3.12 import of `luvoire` fails for any reason after Slot A.
10. Compatibility shim `import knoema` raises ImportError instead of emitting DeprecationWarning.
11. Playground Space cold-start fails post-rename and the failure is not a known user-action blocker (HF Space slug rename).
12. Attribution or SBOM drift check fails after regeneration.
13. Any `site-snapshot/{index.html, styles.css, app.js, hero.js}` file is modified by a v7 slot (Slot D rewrites `Knoema` -> `Luvoire` tokens but the landing is already Luvoire-pure — no edits expected; Slot F is read-only for these files).
