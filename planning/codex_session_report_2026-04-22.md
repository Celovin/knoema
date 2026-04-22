
## Slot A - CAT-28 Viewer Integration

- Scope: grouped replay viewer archetype dropdown into tier 1, tier 2 historical, and CAT-28 tier 5 personality sections; added file-mode self-test, Playwright coverage, and replay changelog.
- GitHub commit SHA: 6f1e8efde3963ef4e33a86a52fc563da40b56cfb
- HF Space SHA + stage: N/A (no playground changes).
- Full-gate results: pytest 604 passed, 2 skipped; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; push origin/main succeeded.
- Acceptance proof: file-mode viewer grouping verified at 4 / 3 / 8; tier 5 selection opens the personality-specific ethics notice and enables the Inject modal button after acknowledgement.

## Slot B - HF Space Cold-Start Warmup and Cache Bust

- Scope: added Space warmup polling, verified fresh-install dependency pinning, factory reboot detection, deploy docs, and deploy-wrapper unit coverage.
- GitHub commit SHA: 94afa189c46df16d7d846a673b537f5525d73678
- HF Space SHA + stage: 9085eae6a62af65e27163f70d94fbdb276c690a4 / RUNNING
- Full-gate results: pytest 610 passed, 2 skipped; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; deploy with --ensure-fresh-install --factory-reboot-on-pyproject-change ok; warm_space exit 0; live smoke 1 passed; runtime log last-50 scan 0 matches.
- Acceptance proof: deploy rewrote playground/requirements.txt to the verified HEAD SHA, factory rebooted the Space, warmed to RUNNING, and returned HTTP 200.

## Slot C - Didimdol One-Pager Generation

- Scope: added deterministic bilingual Didimdol one-pager generator, Korean/English templates, committed PDF outputs, tests, and rebuild documentation.
- GitHub commit SHA: 0effae4b76d5474bf4a9d69dbc433b5eb90edfdb
- HF Space SHA + stage: N/A (no playground changes).
- Full-gate results: pytest 613 passed, 2 skipped; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; push origin/main succeeded.
- Acceptance proof: both PDFs are 1 page, size-bounded, source-cited, forbidden-scan clean, and deterministic with fixed SOURCE_DATE_EPOCH; SHA256 ko=9eacc976674b404cfafebba3c5ca0c2ee4863a4aba25a69d27c9a29b6ec0a17e en=097abbdb970a12bbcd61c29879cd7fc5fdb604867a59b448c5d15e86049a0f01.

## Slot D - Multilingual README Locale Parity

- Scope: added locale parity checker, GitHub Actions enforcement, unit coverage, and recent-feature parity updates across the 7 localized README files.
- GitHub commit SHA: 113492ace0dcdf4fcf21f82e694449429a8b7d9c
- HF Space SHA + stage: N/A (no playground changes).
- Full-gate results: pytest 614 passed, 2 skipped; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; push origin/main succeeded.
- Acceptance proof: `scripts/check_readme_parity.py` passed for all 7 locale files, preserving required anchors and validating heading/bullet parity against the English README.

## Sequential Slots Session 2 - Completion (2026-04-22)

- Slot A commit: 6f1e8efde3963ef4e33a86a52fc563da40b56cfb. Acceptance proof: replay viewer file-mode grouping verified at 4 / 3 / 8, with the CAT-28 tier 5 ethics notice gating modal injection.
- Slot B commit: 94afa189c46df16d7d846a673b537f5525d73678. HF Space SHA + stage: 9085eae6a62af65e27163f70d94fbdb276c690a4 / RUNNING. Acceptance proof: deploy with `--ensure-fresh-install --factory-reboot-on-pyproject-change` succeeded, requirements pin was rewritten to the verified HEAD, factory reboot ran, warmup exited 0, live HTTP returned 200, and live smoke passed.
- Slot C commit: 0effae4b76d5474bf4a9d69dbc433b5eb90edfdb. Follow-up hard-rule fix commit: 07018b202be47eb9f04fdfce6292a403c0bebbaf. Acceptance proof: Korean and English Didimdol PDFs are one page, deterministic, source-cited, and forbidden-scan clean; generator no longer stores tracked forbidden-token literals.
- Slot D commit: 113492ace0dcdf4fcf21f82e694449429a8b7d9c. Acceptance proof: README locale parity checker exits 0 locally and is enforced by `.github/workflows/readme-parity.yml`.
- Final gate after Slot D follow-up fix: pytest 614 passed, 2 skipped, 5 warnings in 126.39s; Ruff `All checks passed!`; Mypy `Success: no issues found in 98 source files`; encoding guard 3 passed; Gradio compatibility OK; Plotly enum safety 4 passed; slot-surface forbidden text scan 0 matches; PDF extracted-text forbidden scan 0 matches.

## Sequential Slot A - 5K Replay Extension (2026-04-22)

- Commit: 6f3ac76ae03337d9e1b3e99fdc9d35163692a24a
- Acceptance proof: benchmark deterministic JSONL SHA256 `78a71d9504d602e810043cf3eb6c2b5730865a89cf600b6ed77eb490893ba9e3`; benchmark output hash `923f55541e1f5e079c2c5e9af58693048d6079ae25a7c07b49dec037248deb26`; 5K msgpack size 4,779,728 bytes; viewer 5K load time 0.293s via file:// + Load files fallback; 20x replay final-tick wall-clock 1.761s; existing 100-agent and 1K msgpack SHA256 values matched `demo/replay/SHA256SUMS.json`.
- Gate results: pytest 619 passed, 2 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; forbidden-entity scan 0 matches; `python demo/replay/generate_replay.py --scenario 5k --verify-existing` passed; `git push origin main` succeeded.

## Sequential Slot A - 10K Replay Extension (2026-04-22)

- Commit: c262c8f912df04be6868740164f6c2c28bf6fc94
- Acceptance proof: benchmark deterministic JSONL SHA256 `0453db8f182206471a21543da4cfd531d6dda8dd9a09ab8429b6869b90e3d6cc`; benchmark output hash `a81bbde312257d250d13cf44e94a3573aabe826d92ef6e27200b66fdd76bf395`; 10K msgpack size 9,539,344 bytes; 10K msgpack SHA256 `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2`; viewer 10K load time 0.584s via file:// + Load files fallback; 20x replay final-tick wall-clock 3.012s; existing 100-agent, 1K, and 5K msgpack SHA256 values matched the handoff baselines.
- Gate results: pytest 624 passed, 2 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; forbidden-entity scan 0 matches; `python demo/replay/generate_replay.py --scenario 10k --verify-existing` passed; `git push origin main` succeeded.

## Sequential v4 Slot A - CAT-28 Full Expansion (2026-04-22)

- Commit: 571a984150a113e4a564ebfc34bd2eca0267cd42
- Scope: completed CAT-28 tier 5 with 22 single archetypes and 6 composite gestalt overlays; updated profile schema identifier rules, CAT-28 bibliography coverage text, manifest entries, replay viewer grouping, viewer self-test, Playwright grouping test, and changelogs.
- Acceptance proof: `python scripts/validate_profile.py "demo/replay/profiles/**/*.yaml"` exited 0; manifest count is 35 profile entries; file count is 35 YAML profiles total with 22 CAT-28 single and 6 CAT-28 composite files; replay viewer grouping verified at 4 / 3 / 22 / 6; `mkdocs build --strict` passed.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values matched the v4 forbidden-regression baselines exactly; staged diff forbidden-entity scan returned 0 matches.
- Gate results: pytest 624 passed, 2 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; `git push origin main` succeeded.

## Sequential v4 Slot B - Nemotron Persona Integration (2026-04-22)

- Commit: 6c2a2acb56e594b1a0514c86d9a4429e1b6764ae
- License gate: `nvidia/Nemotron-Personas-Korea` license `cc-by-4.0` is allowlisted; dataset revision pinned to `0381f03a403df78a7998000f8b11705635b654fd`.
- Scope: converted `knoema.persona` into a package, added a deterministic Nemotron persona loader plus 512-row Gangnam fixture, wired `--persona-source {stub,nemotron}` for 10K replay generation, committed the Nemotron 10K replay variant, added viewer persona-source selection, tests, license notice, persona seeding docs, README locale bullets, and mkdocs nav entry.
- Acceptance proof: `demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack` is 11,802,818 bytes with SHA256 `9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9`; three regeneration runs produced the same SHA; `--verify-existing` passed for both stub and Nemotron sources.
- Regression proof: existing 100 / 1K / 5K / 10K replay msgpack SHA256 values matched the v4 forbidden-regression baselines exactly; staged diff forbidden-entity scan returned 0 matches.
- Gate results: pytest 630 passed, 3 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; README parity pass; mkdocs strict pass; `git push origin main` succeeded.
