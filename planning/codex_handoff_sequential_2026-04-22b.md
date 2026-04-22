# Codex Sequential Handoff - 5K Agent Replay Extension

Author: Celovin (Choi Jihwan)
Date: 2026-04-22 (evening handoff, single slot)
Working directory: `C:\Users\admin\Projects\knoema`
Deadline anchors: 황태정 대면 미팅 2026-04-23 (목) / 2026-04-27 (월); Didimdol grant 2026-04-29 18:00 KST (D-7).
Previous handoff: `planning/codex_handoff_sequential_2026-04-22.md` (all 4 slots closed, session report at `planning/NIGHT_REPORT_knoema_sequential_2026-04-22.md`).

---

## 0. Execution Contract

### 0.1 Single Slot, No Parallel

This handoff contains one slot. Do it. Do not invent additional slots. Do not touch unrelated files.

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

Same as `planning/codex_handoff_sequential_2026-04-22.md` §0.4. Summary:

- Codex MUST NOT run `git remote set-url`, `git remote add`, `gh auth switch`, `gh auth login`, `gh auth logout`.
- Codex MUST NOT modify `credential.*` keys in any git config scope.
- Codex MUST NOT add or modify files under `.git/`.
- Codex MUST NOT hand-type git SHAs. Any SHA written into a file must come from `git rev-parse HEAD` or `git log --format=%H -1` and be verified with `git cat-file -e <sha>`.
- If `git push origin main` is denied, halt with `Slot A BLOCKED: git push denied despite permanent credential fix`.

### 0.5 Standard Verification Gate

After finishing implementation:

1. `pytest --no-cov --ignore=tests/test_phase60_mobile_sdks.py` - all green.
2. `ruff check .` - clean.
3. `mypy src` - clean.
4. `python -m pytest tests/test_playground_encoding_guard.py` - pass.
5. `python scripts/check_gradio_compat.py` - pass.
6. `python -m pytest tests/test_plotly_enum_safety.py` - pass.
7. `git add <slot paths>` + `git commit -m "feat(scaling): add 5k agent replay on 40x40 grid"` + `git push origin main`.

Slot A does NOT touch `playground/` (the replay viewer is file:// local, not on HF Space). Skip HF Space gates (8-11).

### 0.6 Actions Reserved for the User

- 5K replay demo presentation to external stakeholders.
- Any discussion of entity separation or cross-repo sharing.
- Scheduling / messaging any faculty member.

---

## 1. Slot A - 5K Agent Replay on 40x40 Grid

Effort estimate: 4-6 hours (user expects under 1 hour based on prior Codex throughput; estimate is generous).
Rationale: Adds a 5K-agent deterministic replay scenario as a demo-ready upgrade path between the existing 1K scenario and a future 10K scenario. 5K on a 40x40 grid maintains per-cell agent density close to the 1K/20x20 configuration so visual legibility and drill-down behavior are preserved. Purely additive - does not replace or modify the existing 1K or 100-agent scenarios.

### 1.1 Inputs

- `src/knoema/scaling/city_scale.py` - existing `CityScaleRunner`.
- `benchmarks/city_scale_1k.py` - 1K benchmark reference.
- `benchmarks/city_scale_1k_report.md` - report format reference.
- `demo/replay/generate_replay.py` - existing replay generator.
- `demo/replay/replay_1000agents_gangnam_7pm.msgpack` - 1K replay for format parity.
- `demo/replay/viewer.html` - existing local-file viewer with archetype injection.
- `demo/replay/scenario_config.yaml` - existing scenario definition (20x20 grid).

### 1.2 Deliverables

1. `benchmarks/city_scale_5k.py` - benchmark script:
   - 5000 agents, 100 ticks, 3 repetitions, deterministic seeding.
   - Uses the existing `DeterministicLLMClient`.
   - 40x40 grid variant.
   - Emits `benchmarks/city_scale_5k_report.md` with wall-clock median, throughput, peak RSS, repetition-hash match, and the same `Framework Comparison` table as `city_scale_1k_report.md` (Knoema measured, Concordia/Mesa `not-measured`).

2. `demo/replay/scenario_config_40x40.yaml` - new scenario variant:
   - 40x40 grid with the same alley / main-road / commercial edge typology as the 20x20 grid, scaled proportionally.
   - Role distribution identical to the 20x20 scenario (92% general / 3% motivated-offender / 5% guardian).
   - Cite the same published RAT base-rate source in the yaml comment.
   - Do NOT modify `scenario_config.yaml` (20x20 stays authoritative for 100 and 1K).

3. `demo/replay/replay_5000agents_gangnam_7pm.msgpack` - committed replay artifact:
   - 5000 agents, 30 simulated minutes, 40x40 grid.
   - Format identical to existing replays (metadata / agents / frames / memory_snapshots / events).
   - Size target: ≤25 MB.
   - Regenerable via `python demo/replay/generate_replay.py --scenario 5k` producing byte-identical output.

4. `demo/replay/generate_replay.py` updates:
   - Add `--scenario {100,1k,5k}` CLI argument (default preserves current behavior).
   - 5k branch reads `scenario_config_40x40.yaml` and emits `replay_5000agents_gangnam_7pm.msgpack`.
   - `--verify-existing` mode extended to check the 5k artifact.

5. `demo/replay/viewer.html` updates:
   - Scenario switcher dropdown: `100 agents (20x20)` / `1000 agents (20x20)` / `5000 agents (40x40)`.
   - Grid renderer auto-reshapes to 40x40 when the 5k scenario is selected.
   - Hot-spot heatmap toggle continues to work at 40x40 grid density.
   - Archetype injection dropdown behavior is unchanged (Tier 1 / Tier 2 / Tier 5 groups stay as shipped).
   - Scenario load indicator displayed while msgpack deserializes (5K may take 2-4 seconds on demo hardware).

6. `tests/test_replay_5k_scenario.py` - new test file:
   - Determinism: 3 regenerations produce byte-identical msgpack output (SHA256 compare).
   - Size bound: committed 5k msgpack ≤25,000,000 bytes.
   - Format parity: 5k msgpack has the same top-level keys as the 1k msgpack.
   - No forbidden-entity strings in `scenario_config_40x40.yaml`.

7. `demo/replay/CHANGELOG.md` - append a dated entry describing the 5K scenario addition.

8. `docs/scaling.md` - append a "5K scenario" subsection documenting: the 40x40 grid rationale, regeneration command, file size, and the constraint that this is demo-only (no HF Space footprint).

### 1.3 Acceptance Criteria

- `python benchmarks/city_scale_5k.py --output tmp/city_scale_5k` completes within 3 minutes on the local machine using the deterministic client.
- Determinism test passes: identical JSONL output hash across 3 repeated runs with the same seed.
- Committed `demo/replay/replay_5000agents_gangnam_7pm.msgpack` ≤25 MB.
- Opening `demo/replay/viewer.html` via `file://` and switching to the 5K scenario successfully loads the replay within 5 seconds on the local laptop.
- Playing the 5K replay at 20x speed completes within 90 seconds wall-clock.
- `python demo/replay/generate_replay.py --scenario 5k --verify-existing` exits 0 (byte-identical regeneration).
- Forbidden-entity scan on the diff: 0 matches for the forbidden string list in §0.2.
- Existing 1K and 100-agent replays remain byte-identical (regression check via SHA256).

### 1.4 Git

Commit message: `feat(scaling): add 5k agent replay on 40x40 grid`
Paths: `benchmarks/city_scale_5k.py`, `benchmarks/city_scale_5k_report.md`, `demo/replay/scenario_config_40x40.yaml`, `demo/replay/replay_5000agents_gangnam_7pm.msgpack`, `demo/replay/generate_replay.py`, `demo/replay/viewer.html`, `tests/test_replay_5k_scenario.py`, `demo/replay/CHANGELOG.md`, `docs/scaling.md`.

---

## 2. Completion Report

After Slot A passes, append a section to `planning/codex_session_report_2026-04-22.md`:

```markdown
## Sequential Slot A - 5K Replay Extension (YYYY-MM-DD)
- Commit: <sha>
- Acceptance proof: determinism hash, 5K msgpack size, viewer load time, 20x replay wall-clock
- Gate results: pytest N passed, ruff clean, mypy clean, forbidden-entity 0 matches
```

Then create `planning/NIGHT_REPORT_knoema_5k_2026-04-22.md` mirroring the 2026-04-22 night report layout but scoped to this single slot.

---

## 3. What This Handoff Does NOT Include

- 10K or larger scenarios. Reserved for a future handoff post-Didimdol.
- Modification of the existing 1K or 100-agent replays (must stay byte-identical).
- HF Space upload of any kind (5K replay is local demo only).
- Archetype profile changes (no new CAT-28 entries in this slot).
- Live LLM calls during replay generation (determinism requires `DeterministicLLMClient`).
- README multilingual parity updates (addressed by prior Slot D; 5K surface is single-paragraph append in `docs/scaling.md` only, not in README).

---

## 4. Stop Conditions

Halt immediately if:

1. Standard gate fails non-transient.
2. `git push origin main` denied despite permanent credential fix.
3. 5K msgpack exceeds 25 MB (indicates non-linear blowup; investigate and halt).
4. Determinism hash differs across repeated regeneration (indicates non-deterministic path in the runner or generator).
5. Viewer fails to load the 5K replay on Chrome via `file://` (Playwright test timeout).
6. Forbidden-entity scan returns any match.
7. `.env.local` missing or critical env vars unset.
8. Existing 1K or 100-agent replay SHA256 changes (must not happen).
9. Effort exceeds 8 hours (hard cap; the user estimated <1 hour).

On halt: write reason, reproduction command, last-good SHA to `planning/codex_blockers.md` and return to the user.
