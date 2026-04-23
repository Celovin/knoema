# Codex Blockers

## Slot 4 RESOLVED - GitHub Push Denied

- Status: RESOLVED on 2026-04-22.
- Resolution: User-side GitHub authentication was switched to an account with push access, and `f6de9418ff668021815ad237d1a664ce70bbe5ec` was pushed to `origin/main`.
- Original reason: `git push origin main` was denied by GitHub because the active credential resolved to `litheonhq`, which does not have permission to push to `Celovin/knoema`.
- Current slot: Slot 4 - Unity SDK Scaffold
- Reproduction command: `git push origin main`
- Last-good SHA: `1b1b9d4501aef4ab58dd8de09d697c39f79e55c1`
- Local blocked commit: `f6de9418ff668021815ad237d1a664ce70bbe5ec`
- Remote error: `remote: Permission to Celovin/knoema.git denied to litheonhq. fatal: unable to access 'https://github.com/Celovin/knoema.git/': The requested URL returned error: 403`

## Slot 5 RESOLVED - GitHub Push Denied Before Slot 5 Implementation

- Status: RESOLVED on 2026-04-22.
- Resolution: User-side `gh auth switch -u Celovin` + `git push origin main` pushed commit `e39cea0a7cd93515cb08a92c404f8f835dba759e` to `origin/main`.
- Permanent fix (2026-04-22): Remote URL rewritten to embed Celovin as the credential username hint so future pushes remain routed to the Celovin credential regardless of which `gh` account is active:
  - `git remote set-url origin https://Celovin@github.com/Celovin/knoema.git`
  - `git remote set-url --push origin https://Celovin@github.com/Celovin/knoema.git`
  - Git Credential Manager resolves the `Celovin@github.com` hint against the Windows Credential Manager entry for the Celovin PAT independently of `gh auth switch` state.
- Original reason: `git push origin main` was denied again by GitHub because the active credential resolved to `litheonhq`, which does not have permission to push to `Celovin/knoema`.
- Latest recheck: 2026-04-22, the same `git push origin main` command was retried and returned the same 403 denial.
- Current slot: Slot 5 - OpenAI TTS Multimodal Agent
- Reproduction command: `git push origin main`
- Last-good SHA: `f6de9418ff668021815ad237d1a664ce70bbe5ec`
- Local blocked commit: `e39cea0a7cd93515cb08a92c404f8f835dba759e`
- Remote error: `remote: Permission to Celovin/knoema.git denied to litheonhq. fatal: unable to access 'https://github.com/Celovin/knoema.git/': The requested URL returned error: 403`

## Policy Note - Codex Must Not Change Credential Config

User-side permanent fix (2026-04-22) is now complete. `git push origin main` routes to the Celovin credential independently of `gh auth switch` state. Codex may push without any credential-related workaround.

Fix details (do not modify):

- `origin` remote URL: `https://Celovin@github.com/Celovin/knoema.git` (fetch and push).
- Repo-local `.git/config` overrides the github.com credential helper to Git Credential Manager:
  - `credential.https://github.com.helper=` (resets inherited gh helper)
  - `credential.https://github.com.helper=manager`
- Git Credential Manager holds a Celovin-keyed entry for `https://github.com` and resolves the `Celovin@github.com` URL hint to that entry.

Hard rules for Codex:

- Codex MUST NOT run `git remote set-url`, `git remote add`, or otherwise rewrite the origin remote.
- Codex MUST NOT run `gh auth switch`, `gh auth login`, or `gh auth logout`.
- Codex MUST NOT modify `credential.*` keys in any git config scope.
- Codex MUST NOT add or modify files under `.git/`.
- If a future push is still denied, halt with `Slot N BLOCKED: git push denied despite permanent credential fix` and let the user diagnose.

## Slot 5 RESOLVED - HF Space Failed To Reach RUNNING Twice

- Status: RESOLVED on 2026-04-22.
- Root cause: The `knoema-engine` pin in `playground/requirements.txt` contained a fabricated SHA (`d7b844f0d3257c645f20a48c862cfb7a7223e462`) that did not exist in the repository. The real Slot 5 implementation commit is `d7b844f05a61267dff134c843848b8a338a3bf75`. `git cat-file -e` on the fabricated SHA exits non-zero, which is why HF Space's pip install emitted `BUILD_ERROR`.
- Resolution: User-side edited `playground/requirements.txt` to pin `knoema-engine` to the real HEAD SHA `d5ca5eb2de3d913735157b9975621d12816f0392` (d5ca5eb only modifies `playground/requirements.txt` so its `src/knoema/` tree is identical to d7b844f and contains `src/knoema/multimodal/`). Committed as `2648c30ff...` (`fix(playground): correct knoema-engine pin sha for multimodal tts`) and pushed.
- Redeploy result: HF Space SHA `9b06ad89ae12`, stage transitioned `BUILDING` -> `APP_STARTING` -> `RUNNING` within 120 seconds. HTTP/1.1 200 returned by `curl -sI https://huggingface.co/spaces/celovin/knoema-playground`. `tests/integration/test_live_space_smoke.py` passed (1 passed). Runtime-log scan of last 50 lines matched 0 forbidden patterns (`Traceback|Error|gradio.exceptions|TypeError|ValueError`).
- Original reason: Slot 5 Playground deployment did not reach `RUNNING` within the allowed retry window twice in a row.
  - First deployment after `d7b844f05a61267dff134c843848b8a338a3bf75`: HF Space SHA `7dff8093f7209a13595cf4c6cdd25b12072083c5`, stage `RUNTIME_ERROR`; run log showed `ModuleNotFoundError: No module named 'knoema.multimodal'`.
  - Second deployment after dependency pin fix `d5ca5eb2de3d913735157b9975621d12816f0392`: HF Space SHA `ef9043ae93aa8b843ffb2664333dcae446819b60`, stage `BUILD_ERROR`. The pushed `playground/requirements.txt` pinned `knoema-engine` to an incorrect full SHA prefix (`d7b844f0d325...`), while the actual Slot 5 implementation commit is `d7b844f05a61267dff134c843848b8a338a3bf75`.
- Current slot: Slot 5 - OpenAI TTS Multimodal Agent
- Reproduction command: `python scripts/deploy_playground_space.py` then `python - <<'PY'\nfrom huggingface_hub import HfApi\nprint(HfApi().space_info('celovin/knoema-playground').runtime.stage)\nPY`
- Last-good SHA before resolution: `b712a4e13586aa053d19e6383684afaba0b4fba9`
- Local pushed commits before halt:
  - `d7b844f05a61267dff134c843848b8a338a3bf75` - Slot 5 implementation.
  - `d5ca5eb2de3d913735157b9975621d12816f0392` - HF Space dependency pin attempt (typo SHA).
  - `2648c30...` - corrected SHA pin (resolution commit).

## Policy Note - Never Hand-Type Git SHAs

The Slot 5 build failure was caused by a hand-typed SHA that did not correspond to any real commit. When Codex (or any agent) needs to pin a pip dependency to a specific commit, it MUST obtain the SHA from `git rev-parse HEAD` or `git log --format=%H -1` rather than transcribing from memory. Any SHA written into a file must be verified with `git cat-file -e <sha>` before the file is committed.

## Slot B RESOLVED - Standard Gate Failed

- Status: RESOLVED on 2026-04-22.
- Resolution: User-side added the Slot B documentation file `docs/playground-deploy.md` to `mkdocs.yml` nav under the `Reference` section (line inserted between `CI and Release` and `Privacy`). Verified with `python -m pytest tests/test_phase29_mkdocs.py` -> `4 passed`.
- Resolution commit: includes `mkdocs.yml` and this blockers update only; Codex's in-flight Slot B files (`scripts/warm_space.py`, `tests/test_warm_space.py`, `docs/playground-deploy.md`, `scripts/deploy_playground_space.py`, `CHANGELOG.md`) remain untracked / modified in the working tree for Codex to finish committing as the Slot B commit.
- Root cause: `docs/playground-deploy.md` is a new Slot B deliverable per handoff §2.2 item 4; the repository's mkdocs nav coverage test (`tests/test_phase29_mkdocs.py::test_phase29_mkdocs_nav_covers_all_public_markdown_pages`) treats every public markdown file under `docs/` as required in the nav.
- Codex resumption instruction: re-run §0.5 from gate 1 (pytest) with the existing Slot B working-tree changes intact. Gate 1 now passes because `mkdocs.yml` is already updated and committed. On gate 7, add `mkdocs.yml` to the Slot B commit paths alongside the other Slot B deliverables, so the commit message `feat(playground-deploy): add warmup, cache-bust, and factory-reboot flags` still accurately covers the nav registration.
- Original reason: `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py` failed because `docs/playground-deploy.md` was not listed in `mkdocs.yml` nav (`tests/test_phase29_mkdocs.py::test_phase29_mkdocs_nav_covers_all_public_markdown_pages`).
- Current slot: Slot B - HF Space Cold-Start Warmup and Cache Bust
- Reproduction command: `python -m pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py`
- Last-good SHA before resolution: `6f1e8efde3963ef4e33a86a52fc563da40b56cfb`

## Slot E BLOCKED - Hugging Face Space Runtime Not Healthy

- Status: BLOCKED, updated on 2026-04-23.
- Current slot: Slot E - Adapter and Playground final sweep.
- Current reason: the canonical Luvoire Space slug now resolves, but the Space runtime is not healthy. `HfApi().space_info(...)` reports `BUILD_ERROR` for both `celovin/luvoire-playground` and `celovin/knoema-playground` at SHA `d2bb0cfc3e9a1863e08f5733d4038d7d5b5639f0`.
- Original 2026-04-22 reason: the canonical Luvoire Space slug was not reachable. `https://huggingface.co/spaces/celovin/luvoire-playground` returned HTTP 401, while the legacy `https://huggingface.co/spaces/celovin/knoema-playground` returned HTTP 200. Per the v7 handoff, an unchanged HF Space slug was a blocker and Codex had to halt.
- Last pushed SHA before halt: `d655b08c89052549982bc50614753ae9c879ba38`.
- Verification already completed before halt:
  - Tracked adapter/playground sweep found no `knoema` / `Knoema` / `KNOEMA` tokens under `adapters/`, `unity-sdk/`, `sdk/`, `playground/`, `website/`, or allowed `site-snapshot` paths.
  - Filename sweep over the same tracked paths found no old-name tracked filenames.
- Reproduction commands:
  - `python - <<'PY'\nfrom huggingface_hub import HfApi\napi = HfApi()\nfor repo_id in ("celovin/luvoire-playground", "celovin/knoema-playground"):\n    info = api.space_info(repo_id=repo_id)\n    print(repo_id, info.sha, info.runtime.stage)\nPY`
  - `Invoke-WebRequest -Uri 'https://huggingface.co/spaces/celovin/luvoire-playground' -UseBasicParsing -TimeoutSec 20`
  - `Invoke-WebRequest -Uri 'https://huggingface.co/spaces/celovin/knoema-playground' -UseBasicParsing -TimeoutSec 20`
- Required user action: fix or factory-rebuild the Hugging Face Space so `celovin/luvoire-playground` reaches `RUNNING`, then resume Slot E cold-start verification.
