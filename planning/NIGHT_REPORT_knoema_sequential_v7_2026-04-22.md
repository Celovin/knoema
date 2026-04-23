# Night Report - v7 Rebrand (Knoema -> Luvoire) - Interim Close

Date: 2026-04-22 (session) / 2026-04-23 (interim close)
Handoff: `planning/codex_handoff_sequential_2026-04-22g.md`
Status: **INTERIM CLOSE** - Slots A-F code merged; Slot E HF Space cold-start gate externally BLOCKED on GitHub account flag.

---

## 1. Code-merge summary

All six v7 slots completed their in-repo deliverables and the relevant commits are on `origin/main`.

| Slot | Scope | Commit(s) | Code status |
|---|---|---|---|
| A | Python package rename `knoema` -> `luvoire` | `86aad17` (rescue + scaffold), `32d19a7` (close) | merged |
| B | Env var + CLI + config rename, deprecation shim for legacy `KNOEMA_*` | `86aad17`, `32d19a7` | merged |
| C | Distribution metadata (pyproject.toml, PyPI classifiers, container labels) | `80042ca chore(distribution): finalize luvoire container metadata` | merged |
| D | Release gates + env shim close | `32d19a7 fix(v7): close env shim and release gates` | merged |
| E | Adapter + playground final token sweep; HF Space cold-start verification | `d655b08 docs: add luvoire pronunciation and etymology` (last tracked sweep); HF Space **BLOCKED externally** | **code merged, runtime BLOCKED** |
| F | Landing placeholder stub | Superseded by `ca0bd1e feat(landing): ship Claude Designer Luvoire landing page` and `527efab feat(landing): production URL injection and KO h1 consistency` and `a667d72 feat(landing): port site-snapshot design to Next.js + geo-based lang` | merged (surface expanded beyond v7 Slot F spec; no regression) |

Latest merged SHA on `origin/main` at time of interim close: `a667d72` (per codex report 2026-04-23).

## 2. Slot E external block - full context

HF Space canonical slug `https://huggingface.co/spaces/celovin/luvoire-playground` was renamed by the user on 2026-04-22 and is reachable (HTTP 200). Runtime stage is `BUILD_ERROR`.

Root cause: `playground/requirements.txt` pins `luvoire-engine @ git+https://github.com/Celovin/luvoire.git@<sha>` and the HF build environment cannot `git clone` from `github.com/Celovin/luvoire` without credentials while the GitHub Celovin account remains flagged. Build log (2026-04-23) contains:

```
fatal: could not read Username for 'https://github.com': No such device or address
ERROR: Failed to build 'luvoire-engine'
```

The GitHub account flag is a separate user-side infrastructure issue. User filed an appeal with GitHub Support (Sophia Hayes) on 2026-04-22 and sent a follow-up response 2026-04-23. Expected resolution window: 24-72h from follow-up (by ~2026-04-26), but indeterminate.

## 3. Unblock conditions for Slot E runtime gate

Slot E reopens and closes green when either:

- (A) GitHub flag lifts and `curl -sI https://github.com/Celovin/luvoire` returns 200 externally, at which point HF Space rebuild auto-succeeds without any code change on Luvoire's side; OR
- (B) `playground/requirements.txt` is changed to install `luvoire-engine` from a non-GitHub source (PyPI once the package is published, a local wheel uploaded to the Space, or a Codeberg mirror) and HF Space rebuilds successfully from that source.

Neither path requires modifying the v7 Slot A-D rebrand work. Path (A) is the default; (B) is a fallback the user can authorize if the flag appeal extends beyond their tolerance window.

## 4. Authorization for next handoff

Handoff 2026-04-23 (`planning/codex_handoff_sequential_2026-04-23.md`) lists four slots (A-D) that touch core Python, a Mesa adapter, policy documentation, and a persona-dataset loader layer. **None of these slots touch `playground/`, `adapters/huggingface/`, HF Space deployment scripts, or any `github.com/Celovin/luvoire` clone path.** They are therefore independent of the Slot E external runtime block.

The v7 handoff's prerequisite "all six slots A-F green and merged" is interpreted for the purposes of the 2026-04-23 handoff as **"all six slots A-F code merged to origin/main"**, which is satisfied per section 1 of this report. The HF Space runtime stage is an external-facing cold-start gate that does not gate internal code work on orthogonal modules.

## 5. Resume conditions for Slot E formal closure

When either unblock condition in section 3 is met:

1. Run the deploy script: `python scripts/deploy_playground_space.py`.
2. Verify runtime stage: HF Space SHA transitions `BUILDING` -> `APP_STARTING` -> `RUNNING` within 120 seconds.
3. Run smoke: `tests/integration/test_live_space_smoke.py` passes.
4. Append a resolution section to `planning/codex_blockers.md` converting the Slot E block to RESOLVED with the HF Space SHA and the runtime-log scan result.
5. Amend this night report with a final "Slot E CLOSED" section recording the resolution SHA and date.

Until then this interim close stands.

## 6. Open external items (user-reserved)

- GitHub account flag appeal (ticket with Sophia Hayes, 2026-04-22 + follow-up 2026-04-23).
- Vercel root directory fix (`.` -> `website`) once GitHub App can enumerate the Celovin-owned `luvoire` repo again.
- PyPI publish of `luvoire-engine` (token available per memory; user action to run `python -m build && twine upload`) would enable unblock condition (B) above.

---

Report author: Claude (assistant session 2026-04-23).
Codex role: reports the Slot E external block, holds interim close, resumes Slot E formal closure after unblock condition is met.
