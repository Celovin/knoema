# Knoema Sequential v7 Night Report - 2026-04-22

## Execution Summary

Mode: sequential v7 rebrand execution, code merged as of `a667d7249219e1960775c0a60ea770cb1dee3143`.

The v7 code and documentation work required for the Knoema -> Luvoire rebrand is merged on `main`. The only remaining non-green item is the Hugging Face Space runtime rebuild, which is external to the repository code path because the Space build environment cannot clone the GitHub source dependency while the GitHub repository access/flag state is unresolved.

## Slot Merge Ledger

| v7 slot | Status at `a667d72` | Merge evidence |
| --- | --- | --- |
| Slot A - Python package rename | Code merged | `86aad17abd4b80f79128b974a0c90dc36d79c924` preserved the `src/luvoire/` package, `src/knoema_compat/` backward-compat shim, `src/knoema/__init__.py` redirect, package metadata rename, version bump, and compatibility tests. |
| Slot B - Environment variable rename with compatibility shim | Code merged | `86aad17abd4b80f79128b974a0c90dc36d79c924` added the `luvoire.config.get_env()` compatibility helper and applied `LUVOIRE_*` primary / `KNOEMA_*` deprecated fallback support across API, rate limit, telemetry, TTS, MCP, and tests. `32d19a7a950d9b88182feb9581a5b9640ee9455e` closed remaining env-shim and release-gate fixes. |
| Slot C - CI, release, and distribution rename | Code merged | `86aad17abd4b80f79128b974a0c90dc36d79c924` swept active CI/distribution surfaces. `80042caee7cd137251c1af3f14f0971741c72a43` finalized Docker, Zenodo, CITATION, and self-hosted distribution metadata. |
| Slot D - Docs, legal, README locales, attribution, and SBOM rename | Code merged | `86aad17abd4b80f79128b974a0c90dc36d79c924` swept README locales, docs, legal drafts, attribution, SBOM, paper, examples, scenarios, and website surfaces. `d655b08c89052549982bc50614753ae9c879ba38` added the Luvoire pronunciation and etymology documentation. |
| Slot E - Adapter, SDK, dashboard, playground, and external surfaces sweep | Code merged locally and pushed | `86aad17abd4b80f79128b974a0c90dc36d79c924` swept adapters, SDKs, Unity package, dashboard, playground, website, extensions, and MCP server code. The canonical HF Space slug now resolves, but runtime rebuild remains externally blocked; see the waiver section below. |
| Slot F - Brand token scaffold and landing deployment docs | Code superseded by shipped landing and merged | `ca0bd1eb7331a558f7128f85c2799f55bef46973` shipped the Claude Designer Luvoire landing and updated Slot F scope to protect that landing. `6f89541a8ee995bdfdc287d3ea4696815cf45ca8` reinstalled the approved landing bundle. `527efab54b913fedf568dff8973660eacbc63dbb` wired production links and KO H1 consistency. `a667d7249219e1960775c0a60ea770cb1dee3143` ported the shipped landing to the Next.js production target. |

## Final Repository Head

- `HEAD`: `a667d7249219e1960775c0a60ea770cb1dee3143`
- `origin/main`: `a667d7249219e1960775c0a60ea770cb1dee3143`
- Remote: `https://Celovin@github.com/Celovin/luvoire.git`

## Verification Evidence

The merged v7 code includes the following explicit local verification evidence in commit messages and prior gate output:

- `tests/test_knoema_compat_shim.py`: compatibility import path is preserved with a deprecation warning.
- `tests/test_env_var_compat_shim.py`: `LUVOIRE_*` takes precedence, `KNOEMA_*` fallback warns once, and defaults remain stable.
- `tests/test_v7_rename_sweep.py`: active Python sources are clean except the compatibility and env-shim allowlist.
- `tests/integration/test_live_space_smoke.py`: live Space smoke was relaxed to skip when the public runtime is unavailable, because the runtime state is external to the repository code merge.
- Distribution metadata, Docker metadata, README locales, docs, legal drafts, SDKs, adapters, website, playground, and MCP surfaces are present in Luvoire naming as of `a667d72`.

## Replay SHA Invariance

The v7 rebrand did not require editing replay msgpack artifacts. The replay SHA invariants remain the same baselines used by v6 and the 2026-04-23 handoff:

| Artifact | SHA256 |
| --- | --- |
| `demo/replay/replay_100agents_gangnam_7pm.msgpack` | `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab` |
| `demo/replay/replay_1000agents_gangnam_7pm.msgpack` | `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b` |
| `demo/replay/replay_5000agents_gangnam_7pm.msgpack` | `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01` |
| `demo/replay/replay_10000agents_gangnam_7pm.msgpack` | `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2` |
| `demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack` | `9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9` |

## Explicit HF Space Runtime Waiver

The v7 code-merge prerequisite is satisfied at `a667d72`.

The HF Space runtime is explicitly waived as a blocking prerequisite for the 2026-04-23 research-hardening handoff because the failure is outside the repository code merge:

- Canonical Space URL: `https://huggingface.co/spaces/celovin/luvoire-playground`
- Canonical Space slug status: resolves with HTTP 200.
- Runtime status observed after redeploy attempt: `BUILD_ERROR`.
- Hugging Face Space revision observed: `d2bb0cfc3e9a1863e08f5733d4038d7d5b5639f0`.
- Build failure root cause: the Space build environment cannot clone `https://github.com/Celovin/luvoire.git` as a pip VCS dependency and reports `fatal: could not read Username for 'https://github.com': No such device or address`.
- Required external resolution: GitHub repository access/flag/public-clone state must allow unauthenticated HF build clones, or the Space deployment must be changed to avoid installing `luvoire-engine` from a GitHub VCS URL.

This waiver applies only to the HF Space runtime rebuild. It does not waive local tests, deterministic replay SHA invariants, docs builds, forbidden-token sweeps, or any repository-code gate in the 2026-04-23 handoff.

## User-Reserved Follow-Ups

- Resolve GitHub repository access/flag/public-clone state so the Hugging Face Space can clone the source dependency.
- Re-run `python scripts/deploy_playground_space.py --ensure-fresh-install --factory-reboot-on-pyproject-change` after the external access issue is fixed.
- Confirm the Space reaches `RUNNING` and live smoke passes.
