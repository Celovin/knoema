# Codex Sequential Handoff - 10K Agent Replay Extension

Author: Celovin (Choi Jihwan)
Date: 2026-04-22 (third handoff, single slot)
Working directory: `C:\Users\admin\Projects\knoema`
Deadline anchors: 황태정 대면 미팅 2026-04-23 (목) / 2026-04-27 (월); Didimdol grant 2026-04-29 18:00 KST (D-7).
Previous handoff: `planning/codex_handoff_sequential_2026-04-22b.md` (5K slot closed at commit `6f3ac76`, session report appended at `c4127ce`).

Context: 5K replay measured 4.78 MB (per-agent bytes decreased vs 1K due to change-only memory writes and delta-encoded frames). Linear extrapolation predicts 10K at 6-10 MB, well under the 25 MB cap. 60x60 grid preserves per-cell density close to the 1K/20x20 and 5K/40x40 configurations.

---

## 0. Execution Contract

### 0.1 Single Slot, No Parallel

One slot. Do not invent additional work. Do not regress existing scenarios.

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
```

### 0.4 Hard Credential and Config Rules

Same as prior handoffs. Summary:

- Codex MUST NOT run `git remote set-url`, `gh auth switch`, `gh auth login`, `gh auth logout`.
- Codex MUST NOT modify `credential.*` keys in any git config scope.
- Codex MUST NOT add or modify files under `.git/`.
- Codex MUST NOT hand-type git SHAs. Use `git rev-parse HEAD` and verify with `git cat-file -e <sha>`.
- If `git push origin main` is denied, halt with `Slot A BLOCKED: git push denied despite permanent credential fix`.

### 0.5 Standard Verification Gate

After implementation:

1. `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py` - all green.
2. `ruff check .` - clean.
3. `mypy src` - clean.
4. `python -m pytest tests/test_playground_encoding_guard.py` - pass.
5. `python scripts/check_gradio_compat.py` - pass.
6. `python -m pytest tests/test_plotly_enum_safety.py` - pass.
7. `git add <slot paths>` + `git commit -m "feat(scaling): add 10k agent replay on 60x60 grid"` + `git push origin main`.

Slot A does NOT touch `playground/`. Skip HF Space gates (8-11).

### 0.6 Actions Reserved for the User

- Demo presentation to external stakeholders.
- Any discussion of entity separation or cross-repo sharing.

---

## 1. Slot A - 10K Agent Replay on 60x60 Grid

Effort estimate: 1-2 hours (5K slot closed in 20 minutes; 10K expected similar).
Rationale: Adds a 10K-agent deterministic replay scenario on a 60x60 grid. Per-cell agent density stays close to the 1K/20x20 (2.5) and 5K/40x40 (3.1) configurations so visual legibility and drill-down behavior remain comparable. Purely additive - must not modify existing 100 / 1K / 5K scenarios.

### 1.1 Inputs

- `src/knoema/scaling/city_scale.py` - existing `CityScaleRunner`.
- `benchmarks/city_scale_5k.py` - 5K benchmark for structure parity.
- `benchmarks/city_scale_5k_report.md` - 5K report format reference.
- `demo/replay/generate_replay.py` - existing replay generator with `--scenario` flag.
- `demo/replay/scenario_config_40x40.yaml` - 5K grid variant reference.
- `demo/replay/replay_5000agents_gangnam_7pm.msgpack` - 5K replay for format parity.
- `demo/replay/viewer.html` - existing scenario switcher.

### 1.2 Deliverables

1. `benchmarks/city_scale_10k.py` - benchmark script:
   - 10000 agents, 100 ticks, 3 repetitions, deterministic seeding.
   - Uses the existing `DeterministicLLMClient`.
   - 60x60 grid variant.
   - Emits `benchmarks/city_scale_10k_report.md` with wall-clock median, throughput, peak RSS, repetition-hash match, and the same Framework Comparison table (Knoema measured, Concordia/Mesa `not-measured`).

2. `demo/replay/scenario_config_60x60.yaml` - new scenario variant:
   - 60x60 grid with the same alley / main-road / commercial edge typology as the 20x20 and 40x40 grids, scaled proportionally.
   - Role distribution identical to prior scenarios (92% general / 3% motivated-offender / 5% guardian).
   - Cite the same published RAT base-rate source in the yaml comment.
   - Do NOT modify `scenario_config.yaml` (20x20) or `scenario_config_40x40.yaml` (5K).

3. `demo/replay/replay_10000agents_gangnam_7pm.msgpack` - committed replay artifact:
   - 10000 agents, 30 simulated minutes, 60x60 grid.
   - Format identical to existing replays.
   - Size target: ≤25 MB (extrapolation predicts 6-10 MB).
   - Regenerable via `python demo/replay/generate_replay.py --scenario 10k` producing byte-identical output.

4. `demo/replay/generate_replay.py` updates:
   - Extend `--scenario` choices to include `10k`.
   - 10k branch reads `scenario_config_60x60.yaml` and emits `replay_10000agents_gangnam_7pm.msgpack`.
   - `--verify-existing` mode extended to check the 10k artifact.

5. `demo/replay/viewer.html` updates:
   - Scenario switcher dropdown now: `100 agents (20x20)` / `1000 agents (20x20)` / `5000 agents (40x40)` / `10000 agents (60x60)`.
   - Grid renderer auto-reshapes to 60x60 when the 10k scenario is selected.
   - Hot-spot heatmap toggle must continue to work at 60x60 grid density.
   - Scenario load indicator visible while msgpack deserializes (target ≤5 seconds for 10k).
   - Archetype injection dropdown behavior is unchanged.

6. `tests/test_replay_10k_scenario.py` - new test file:
   - Determinism: 3 regenerations produce byte-identical msgpack output (SHA256 compare).
   - Size bound: committed 10k msgpack ≤25,000,000 bytes.
   - Format parity: 10k msgpack has the same top-level keys as the 5k msgpack.
   - No forbidden-entity strings in `scenario_config_60x60.yaml`.

7. `demo/replay/CHANGELOG.md` - append a dated entry describing the 10K scenario addition.

8. `docs/scaling.md` - append a "10K scenario" subsection documenting: the 60x60 grid rationale, regeneration command, measured file size, and the constraint that this is demo-only (no HF Space footprint).

### 1.3 Acceptance Criteria

- `python benchmarks/city_scale_10k.py --output tmp/city_scale_10k` completes within 6 minutes on the local machine using the deterministic client.
- Determinism test passes: identical JSONL output hash across 3 repeated runs with the same seed.
- Committed `demo/replay/replay_10000agents_gangnam_7pm.msgpack` ≤25 MB.
- Opening `demo/replay/viewer.html` via `file://` and switching to the 10K scenario successfully loads the replay within 5 seconds on the local laptop.
- Playing the 10K replay at 20x speed completes within 120 seconds wall-clock.
- `python demo/replay/generate_replay.py --scenario 10k --verify-existing` exits 0 (byte-identical regeneration).
- Forbidden-entity scan on the diff: 0 matches.
- Existing 100 / 1K / 5K replays remain byte-identical (regression check via SHA256 against these committed hashes):
  - `replay_100agents_gangnam_7pm.msgpack`: `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab`
  - `replay_1000agents_gangnam_7pm.msgpack`: `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b`
  - `replay_5000agents_gangnam_7pm.msgpack`: `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01`

### 1.4 Git

Commit message: `feat(scaling): add 10k agent replay on 60x60 grid`
Paths: `benchmarks/city_scale_10k.py`, `benchmarks/city_scale_10k_report.md`, `demo/replay/scenario_config_60x60.yaml`, `demo/replay/replay_10000agents_gangnam_7pm.msgpack`, `demo/replay/generate_replay.py`, `demo/replay/viewer.html`, `tests/test_replay_10k_scenario.py`, `demo/replay/CHANGELOG.md`, `docs/scaling.md`.

---

## 2. Completion Report

After Slot A passes, append a section to `planning/codex_session_report_2026-04-22.md`:

```markdown
## Sequential Slot A - 10K Replay Extension (YYYY-MM-DD)
- Commit: <sha>
- Acceptance proof: determinism hash, 10K msgpack size, viewer load time, 20x replay wall-clock
- Gate results: pytest N passed, ruff clean, mypy clean, forbidden-entity 0 matches
```

Then create `planning/NIGHT_REPORT_knoema_10k_2026-04-22.md` mirroring the 5K night report layout but scoped to this single slot.

---

## 3. What This Handoff Does NOT Include

- 50K or larger scenarios.
- Modification of existing 100 / 1K / 5K replays (must stay byte-identical).
- HF Space upload of any kind.
- Archetype profile changes.
- Live LLM calls during replay generation.
- README multilingual parity updates (addressed by prior Slot D; 10K surface is a single-paragraph append in `docs/scaling.md` only).

---

## 4. Stop Conditions

Halt immediately if:

1. Standard gate fails non-transient.
2. `git push origin main` denied despite permanent credential fix.
3. 10K msgpack exceeds 25 MB (indicates non-linear blowup; investigate and halt).
4. Determinism hash differs across repeated regeneration.
5. Viewer fails to load the 10K replay on Chrome via `file://` within 5 seconds.
6. Forbidden-entity scan returns any match.
7. `.env.local` missing or critical env vars unset.
8. Existing 100 / 1K / 5K replay SHA256 changes (must not happen).
9. Effort exceeds 4 hours (hard cap).

On halt: write reason, reproduction command, last-good SHA to `planning/codex_blockers.md` and return to the user.
