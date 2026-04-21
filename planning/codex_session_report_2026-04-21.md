# Codex Session Report - 2026-04-21

## Scope

작업 대상은 `Celovin/knoema` 저장소와 HF Space `celovin/knoema-playground`로 제한했다. Seizn 프로젝트와 `.codex/seizn/` 경로는 건드리지 않았다.

## Completed Batches

- Batch P, Cross-model A/B/C comparison: Playground에 GPT, Claude, Replay 병렬 비교 패널을 추가하고, tick/agent action overlap ratio와 모델 간 action distribution Pearson r를 표시한다.
- Batch MM, Presentation mode: `?mode=present`에서 Gradio chrome을 줄이고, 좌우 방향키 탭 이동, Space 실행, Esc 복귀를 지원한다.
- Batch U, Reproducibility certificate: `knoema.reproducibility` 모듈, `knoema-verify` CLI, Playground 인증서 ZIP export를 추가했다.
- Batch S, Fairness audit: `playground/analysis/fairness_audit.py`를 추가하고, trait-action heatmap과 top-10 bias summary를 표시하는 Bias audit 패널을 연결했다.
- Batch HH, Prereg template library: 연구 질문별 10개 사전등록 템플릿과 OSF form autofill picker를 Playground에 추가했다.
- Batch O, MCP server integration: `knoema_mcp` stdio JSON-RPC server, five MCP tools, `knoema-mcp` entry point, Claude Desktop/Code/Cursor setup docs를 추가했다.
- Batch V, NL scenario generation: `knoema.scenario_synthesis` validated YAML generator와 Playground 자연어 시나리오 생성 패널을 추가했다.
- Batch Q, CLI + Docker self-hosted stack: `knoema list-scenarios`, `knoema verify`, `knoema playground`, `python -m knoema`, Dockerfile, Compose, and self-hosted docs를 추가했다.
- Batch AA, Fine-tuning dataset exporter: OpenAI/Anthropic/DPO JSONL exporters, Python API docs, and Playground fine-tuning download controls를 추가했다.
- Batch NN, Discord/Slack bot: `knoema_bots` core, Discord embed formatter, Slack Block Kit formatter, optional bot entry points, setup docs를 추가했다.
- Batch GG, University course kit: 12-week syllabus, weekly assignments, labs, rubric, reveal.js slide template, and MkDocs education nav를 추가했다.

- Batch R, Community scenario gallery: `knoema.community` seed gallery, GitHub manifest loader, Playground gallery picker, contribution templates, and schema tests were added.

## Commits

- GitHub code commit: `ce1ed44` (`feat(playground): add model compare and reproducibility tools`)
- GitHub code commit: `3184fe0` (`feat(analysis): add trait-action fairness audit`)
- GitHub code commit: `fd29ed7` (`feat(research): add preregistration template library`)
- GitHub code commit: `53f0577` (`feat(mcp): expose Knoema scenario tools`)
- GitHub code commit: `4fcbc75` (`feat(playground): synthesize scenarios from natural language`)
- GitHub code commit: `5577471` (`feat(cli,deploy): add self-hosted distribution`)
- GitHub code commit: `3ed33ca` (`feat(export): add fine-tuning dataset exporter`)
- GitHub code commit: `1a2e92e` (`feat(bots): add Discord and Slack scenario runners`)
- GitHub code commit: `de4b6ad` (`feat(education): add university course kit`)
- GitHub code commit: `e863698` (`feat(community): add GitHub-backed scenario gallery`)
- HF Space deploy commit: `4548af62a05ee130bf32f097d4abe2dd8e9420a4`
- HF Space deploy commit: `9c6f1b972bdc5ce48575ce0752afbd07d3e3a786`
- HF Space deploy commit: `05eb8106432bae501ca21be8187921b67538bf52`

## Local Verification

- Target tests: `11 passed, 5 warnings`
  - `tests/test_playground_cross_model.py`
  - `tests/test_playground_presentation_mode.py`
  - `tests/test_reproducibility_certificate.py`
  - `tests/test_reproducibility_verify.py`
  - `tests/test_fairness_audit.py`
  - `tests/test_playground_fairness_panel.py`
- Full pytest gate: `545 passed, 2 skipped, 5 warnings`
- Batch HH full pytest gate: `548 passed, 2 skipped, 5 warnings`
- Batch O full pytest gate: `553 passed, 2 skipped, 5 warnings`
- Batch V full pytest gate: `558 passed, 2 skipped, 5 warnings`
- Batch Q full pytest gate: `566 passed, 2 skipped, 5 warnings`
- Batch AA full pytest gate: `572 passed, 2 skipped, 5 warnings`
- Batch NN full pytest gate: `577 passed, 2 skipped, 5 warnings`
- Batch GG full pytest gate: `581 passed, 2 skipped, 5 warnings`
- Batch R full pytest gate: `587 passed, 2 skipped, 5 warnings`
- Ruff full gate: `All checks passed!`
- Batch Q Ruff gate: `All checks passed!`
- Batch AA Ruff gate: `All checks passed!`
- Batch NN Ruff gate: `All checks passed!`
- Batch GG Ruff gate: `All checks passed!`
- Batch R Ruff gate: `All checks passed!`
- Mypy gate: `Success: no issues found in 83 source files`
- Batch Q Mypy gate: `Success: no issues found in 84 source files`
- Batch AA Mypy gate: `Success: no issues found in 86 source files`
- Batch NN Mypy gate: `Success: no issues found in 90 source files`
- Batch GG Mypy gate: `Success: no issues found in 90 source files`
- Batch R Mypy gate: `Success: no issues found in 92 source files`
- Gradio compatibility: `Gradio compatibility OK`
- Batch R Gradio compatibility: `Gradio compatibility OK`
- Encoding guard and Plotly enum safety tests passed earlier in the session.

## Live Verification

- Deploy command: `scripts/deploy_playground_space.py` completed with `status: ok`.
- HF Space stage: `RUNNING`
- Batch HH HF Space sha/stage: `4548af62a05ee130bf32f097d4abe2dd8e9420a4` / `RUNNING`
- Batch O HF Space sha/stage: `4548af62a05ee130bf32f097d4abe2dd8e9420a4` / `RUNNING`
- Batch V HF Space sha/stage: `9c6f1b972bdc5ce48575ce0752afbd07d3e3a786` / `RUNNING`
- Batch Q HF Space sha/stage: `9c6f1b972bdc5ce48575ce0752afbd07d3e3a786` / `RUNNING`
- Batch AA HF Space sha/stage: `b8be050dbf871940ae2302f4aa29581c09088b18` / `RUNNING`
- Batch NN HF Space sha/stage: `b8be050dbf871940ae2302f4aa29581c09088b18` / `RUNNING`
- Batch GG HF Space sha/stage: `b8be050dbf871940ae2302f4aa29581c09088b18` / `RUNNING`
- Batch R HF Space sha/stage: `05eb8106432bae501ca21be8187921b67538bf52` / `RUNNING`
- RUNNING check time: `2026-04-21 08:53:24 KST`
- Space URL HTTP status: `200`
- Live smoke with `KNOEMA_EXPECT_CROSS_MODEL=1` and `KNOEMA_EXPECT_FAIRNESS_AUDIT=1`: `1 passed, 3 warnings`
- Batch HH live smoke with `KNOEMA_EXPECT_PREREG_TEMPLATE=1`: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-042011.png`
- Batch O live smoke: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-043217.png`
- Batch V live smoke with `KNOEMA_EXPECT_SCENARIO_SYNTHESIS=1`: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-045635.png`
- Batch Q live smoke: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-050649.png`
- Batch AA live smoke with `KNOEMA_EXPECT_FINETUNING_EXPORT=1`: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-052903.png`
- Batch NN live smoke: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-053920.png`
- Batch GG live smoke: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-054749.png`
- Batch R live smoke with `KNOEMA_EXPECT_COMMUNITY_GALLERY=1`: `1 passed, 3 warnings`; screenshot `C:\Users\admin\Projects\knoema\artifacts\live-graph-20260421-061840.png`
- Recent Space run logs: `error_matches=0` for `Traceback|Error|gradio.exceptions|TypeError|ValueError`

## Operational Notes

- Initial HF runtime failed because the Space build reused an older cached `knoema-engine @ ...@main` install that did not include `knoema.reproducibility`.
- A production `factory_reboot` was requested through `HfApi.restart_space(..., factory_reboot=True)`, after which the Space rebuilt and reached `RUNNING`.
- Batch R initial HF runtime failed with stale cached install missing `knoema.community`; a production `factory_reboot` rebuilt the Space and restored `RUNNING`.
- Batch S는 `playground/` 내부 로컬 분석 모듈로 구현해서 두 번째 Space 배포에서는 추가 factory reboot가 필요하지 않았다.
- Existing unrelated dirty files were left unstaged and untouched.

## Next Session

1. All requested autonomous batches through R are complete.
2. Keep the seven-gate batch loop for any v3 follow-up batches.

## Sequential Slot 3 - 1K Agent City-Scale Proof of Concept

### Scope

- Added deterministic city-scale shard runner, 1K benchmark, replay viewer, offline replay artifacts, pedagogical archetype profiles, validators, and scaling docs.
- Slot 3 did not touch `playground/`; HF Space deployment gates 8-11 were skipped per Section 0.4.

### Commit

- GitHub code commit: `ea0783bcc892ba827b73cc7df61db9586f04880a` (`feat(scaling): add city-scale 1k benchmark, demo replay viewer, and archetype library`)
- HF Space SHA / stage: N/A, no playground deployment.

### Standard Gate Results

- Full pytest gate: `593 passed, 2 skipped, 5 warnings in 108.39s`
- Ruff gate: `All checks passed!`
- Mypy gate: `Success: no issues found in 94 source files`
- Encoding guard: `3 passed`
- Gradio compatibility: `Gradio compatibility OK: C:\Users\admin\Projects\knoema\playground\app.py`
- Plotly enum safety: `4 passed`
- Git push: `11d3758..ea0783b main -> main`

### Slot Acceptance Proof

- `python benchmarks\city_scale_1k.py --output tmp\city_scale` completed locally; median wall-clock `13.084720s`, peak RSS `144.426 MB`, throughput `7642.50 agent-ticks/sec`, deterministic hash `0630fa745fa93a18ec0c37b2718e6cc77c6df632059812ab94d6da4b5af24697`.
- `python -m pytest tests\test_scaling_city_scale.py` passed; single and multiprocessing backends produced identical small-N hashes.
- `knoema[scale]` installed cleanly in a fresh `tmp\.venv-scale` virtualenv after Python 3.13-compatible Ray marker gating.
- `python demo\replay\generate_replay.py --verify-existing` passed; committed replay msgpack files are byte-identical to regenerated output.
- `demo\replay\replay_1000agents_gangnam_7pm.msgpack` size: `4,419,939` bytes.
- Chromium `file://` viewer verification passed through the local `Load files` fallback: 100-agent and 1000-agent msgpacks loaded offline; profile dropdown and ethics modal flow worked.
- Research phase completed before profile YAML generation. All 7 research docs are within the 1500-3000 word bound, `_source_log.json` records consulted sources, and `python scripts\validate_citations.py demo\replay\profiles\_research` passed.
- `python scripts\validate_profile.py "demo/replay/profiles/**/*.yaml"` passed; all profile sources cross-reference their research appendices.
- Forbidden scans for `Litheon|Seizn|Ovriel|Fangden|Notrivo` and Tier 3/4 forbidden-name substrings returned 0 matches in Slot 3 surfaces.
