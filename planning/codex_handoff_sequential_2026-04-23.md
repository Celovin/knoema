# Codex Sequential Handoff 2026-04-23 - Research-Informed Hardening v1

Author: Celovin (Choi Jihwan)
Date: 2026-04-23 (first post-v7 handoff; research-informed priorities)
Working directory: `C:\Users\admin\Projects\knoema`
Deadline anchors:
- Didimdol grant submission 2026-04-29 18:00 KST (Slot C ships in-window marketing claim support; Slot D's roadmap claim usable in proposal narrative)
- EU AI Act Art. 50 transparency enforceable 2026-08-02 (next-handoff Slot E prerequisite; not in this handoff)
- PIPA 10% global-revenue fine regime starts 2026-09-11 (next-handoff Slot F prerequisite; not in this handoff)

Prerequisite: v7 handoff (`planning/codex_handoff_sequential_2026-04-22g.md`) MUST be fully closed (all six slots A-F green and merged) before any slot of this handoff starts. v7's rebrand is load-bearing for every path in this document.

Scope of this handoff: four slots that encode the highest-priority research findings from the five-track 2026-04-23 strengthening research into concrete code. Slots target the "Top 4 next-2-weeks" items from the unified roadmap:

- Slot A: Response-cache layer in core (prerequisite architecture for every future LLM-touching integration including A-MEM and Concordia).
- Slot B: Mesa 3 adapter + ODD protocol markdown exporter (publication-pipeline lever for computational social science audience).
- Slot C: Civilian-only redline declaration across ToS, README, docs, and landing (positioning + regulatory hygiene).
- Slot D: Nemotron-Personas multi-country loader (7 countries) + Luvoire Persona Interface v1 (harmonized cross-country ontology; NeurIPS Datasets & Benchmarks 2026 submission axis; Didimdol global-R&D narrative lever).

Slots E-H (C2PA manifests, PIPA re-identification evaluator, A-MEM plugin, LongMemEval score run, HugAgent experiments, Nemotron-Personas-Germany custom build) are **out of scope for this handoff** and will ship in the next handoff after the Didimdol window closes 2026-04-29.

---

## 0. Execution Contract

### 0.1 Sequential Only

Slots run in order: A -> B -> C -> D. Each slot closes fully (gates green, merged, pushed) before the next starts. Parallel slot execution is forbidden (user feedback memory: `feedback_codex_sequential_execution.md`, 2026-04-21).

### 0.2 Scope Guard

Inside `C:\Users\admin\Projects\knoema` only. Never touch:

- `C:\Users\admin\Projects\seizn*`
- `C:\Users\admin\Projects\knot`
- `C:\Users\admin\Projects\thelabforge`
- `C:\Users\admin\Projects\milkypix`
- `.codex/`, `.claude/`, Dendron vaults

Forbidden strings in any tracked file: `Litheon`, `Seizn`, `Ovriel`, `Fangden`, `Notrivo`, `Milkypix`, `Yami`, `Qwen3.5-35B-A3B`.

Post-v7 baseline: `knoema` / `Knoema` / `KNOEMA` tokens are forbidden outside the v7 historical allowlist (`planning/`, pre-v7 `CHANGELOG.md` entries). Every new file this handoff introduces MUST use `luvoire` / `Luvoire` naming.

### 0.3 Environment Bootstrap

```bash
cd /c/Users/admin/Projects/knoema
export $(grep -v '^#' .env.local | xargs)
.venv/Scripts/python.exe -m pip install -e .[dev]
```

No new env vars introduced in this handoff.

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
8. `git grep -E '\bknoema\b|\bKnoema\b|\bKNOEMA\b'` against v7 historical allowlist. Any hit outside the allowlist fails the slot.
9. `git add <slot paths>` + `git commit -m "<slot commit message>"` + `git push origin main`.

### 0.6 Forbidden Regression (msgpack SHA invariants)

The following msgpack files MUST remain byte-identical through every slot of this handoff. Any change = halt.

- `replay_100agents_gangnam_7pm.msgpack`: `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab`
- `replay_1000agents_gangnam_7pm.msgpack`: `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b`
- `replay_5000agents_gangnam_7pm.msgpack`: `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01`
- `replay_10000agents_gangnam_7pm.msgpack`: `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2`
- `replay_10000agents_nemotron_gangnam_7pm.msgpack`: `9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9`

### 0.7 Historical Preservation

Everything under `planning/`, all prior `codex_session_report_*.md`, all prior `NIGHT_REPORT_*.md`, and pre-v7 `CHANGELOG.md` entries are engineering history. They MUST NOT be rewritten by this handoff. The pre-commit sweep (step 8 above) uses the same allowlist the v7 handoff established.

### 0.8 Actions Reserved for the User

- Approving the Civilian-Only policy wording before it ships publicly (Slot C deliverable 3.5 posts a review request to the session report).
- Any trademark filing, DNS, or GitHub settings action.
- Enabling the HF Space rebuild if `site-snapshot/` content changes trigger a Space redeploy.

### 0.9 Slot Completion Report

After each slot, append a section to `planning/codex_session_report_2026-04-23.md` (create on first write). After Slot C, create `planning/NIGHT_REPORT_luvoire_research_hardening_v1_2026-04-23.md`.

### 0.10 Research Provenance

The priorities in this handoff derive from five parallel research tracks completed 2026-04-23. A full synthesis lives in the session transcript; for Codex's purposes the load-bearing findings are:

- "SHA256 replay = recorded side-effects + deterministic core" (Tracks A and E convergence) - motivates Slot A.
- Mesa 4 migration is in-flight, `mesa-llm` is alpha and will rewrite against Mesa 4; plain Mesa 3 adapter is the stable integration point (Track E item 3) - motivates Slot B choice of plain Mesa over mesa-llm.
- Refusing defense + predictive policing + PSYOP segments is a positioning moat in 2026 (Track B) and aligns with EU Horizon + Korean MIC + IRB expectations (Track C) - motivates Slot C.
- NVIDIA Nemotron-Personas already covers 7 countries (USA, Japan, India, Brazil, Singapore, France, Korea) under a consistent CC-BY-4.0 methodology, but the schemas are similar-but-not-identical across countries and no harmonized cross-country persona ontology exists in the field (multi-country research addendum, 2026-04-23) - motivates Slot D.

---

## 1. Slot A - Response-Cache Layer in Core

Effort estimate: 5-8 hours.

Rationale: Every downstream integration that calls an LLM (A-MEM evolution loop, Concordia entity act, mesa-llm, Letta adapter, behavioral-fidelity eval harness, HugAgent runs) has non-deterministic sampling at the edge. Track A and Track E independently concluded that Luvoire's deterministic-replay contract must be built as `recorded side-effects + deterministic core`, not `redo from scratch`. This slot ships that contract as a first-class core module so every later LLM-touching slot can declare replay safety by construction.

### 1.1 Inputs

- `src/luvoire/core/` (existing deterministic core)
- `src/luvoire/llm/` (existing LLM gateway)
- Existing tests under `tests/` that exercise LLM calls (check current state; likely `tests/test_llm_*.py`)

### 1.2 Deliverables

1. New module `src/luvoire/core/replay_cache.py` implementing:

   ```python
   class ReplayCache:
       """Deterministic cache of LLM side-effects keyed by (model, prompt_hash, sampling_params, seed).

       Stores request -> response with content-hash keys. On replay, ReplayCache.get() returns
       the recorded response; on record, ReplayCache.put() canonicalizes and persists. The cache
       file format is newline-delimited msgpack (NDMP) for streaming writes and SHA256-stable
       ordering.
       """

       def __init__(self, path: Path, mode: Literal["record", "replay", "off"] = "off"): ...

       def key(self, *, model: str, prompt: str, sampling: Mapping[str, Any], seed: int) -> str:
           """Canonicalize inputs and return a stable SHA256 hex digest."""

       def get(self, key: str) -> Optional[RecordedResponse]: ...

       def put(self, key: str, response: RecordedResponse) -> None: ...

       def close(self) -> None: ...
   ```

   - `RecordedResponse` is a frozen dataclass with fields: `text: str`, `finish_reason: str`, `prompt_tokens: int`, `completion_tokens: int`, `model_fingerprint: Optional[str]`, `captured_at: datetime`.
   - Key canonicalization MUST be stable across Python minor versions: sort `sampling` keys alphabetically, coerce numeric values to JSON-safe form, hash `prompt` as UTF-8 bytes, include `seed` as a decimal integer. Document the canonicalization in a module docstring.
   - File format: NDMP with header record `{"format": "luvoire.replay_cache.v1", "created_at": ISO8601}` as line 0. Every subsequent line is one `{"key": str, "response": RecordedResponse.as_dict()}` record. Append-only during record mode.

2. New module `src/luvoire/llm/gateway.py` change (or whatever the current LLM entry file is called - discover via `grep -rn "openai" src/luvoire/llm/`): wrap every outbound LLM call in a `ReplayCache`-aware shim:

   - Read `LUVOIRE_REPLAY_CACHE_PATH` env var. If unset, mode is `off` and current behavior is preserved bit-for-bit.
   - In `replay` mode, every uncached key MUST raise `ReplayCacheMiss`; the caller MUST NOT fall back to a live LLM call silently.
   - In `record` mode, cache hits are served from the cache; cache misses call the LLM and persist.

3. New CLI: `python -m luvoire.cli replay-cache inspect <path>` that prints a summary (record count, unique models, first/last capture timestamp, total bytes). Helper for debugging, not a user-facing feature.

4. Tests under `tests/test_replay_cache.py`:

   - Key-canonicalization golden test: a fixed set of (model, prompt, sampling, seed) inputs MUST produce a stable SHA256 digest. Lock 12 golden digests in the test file. Store the fixture at `tests/fixtures/replay_cache_keys.json`.
   - Round-trip test: write 3 records, close, reopen, read-back all 3 with identical bytes.
   - Replay-miss test: record cache with 2 entries, open in `replay` mode, request a 3rd unrecorded key, assert `ReplayCacheMiss` raised.
   - Concurrent-write guard: simulate two processes recording to the same cache path, assert either (a) second writer waits for file lock, or (b) second writer fails fast with clear error. Pick one; document which.
   - No test may require a live LLM call; use a deterministic fake `LLMClient` fixture.

5. Documentation update `docs/architecture.md`: new section `Replay Cache` placed immediately after the existing `Determinism` section. Explain: (a) why (recorded side-effects vs. redo-from-scratch), (b) the three modes, (c) env var control, (d) the canonicalization contract, (e) explicit caveat that closed-API LLMs drift - the cache records a specific model fingerprint and is only valid for replays against that fingerprint.

6. New entry in `CHANGELOG.md` under an un-released `[Unreleased]` heading at the top:
   - `Added: luvoire.core.replay_cache (record/replay modes for deterministic LLM side-effects).`
   - `Added: LUVOIRE_REPLAY_CACHE_PATH env var; unset = current behavior.`

### 1.3 Constraints

- No change to the public `luvoire.City(...)` / `luvoire.run(...)` API surface.
- No change to any existing msgpack replay file (see 0.6).
- `mode == "off"` MUST be a zero-overhead path - no caching code paths executed.
- The default behavior when `LUVOIRE_REPLAY_CACHE_PATH` is unset MUST equal pre-slot behavior exactly. CI will diff a canary run before and after; SHAs must match.

### 1.4 Verification

Standard gate (0.5) plus:

- `pytest tests/test_replay_cache.py` - new tests pass.
- Canary replay check: `python scripts/verify_replay_shas.py` (existing script) - no msgpack SHA regressed.
- `python -m luvoire.cli replay-cache inspect tests/fixtures/sample_cache.ndmp` - prints 3 records, exits 0.
- `grep -rn "ReplayCache" src/` returns only matches in `src/luvoire/core/replay_cache.py` and `src/luvoire/llm/gateway.py` (no stray imports elsewhere).

### 1.5 Commit Message

```
feat(core): add replay cache for deterministic LLM side-effects

Motivates downstream A-MEM, Concordia, mesa-llm, and behavioral-fidelity
integrations by making "recorded side-effects + deterministic core" a
first-class contract. Adds luvoire.core.replay_cache with record/replay
modes, env-var control (LUVOIRE_REPLAY_CACHE_PATH), canonicalized cache
keys with golden-digest test, NDMP storage format, and docs/architecture
entry.

No change to public API. Default off when env var unset; pre-existing
msgpack replay SHAs verified unchanged.
```

### 1.6 Close Criteria

- All gates (0.5) green.
- `planning/codex_session_report_2026-04-23.md` appended with a Slot A section listing commit SHA, files changed, and test counts.

---

## 2. Slot B - Mesa 3 Adapter + ODD Markdown Exporter

Effort estimate: 5-7 days.

Rationale: Mesa is the Python-native ABM standard and the field's publication pipeline. Track B found that Mesa added an official `mesa-llm` GSoC 2026 project; Track E found `mesa-llm` is still alpha and explicitly marked for Mesa 4 rewrite (`mesa-llm` issue #273). Plain Mesa 3 is the stable layer. Shipping a plain Mesa 3 adapter PLUS an ODD-protocol markdown exporter (Grimm et al. 2020, JASSS) turns Luvoire runs into publication-ready methods sections with one command. No competing LLM-agent framework ships ODD export today.

### 2.1 Inputs

- Mesa 3 (stable, PyPI `mesa[rec]>=3.0,<4`). Python 3.12 hard requirement.
- `src/luvoire/scenario_synthesis.py` (existing scenario layer - reference for config shape)
- `src/luvoire/agents/**` (existing agent interface)
- Reference: Grimm, Railsback, Vincenot, Berger, Gallagher, DeAngelis, Edmonds, Ge, Giske, Groeneveld, Johnston, Milles, Nabe-Nielsen, Polhill, Radchuk, Rohwader, Stillman, Thiele, Ayllón (2020). "The ODD Protocol for Describing Agent-Based Models: A Second Update." JASSS 23(2) 7. https://www.jasss.org/23/2/7.html

### 2.2 Deliverables

1. New optional extra in `pyproject.toml`:

   ```toml
   [project.optional-dependencies]
   mesa = ["mesa[rec]>=3.0,<4"]
   ```

   DO NOT add `mesa` to default runtime dependencies. Adapter is behind the `luvoire[mesa]` extra.

2. New package `src/luvoire/adapters/mesa/` with:

   - `__init__.py` exporting `LuvoireMesaAgent`, `LuvoireMesaModel`, and `to_mesa_model(sim: Simulation, seed: int) -> mesa.Model`.
   - `agent.py`:

     ```python
     import mesa
     from luvoire.agents import Agent as LuvoireAgent

     class LuvoireMesaAgent(mesa.Agent):
         def __init__(self, model: mesa.Model, luv_agent: LuvoireAgent):
             super().__init__(model)
             self.luv = luv_agent

         def step(self) -> None:
             obs = self.model.observe(self.luv)
             action = self.luv.act(obs)
             self.model.apply(self.luv, action)
     ```

   - `model.py`:

     ```python
     import mesa
     from luvoire.simulation import Simulation

     class LuvoireMesaModel(mesa.Model):
         def __init__(self, sim: Simulation, seed: int = 0):
             super().__init__(seed=seed)
             self.luv = sim
             for a in sim.agents:
                 LuvoireMesaAgent(self, a)

         def step(self) -> None:
             self.agents.shuffle_do("step")

         def observe(self, agent): ...  # delegate to Luvoire sim
         def apply(self, agent, action): ...
     ```

   - Do NOT call any LLM from the adapter layer itself. LLM calls must flow through the existing `luvoire.llm.gateway`, which in turn MAY go through the replay cache from Slot A if the env var is set.

3. New package `src/luvoire/export/odd/` with:

   - `odd_schema.py` defining `OddReport` as a pydantic or dataclass model with the seven ODD sections: `purpose_and_patterns`, `entities_state_variables_scales`, `process_overview_and_scheduling`, `design_concepts`, `initialization`, `input_data`, `submodels`. Each is a `str` field; the schema stores human-authored markdown fragments.
   - `populate.py` with `def populate_from_simulation(sim: Simulation, scenario: Scenario) -> OddReport` that fills the machine-derivable fields: entity names, state variables, RNG seed, scheduler type, LLM model + fingerprint, run duration. Human-authored sections (`purpose_and_patterns`, `design_concepts`) default to a stub `"TODO: author this section"` string.
   - `render.py` with `def render_markdown(report: OddReport) -> str` that emits the canonical 7-section markdown document with top matter:

     ```markdown
     # ODD Protocol Description

     Generated by Luvoire v{VERSION} on {DATE}.
     Reference: Grimm et al. 2020, JASSS 23(2) 7.

     ## 1. Purpose and Patterns
     ...
     ```

   - `cli.py` hook so `python -m luvoire.cli export odd <scenario.yaml> --out odd_report.md` works end-to-end.

4. Tests under `tests/test_mesa_adapter.py` (skipped cleanly if `mesa` extra not installed via a `pytest.importorskip("mesa")` guard at module top):

   - Smoke test: build a 10-agent Luvoire simulation, wrap with `to_mesa_model`, step 5 ticks, assert the underlying Luvoire simulation state advanced.
   - Determinism test: two independent `LuvoireMesaModel(sim, seed=42)` instances must produce identical agent-state trajectories for 20 ticks. MUST pass without the replay cache (no LLM calls in the tiny smoke sim).
   - Import-isolation: `import luvoire` without `mesa` installed must still succeed (pytest marker skips the adapter tests).

5. Tests under `tests/test_odd_exporter.py`:

   - Golden-file test: a fixed scenario (`tests/fixtures/odd_golden_scenario.yaml`) rendered via `render_markdown` MUST byte-match `tests/fixtures/odd_golden_report.md`.
   - Seven-section coverage: parsed output has seven top-level `## ` headings in the canonical order.
   - Stub detection: fields left as `TODO: author this section` produce a non-fatal warning on `render_markdown` (stderr or logger.warning). Test asserts one warning appears for a stub-only report.

6. Documentation updates:

   - New `docs/adapters/mesa.md` explaining installation (`pip install luvoire[mesa]`), a 30-line runnable example, and a paragraph on why plain Mesa rather than mesa-llm.
   - New `docs/export/odd.md` with the seven-section reference, a 15-line invocation example, and a link to the Grimm 2020 JASSS paper.
   - Add both pages to `mkdocs.yml` navigation under a new `Adapters` and `Export` section as appropriate.

7. `CHANGELOG.md` `[Unreleased]` additions:
   - `Added: luvoire.adapters.mesa (plain Mesa 3 integration, behind luvoire[mesa] extra).`
   - `Added: luvoire.export.odd (Grimm 2020 ODD protocol markdown exporter; python -m luvoire.cli export odd).`

### 2.3 Constraints

- No change to any existing msgpack replay file (see 0.6).
- `mesa-llm` is NOT a dependency. Do not import it. If a test surfaces a reason to integrate mesa-llm, halt and flag in the session report for a later handoff.
- Default runtime with no Mesa installed MUST preserve pre-slot behavior exactly.
- The ODD exporter MUST NOT call any LLM. It is a pure code -> markdown transformation. Human authoring of stub sections is left to the researcher.

### 2.4 Verification

Standard gate (0.5) plus:

- `pytest tests/test_mesa_adapter.py tests/test_odd_exporter.py` green (adapter tests auto-skip if Mesa not installed in the default dev extra; install Mesa before gating).
- `pip install -e .[mesa]` succeeds cleanly in the verification shell.
- `python -m luvoire.cli export odd examples/scenarios/gangnam_7pm.yaml --out /tmp/odd.md` exits 0 and `/tmp/odd.md` is a valid 7-section document.
- mkdocs navigation renders both new pages without warnings.

### 2.5 Commit Message

```
feat(adapters+export): add Mesa 3 adapter and ODD protocol exporter

Wires Luvoire simulations into the Mesa 3 ABM ecosystem behind the
luvoire[mesa] extra (plain Mesa, not mesa-llm; see docs/adapters/mesa.md
for rationale) and ships a Grimm 2020 ODD protocol markdown exporter
that turns a Luvoire scenario into a publication-ready methods section
in one command.

Both additions preserve the deterministic core. Neither calls an LLM.
No existing msgpack replay SHAs changed.
```

### 2.6 Close Criteria

- All gates (0.5) green with `luvoire[mesa]` installed.
- `planning/codex_session_report_2026-04-23.md` appended with a Slot B section.

---

## 3. Slot C - Civilian-Only Use Policy

Effort estimate: 4-6 hours.

Rationale: Tracks B and C converged on a concrete positioning moat: every commercial competitor is quietly chasing DoD/MIC or predictive-policing contracts in 2025-2026, and EU Horizon + Korean MIC + university IRBs increasingly require explicit non-military + non-surveillance declarations. Shipping a public, version-pinned "Civilian Use Policy" before the Didimdol grant submission (2026-04-29) materially strengthens the ethics section of the application and serves as a durable PR asset with public funders. This is a Codex-suitable slot because the implementation is strings + file placement; the wording is load-bearing and pre-authored below.

### 3.1 Inputs

- `README.md`, `README.ko.md`
- `docs/` (mkdocs)
- `site-snapshot/index.html` (site v7 landing)
- `website/components/LuvoireLanding.tsx` (ported Next.js landing)
- `website/public/pricing.html`
- Any existing `TERMS.md`, `POLICIES.md`, or similar - discover via `ls` and `grep -l -i "terms" *.md`.

### 3.2 Deliverables

1. New file `POLICIES/civilian_use.md` containing the authoritative policy text below. DO NOT paraphrase or trim; the exact wording is load-bearing for Didimdol and for future compliance cross-references:

   ```markdown
   # Civilian Use Policy

   Version 1.0 - effective 2026-04-23

   Luvoire is a research and commercial engine for civilian multi-agent simulation.
   The project and its maintainer (Celovin) decline the following use categories,
   regardless of payment:

   1. Military operational wargaming, targeting support, or battle-damage assessment
      for armed forces, intelligence services, or defense contractors acting in
      operational capacities.
   2. Predictive policing, individual crime-risk scoring, or any law-enforcement
      application that produces a per-person risk or suspicion ranking.
   3. Persuasion, influence, disinformation, or PSYOP optimization for political
      campaigns, electoral targeting, or state information operations, regardless
      of attribution or cover.
   4. Non-consenting real-person simulation: twinning a named natural person from
      their public or private data without that person's IRB-grade consent.
   5. Minors in synthetic-subject pipelines: simulation of identified or
      identifiable individuals under 18 without IRB approval plus parental consent.

   Counter-disinformation, emergency preparedness, de-escalation training, urban
   planning, public-health scenario analysis, and academic computational-social-
   science research remain supported, subject to the same re-identification,
   provenance, and transparency controls documented in the Luvoire technical report.

   This policy is versioned. Updates are announced in CHANGELOG.md with a two-
   version deprecation window before any category here is relaxed.

   Contact: hello@celovin.com
   ```

2. New file `POLICIES/civilian_use.ko.md`: a professional Korean translation of the above. Translation must preserve category numbering and the "regardless of payment" clause. Use formal research-context Korean (해요체 금지, 문어체 유지). Flag to user in session report if any term needs vocabulary decision; DO NOT guess domain terms like "wargaming" or "PSYOP" - use commonly-accepted translations (`워게이밍`, `심리전`).

3. Update `README.md`:
   - New section `## Civilian Use Policy` placed immediately after the existing `## License` section. Body: one paragraph summary plus a link to `POLICIES/civilian_use.md`.

4. Update `README.ko.md` in parallel with the same structure, linking `POLICIES/civilian_use.ko.md`.

5. Add a sidebar link to `docs/` via `mkdocs.yml` navigation: new `Policies` -> `Civilian Use` entry.

6. Update `site-snapshot/index.html` footer: add `<a href="../POLICIES/civilian_use.md">Civilian Use</a>` to the existing Company column (the column that already lists About, hello@celovin.com, GitHub, Status). Preserve existing ordering; insert the new link between GitHub and Status.

7. Update `website/components/LuvoireLanding.tsx` footer Company column in parallel:

   ```tsx
   <li><a href="https://github.com/Celovin/luvoire/blob/main/POLICIES/civilian_use.md">Civilian Use</a></li>
   ```

   between the existing `GitHub` and `Status` `<li>` entries.

8. Update `website/public/pricing.html` footer if it has a mirrored Company column. If the file does not have one, skip with a note in the session report.

9. `CHANGELOG.md` `[Unreleased]` addition:
   - `Added: POLICIES/civilian_use.md and .ko.md (public refusal of defense, predictive policing, PSYOP, non-consenting twinning, minors-in-synthetic-pipelines).`

### 3.3 Constraints

- The policy text in deliverable 1 is user-reviewed pre-authored wording. Codex MUST NOT edit the English text beyond fixing typos. Any proposed change is posted as a comment in the session report for user sign-off; the slot does not close until the user approves.
- No change to any existing msgpack replay file (see 0.6).
- No code under `src/luvoire/` is changed in this slot. If Codex identifies a runtime check ("refuse to run if `luvoire.policy.military_wargaming` flag asserted") that is **out of scope** - defer to a later handoff.

### 3.4 Verification

Standard gate (0.5) plus:

- `git ls-files POLICIES/` shows exactly two files: `civilian_use.md` and `civilian_use.ko.md`.
- `python -m mkdocs build --strict` emits no warning about the new `Policies` nav section.
- `grep -rn "Civilian Use" README.md README.ko.md site-snapshot/index.html website/components/LuvoireLanding.tsx` finds at least one match in each.

### 3.5 User Sign-Off Gate

Before committing, post the Korean translation in deliverable 2 verbatim to `planning/codex_session_report_2026-04-23.md` under a subsection titled `Slot C - Pending KO Translation Review`. Halt with `Slot C PAUSED: awaiting user approval of KO translation`. Resume only after the user acknowledges in session the translation is acceptable or posts a revised version. The commit (step 9 of the standard gate) must include the approved text exactly.

### 3.6 Commit Message

```
feat(policy): publish Civilian Use Policy v1.0

Documents the project's refusal of five use categories - military
wargaming, predictive policing, PSYOP/influence optimization, non-
consenting real-person twinning, and minors in synthetic pipelines -
with a two-version deprecation window on future changes. Policy is
versioned under POLICIES/, linked from README in EN/KO, mkdocs
navigation, and both the static site-snapshot and Next.js landing
footers.

Aligns with Didimdol 2026 ethics framing and EU Horizon / Korean MIC
funder expectations. Translation reviewed by user per §3.5 gate.
```

### 3.7 Close Criteria

- All gates (0.5) green.
- User sign-off on KO translation recorded in session report.
- `planning/codex_session_report_2026-04-23.md` appended with a Slot C section.

---

## 4. Slot D - Nemotron-Personas Multi-Country Loader + Luvoire Persona Interface v1

Effort estimate: 7-10 days.

Rationale: The 2026-04-23 multi-country persona research addendum (see `planning/codex_session_report_2026-04-23.md` for the full findings, or recompute via web search) established that NVIDIA's Nemotron-Personas family already covers seven countries under one CC-BY-4.0 methodology: USA (6M), Japan (6M), India (21M EN+Hindi), Brazil (6M PT-BR), Singapore (888K EN+Singlish), France (1M, 18+), and Korea (6M; Luvoire's existing base). No open alternative is both commercial-safe and census-grounded (PersonaHub is CC-BY-NC-SA; Stanford Park 2024 transcripts are gated; Twin-2K-500 is US-only). The schemas are similar but not identical across countries (India adds religion + script variants; France drops under-18; Singapore adds ethnicity; Korea uses honorifics fields). Nobody in the field has published a harmonized cross-country persona ontology, which leaves a clean NeurIPS Datasets & Benchmarks 2026 submission slot. This slot ships (a) the multi-country loader and (b) the v1 harmonization layer ("Luvoire Persona Interface," LPI) as a commercial-safe foundation for multi-national simulation and the academic paper axis.

### 4.1 Inputs

- `src/luvoire/personas/` (existing Korean persona handling; treat as reference and extend; discover current shape via `ls src/luvoire/personas/` and `grep -rn "KOSIS\|Nemotron" src/luvoire/`)
- Local dataset memory note `C:\Users\admin\.claude\projects\c--Users-admin--codex\memory\nemotron-personas-korea.md` — confirms local Korea parquet shards at `D:\datasets\nemotron-personas-korea\`, pattern to mirror for other countries.
- HuggingFace datasets (CC-BY-4.0, verified existence 2026-04-23):
  - `nvidia/Nemotron-Personas-USA`
  - `nvidia/Nemotron-Personas-Japan`
  - `nvidia/Nemotron-Personas-India`
  - `nvidia/Nemotron-Personas-Brazil`
  - `nvidia/Nemotron-Personas-Singapore`
  - `nvidia/Nemotron-Personas-France`
  - `nvidia/Nemotron-Personas-Korea` (verify exact HF slug at build time; local copy is authoritative if HF slug moves)
- Distortion literature to cite in docs: Twin-2K-500 "Funhouse Mirrors" paper (arXiv:2509.19088) naming 5 persona distortions including blue-shift.

### 4.2 Deliverables

1. New module `src/luvoire/personas/lpi.py` defining **Luvoire Persona Interface v1** — a harmonized cross-country persona dataclass:

   ```python
   COUNTRY_ISO = Literal["USA", "JPN", "IND", "BRA", "SGP", "FRA", "KOR"]

   @dataclass(frozen=True, slots=True)
   class LPIPersona:
       persona_id: str
       country_iso: COUNTRY_ISO
       language_locale: str            # e.g., "en-US", "ja-JP", "hi-IN-Deva", "pt-BR", "en-SG", "fr-FR", "ko-KR"
       age: Optional[int]              # years; None for France persona pre-18 exclusion contexts
       sex: Optional[Literal["F", "M", "X"]]
       region_l1: Optional[str]        # state / prefecture / region-level 1
       region_l2: Optional[str]        # county / ward / region-level 2
       education_isced: Optional[int]  # ISCED-2011 level 0-8, mapped from source taxonomy
       occupation_isco08: Optional[str]  # ISCO-08 major group code, mapped from source taxonomy
       income_bracket_oecd: Optional[Literal["q1", "q2", "q3", "q4", "q5"]]  # household income quintile
       household_size: Optional[int]
       marital_status: Optional[Literal["single", "married", "divorced", "widowed", "other"]]
       big5: Optional[Mapping[Literal["O", "C", "E", "A", "N"], float]]
       narrative_text: str             # the persona backstory from the source dataset
       grounding_source: str           # e.g., "nvidia/Nemotron-Personas-USA@v1.0"
       grounding_version: str          # dataset revision SHA / release tag
       distortion_flags: tuple[str, ...] = ()  # e.g., ("blue_shift_risk", "moderation_collapse_risk")
       extras: Mapping[str, Any] = field(default_factory=dict)  # country-specific fields preserved verbatim
   ```

   - `extras` holds any country-specific attribute that does not map onto a harmonized field (India religion, Singapore ethnicity, Korea honorifics, France department code). Those fields are NOT silently dropped.
   - Include `LPIPersona.to_dict()` / `from_dict()` + a JSON schema export at `src/luvoire/personas/lpi_schema.json` derived from the dataclass via introspection.

2. New module `src/luvoire/personas/loaders/` with one file per country and a registry:

   ```
   src/luvoire/personas/loaders/
       __init__.py          # exports load_country(iso: str) -> Iterator[LPIPersona]
       nemotron_base.py     # shared parquet-reader, attribution logging, license gate
       usa.py
       japan.py
       india.py
       brazil.py
       singapore.py
       france.py
       korea.py             # reuses existing Korea pipeline; refactor to emit LPIPersona
   ```

   - `nemotron_base.load_parquet_shards(path_or_hf_id)` handles: (a) local path first (mirrors Korea pattern at `D:\datasets\nemotron-personas-*`), (b) falls back to `datasets.load_dataset(..., split="train", streaming=True)` if local shards absent, (c) logs a CC-BY-4.0 attribution line on first call (once per process).
   - Each country file implements `def iter_personas() -> Iterator[LPIPersona]` that (i) reads source rows, (ii) maps source columns to LPI fields via country-specific mapping tables, (iii) writes country-specific fields to `extras`, (iv) sets `distortion_flags` per source-dataset known-issue list (default: `("llm_narrative_synthetic",)` for all, plus `("blue_shift_risk",)` when the narrative includes political-axis vocabulary — a simple keyword check documented in the file).
   - Country-specific mapping tables live next to the loader as `*_mapping.py` constants (e.g., `usa_mapping.py` maps BLS SOC codes to ISCO-08). Tables are hand-curated; not auto-generated. Put 1-page `# source: ...` comment headers citing the reference table used.

3. Public API at `src/luvoire/personas/__init__.py`:

   ```python
   from luvoire.personas.lpi import LPIPersona, COUNTRY_ISO
   from luvoire.personas.loaders import load_country, list_countries

   # Example:
   # for p in load_country("USA"):
   #     ...  # p is LPIPersona
   ```

   - `load_country(iso, *, limit: Optional[int] = None, seed: Optional[int] = None)` supports deterministic sampling: when `seed` is set, the loader uses a seeded RNG to select `limit` personas from the shard stream in a reproducible order. Document that determinism requires a fixed dataset revision (`grounding_version`) — drift in upstream HF tags breaks replay.
   - `list_countries() -> tuple[COUNTRY_ISO, ...]` returns the 7 ISO codes.

4. CLI:

   - `python -m luvoire.cli personas list` prints the 7 countries with `(iso, population_source, record_count, license, grounding_version)`.
   - `python -m luvoire.cli personas sample --country USA --n 10 --seed 42` streams 10 LPI personas as NDJSON for quick inspection.
   - `python -m luvoire.cli personas schema --out lpi_schema.json` writes the LPI JSON schema.

5. Tests under `tests/test_personas_lpi.py` and `tests/test_personas_loaders.py`:

   - LPI dataclass round-trip: `to_dict(from_dict(d)) == d` for a 20-persona golden fixture covering all 7 countries (1-3 personas each).
   - Loader registry: `list_countries()` returns exactly the 7 ISOs and no others.
   - Determinism: `load_country("USA", limit=100, seed=42)` produces the same first-persona `persona_id` in two independent processes (pin via small golden fixture rather than hitting HF in CI).
   - Attribution log test: load one persona from each country; assert a CC-BY-4.0 attribution line was emitted once per country per process (not per persona).
   - Distortion flag contract: all personas carry at least `("llm_narrative_synthetic",)`.
   - Schema export: generated `lpi_schema.json` validates against a JSON-Schema draft-2020-12 validator.
   - All tests MUST run without network access — fixtures mock the parquet read with small frozen parquet files stored under `tests/fixtures/personas/{iso}/`. Fixtures are ≤100 rows per country.
   - A separate `tests/test_personas_hf_smoke.py` marked `@pytest.mark.hf_live` performs a single 1-row `streaming=True` read per country and is `skip`-ed unless `LUVOIRE_HF_LIVE=1` is set. Runs nightly in a separate CI job, never in the default `pytest` gate.

6. Documentation:

   - New `docs/personas/lpi.md` — the authoritative LPI v1 schema description. Includes: (a) rationale (harmonization gap, Nemotron schema divergence table), (b) the 16 harmonized fields with cross-country mapping examples, (c) `extras` contract, (d) determinism + grounding-version caveat, (e) distortion literature citation (arXiv:2509.19088), (f) explicit list of unverified fields per country (e.g., India caste/language axes not mapped into LPI core).
   - New `docs/personas/countries.md` — one section per country: source HF dataset URL, license attribution text to quote in downstream artifacts, known caveats (France 18+, Korea honorifics, India script variants, Singapore ethnicity, Brazil CBO occupation expansion, Japan small-sample tails, USA region granularity).
   - Update `mkdocs.yml` navigation with a new `Personas` section.
   - Update `README.md` "Datasets" section (or create) citing the 7-country coverage and the CC-BY-4.0 attribution requirement.

7. `CHANGELOG.md` `[Unreleased]` additions:
   - `Added: luvoire.personas.lpi - Luvoire Persona Interface v1 (harmonized cross-country persona dataclass + JSON schema).`
   - `Added: luvoire.personas.loaders - multi-country Nemotron-Personas loaders for USA, Japan, India, Brazil, Singapore, France, Korea (all CC-BY-4.0).`
   - `Added: python -m luvoire.cli personas {list,sample,schema} CLI.`

### 4.3 Constraints

- No change to any existing msgpack replay file (see 0.6).
- The existing Korea persona pipeline MUST continue to function unchanged for any caller that has not migrated to LPI. Add LPI as an additional output path; do not break the old one. Mark the old Korea-only path `# deprecated: migrate to luvoire.personas.loaders.korea.iter_personas()` but leave it callable for at least one release.
- Do NOT vendor any persona data into the repo. Tests use small fixture shards under `tests/fixtures/personas/` that are hand-crafted synthetic rows (not copied from upstream datasets) — cite this in fixture headers to avoid re-licensing confusion.
- Do NOT add `datasets` (HuggingFace) to the default runtime dependency tree. Put it under an optional extra `luvoire[personas]` alongside `pyarrow`. Default runtime must still import cleanly without it.
- Do NOT introduce any country outside the 7 Nemotron-supported set in this slot. Germany / UK / China Tier-B builds are deferred to a later handoff.
- Do NOT call an LLM anywhere in the loader or LPI code. Narrative text is loaded verbatim from the source dataset.

### 4.4 Verification

Standard gate (0.5) plus:

- `pip install -e .[personas]` succeeds.
- `pytest tests/test_personas_lpi.py tests/test_personas_loaders.py` - green.
- `pytest tests/test_personas_hf_smoke.py` - SKIPPED in default gate (verify skip reason text mentions `LUVOIRE_HF_LIVE`).
- `python -m luvoire.cli personas list` prints exactly 7 rows with the expected ISO codes.
- `python -m luvoire.cli personas sample --country USA --n 3 --seed 42` emits 3 valid NDJSON lines using the test fixture (configure to point at the test fixtures when running under verification).
- `python scripts/verify_replay_shas.py` - no msgpack SHA regressed.
- mkdocs navigation renders the new `Personas` section without warnings.
- `grep -rn "Nemotron-Personas-" src/luvoire/` finds at least one attribution string per country.

### 4.5 Commit Message

```
feat(personas): add multi-country Nemotron loader and Luvoire Persona Interface v1

Ships CC-BY-4.0 loaders for NVIDIA Nemotron-Personas across USA, Japan,
India, Brazil, Singapore, France, and Korea (7 countries; total ~47M
personas) behind the luvoire[personas] extra, plus a harmonized
Luvoire Persona Interface (LPI v1) that maps divergent per-country
Nemotron schemas onto a common 16-field dataclass with an `extras`
escape hatch for country-specific axes (India religion/script,
Singapore ethnicity, Korea honorifics, France department, etc.).

Includes deterministic sampling (seed + pinned grounding_version),
distortion_flags per arXiv:2509.19088 Funhouse-Mirrors taxonomy,
CC-BY-4.0 attribution logging, CLI (personas list/sample/schema),
JSON schema export, and per-country documentation.

No change to public simulation APIs or existing msgpack replay SHAs.
Old Korea-only persona path preserved with deprecation marker.
```

### 4.6 Close Criteria

- All gates (0.5) green.
- `planning/codex_session_report_2026-04-23.md` appended with a Slot D section listing commit SHA, files changed, test counts, and the final LPI field list (so the next handoff can reference it verbatim).
- A single-paragraph summary of "Luvoire now supports 7 countries; first harmonized cross-country persona interface in the field" is dropped into `planning/codex_session_report_2026-04-23.md` tagged `### Slot D - Didimdol-ready one-liner` for easy copy-paste into the proposal.

---

## 5. Handoff Close (After Slot D)

Codex creates `planning/NIGHT_REPORT_luvoire_research_hardening_v1_2026-04-23.md` summarizing:

- The four slots (commit SHAs, files changed, test counts).
- Any blocker or deferred item encountered.
- Suggested next-handoff inputs. In particular, confirm whether the following candidates are ready:
  - Slot E candidate: C2PA 2.2 manifest emission on replay artifacts (deadline 2026-08-02).
  - Slot F candidate: PIPA re-identification-risk evaluator for persona pipelines (deadline 2026-09-11). Now higher priority given Slot D quintuples the downstream persona surface.
  - Slot G candidate: A-MEM optional plugin behind `luvoire[amem]` extra (now safe because Slot A's replay cache exists).
  - Slot H candidate: LongMemEval-S run with gpt-4o reader, target 80-85% overall (blog + repo publication path).
  - Slot I candidate: HugAgent cross-domain belief-transfer experiment (requires Slot G).
  - Slot J candidate: Nemotron-Personas-Germany custom build (ALLBUS + Destatis, Nemotron methodology clone) as the first "Luvoire-defined" country persona release and EU Horizon differentiator.
  - Slot K candidate: cross-country migration-scenario reference simulation (e.g., Korea → Germany labor migration) using LPI as input; NeurIPS Datasets & Benchmarks 2026 or ESSA SSC 2026 Durham submission prep.

Night report structure mirrors the v7 night report for continuity.

---

## 6. Open Questions for the User (post-close, not blocking)

1. HF Space rebuild status after user renamed slug: confirm build is green or still blocked.
2. Vercel deployment status after GitHub flag lifts: confirm `website/` builds to production on the corrected Root Directory.
3. GitHub flag appeal status (ticketed with Sophia Hayes 2026-04-22): any update from support?

These are tracked here for context only. No slot is blocked on them.
