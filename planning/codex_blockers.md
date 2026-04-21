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

## Policy Note - Codex Must Not Change Remote URL

- The `origin` remote URL is fixed to `https://Celovin@github.com/Celovin/knoema.git` as a user-side permanent fix for the recurring 403 issue.
- Codex MUST NOT run `git remote set-url`, `git remote add`, or otherwise rewrite the origin remote.
- Codex MUST NOT run `gh auth switch`. User-side GCM username hint already routes credentials correctly.
- If a future push is still denied, halt with `Slot N BLOCKED: git push denied despite embedded-username remote` and let the user diagnose; do not attempt credential workarounds.
