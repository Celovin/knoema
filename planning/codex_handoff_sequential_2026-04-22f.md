# Codex Sequential Handoff v6 - Commercial Wiring and Distribution Readiness

Author: Celovin (Choi Jihwan)
Date: 2026-04-22 (sixth handoff, six-slot sequential)
Working directory: `C:\Users\admin\Projects\knoema`
Deadline anchors: Didimdol grant 2026-04-29 18:00 KST; commercial PoC readiness target 2026-05-31.

Prerequisite: v5 (`planning/codex_handoff_sequential_2026-04-22e.md`) MUST be closed before any slot of this handoff starts. v5 Slot F produced the static status page and 15-minute cron; v6 builds on top of v5's billing primitives, legal drafts, SBOM, pricing page, and status page.

Scope of v6: connect v5 billing primitives to the actual product surface (API server), add audit-log coverage for commercial events, ship customer onboarding CLI, publish public replay benchmark numbers, add opt-in observability, and expand the status page with rolling uptime. Rebrand (Knoema name change) remains deferred to a future v7 handoff. PyPI release, Docker image, and GDPR data-subject endpoints are explicitly out of scope (user-only decisions).

Context:
- v5 shipped `src/knoema/billing/` (gateway, webhooks, api_keys, markup, stripe_adapter, tiers) but did NOT wire it into `src/knoema/api/server.py`. v6 Slot A closes that gap.
- `src/knoema/safety/audit_log.py` exists but is not invoked from any `knoema.billing` module. v6 Slot B closes that gap.
- v5 Slot F `status.html` shows a 30-day history bar only; v6 Slot F adds 7/30/90-day rolling uptime percentages and SLA-target badges.

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

### 0.3 Environment Bootstrap

```bash
cd /c/Users/admin/Projects/knoema
export $(grep -v '^#' .env.local | xargs)
.venv/Scripts/python.exe -m pip install -e .[dev]
.venv/Scripts/python.exe -m pip install 'opentelemetry-api>=1.25,<2' 'opentelemetry-sdk>=1.25,<2' 'prometheus-client>=0.20,<1.0'
```

Required env vars: `HF_TOKEN`, `OPENAI_API_KEY`. Optional for tests: `STRIPE_TEST_SECRET_KEY` (skip gracefully when unset).

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
7. `python -m mkdocs build --strict` - pass (Slots that touch `docs/`).
8. `git add <slot paths>` + `git commit -m "<slot commit message>"` + `git push origin main`.

None of the v6 slots touch `playground/`. Skip HF Space gates.

### 0.6 Forbidden Regression

The following msgpack files MUST remain byte-identical through all of v6. Any change = halt.

- `replay_100agents_gangnam_7pm.msgpack`: `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab`
- `replay_1000agents_gangnam_7pm.msgpack`: `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b`
- `replay_5000agents_gangnam_7pm.msgpack`: `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01`
- `replay_10000agents_gangnam_7pm.msgpack`: `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2`
- `replay_10000agents_nemotron_gangnam_7pm.msgpack`: `9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9`

The v5 tracked artifacts MUST also remain content-identical unless a slot explicitly declares it overwrites one:

- `ATTRIBUTIONS.md`, `sbom.cdx.json` (may be regenerated if and only if source deps change; CI drift check must still pass).
- `site-snapshot/pricing.html` (Slot F in v6 may expand its status link target; MUST NOT modify pricing HTML itself).

### 0.7 Actions Reserved for the User

- Actually registering as a Toss Payments / Paddle / Stripe seller.
- Publishing the pricing page to a public domain.
- Executing any customer contract.
- Choosing the rebrand name (deferred to v7).
- Deciding to publish the npm/PyPI distribution.
- Any legal review of audit-log retention windows past the default 90 days.

### 0.8 Slot Completion Report

After each slot, append a section to `planning/codex_session_report_2026-04-22.md`. After Slot F, create `planning/NIGHT_REPORT_knoema_sequential_v6_2026-04-22.md` mirroring the v5 structure.

---

## 1. Slot A - API Server Commercial Gating

Effort estimate: 3-5 hours.
Rationale: v5 shipped the billing primitives (tenant API keys, tier table, markup math, usage spool, webhook dispatcher) but never connected them to the actual HTTP surface. Customers cannot be charged nor rate-limited today because `src/knoema/api/server.py` only wires a generic IP-keyed token bucket. Slot A connects billing to the server so Pro/Team/Enterprise tier enforcement is real.

### 1.1 Inputs

- `src/knoema/billing/api_keys.py` (v5 Slot A) - hashed tenant keys, verify/rotate/revoke primitives.
- `src/knoema/billing/tiers.py` (v5 Slot A) - `TierName`, `monthly_output_token_cap`, `is_api_key_source_allowed`.
- `src/knoema/billing/gateway.py` (v5 Slot A) - `UsageMeter`, `UsageRecord`, JSONL spool path.
- `src/knoema/api/rate_limit.py` (pre-existing) - generic `TokenBucket` / `RateLimiter`.
- `src/knoema/api/server.py`, `routes/*.py` - attach point.

### 1.2 Deliverables

1. `src/knoema/api/auth.py` (new):
   - `AuthenticatedTenant` dataclass: `tenant_id`, `tier: TierName`, `api_key_id`, `api_key_source`.
   - `require_tenant()` FastAPI dependency:
     - Reads `Authorization: Bearer knoema_<id>_<secret>` header.
     - Calls `billing.api_keys.verify_key` with constant-time comparison.
     - Returns `AuthenticatedTenant` on success; raises `HTTPException(401)` on miss / revoked.
     - On success: sets response header `X-Knoema-Tenant-Tier` to the tier name.
   - `optional_tenant()` dependency variant for endpoints that allow anonymous replay-viewer access.

2. `src/knoema/api/tier_rate_limit.py` (new, wraps pre-existing `rate_limit.py`):
   - Per-tier bucket sizes loaded from `tiers.py`:
     - Free: 10 req/min burst 20.
     - Pro: 120 req/min burst 240.
     - Team: 600 req/min burst 1200.
     - Enterprise: 6000 req/min burst 12000.
   - Key strategy: `tier:{tier}|tenant:{tenant_id}` (not IP).
   - Falls through to the pre-existing IP bucket for unauthenticated endpoints so Slot A does not regress anonymous replay access.
   - Response headers on 429: `Retry-After`, `X-Knoema-RateLimit-Tier`, `X-Knoema-RateLimit-Remaining`.

3. `src/knoema/api/usage_middleware.py` (new):
   - Middleware that, for every authenticated POST/PUT that goes through `billing.gateway.LLMGateway`, records a `UsageRecord` via the in-process `UsageMeter` and writes to the JSONL spool.
   - Middleware skips GET endpoints and unauthenticated traffic.
   - Writes to `var/billing/usage_<yyyymmdd>.jsonl` using the same schema as v5 Slot A's `UsageRecord.to_json()` (no schema drift).

4. `src/knoema/api/routes/*.py` edits:
   - Attach `require_tenant` to `simulations.router`, `agents.router`, `events.router` (POST routes only).
   - Leave `ws.router` anonymous-allowed but add `optional_tenant()`; if a tenant token is presented it is validated and used for tier routing.
   - Leave `/healthz` and any existing public-read endpoints untouched.

5. `tests/test_api_commercial_gating.py` (new):
   - Auth missing -> 401 with `WWW-Authenticate: Bearer`.
   - Auth valid Pro tier -> 200 + response header `X-Knoema-Tenant-Tier: pro`.
   - Auth valid Free tier attempting Pro-only `/simulations/run?model=gpt-4o` -> 402 Payment Required with tier-upgrade message.
   - Rate limit: 200 Pro requests in 1s -> first 240 succeed (burst) then 429 with `Retry-After`.
   - Usage middleware: one authenticated call produces exactly one JSONL line with the expected schema.
   - Revoked key -> 401.
   - Constant-time comparison coverage (no timing oracle).

### 1.3 Completion Report

Commit message: `feat(api): wire billing into api server with tier-based auth and rate limit`.

Acceptance evidence:
- Authenticated request produces `X-Knoema-Tenant-Tier` header (captured in test).
- Free-tier gpt-4o attempt returns 402.
- Rate-limit 429 includes `Retry-After`.
- Usage spool JSONL line matches v5 schema byte-for-byte.

---

## 2. Slot B - Audit Log Coverage for Commercial Events

Effort estimate: 2-3 hours.
Rationale: `src/knoema/safety/audit_log.py` exists but v5 billing never invokes it. PIPA Article 29 and GDPR Article 30 both expect tamper-resistant records of who accessed what and when, especially for customer-provisioning actions. Slot B wires billing events into the existing audit log so compliance questions have a file-backed answer.

### 2.1 Inputs

- `src/knoema/safety/audit_log.py` - existing `AuditLog.append(event_type, actor, subject, metadata)` and rotating writer.
- `src/knoema/billing/api_keys.py` - `issue_key`, `rotate_key`, `revoke_key`, `verify_key`.
- `src/knoema/billing/webhooks.py` - dispatcher and retry paths.
- `src/knoema/billing/gateway.py` - tier-violation and cap-exhaustion paths.

### 2.2 Deliverables

1. Extend `src/knoema/safety/audit_log.py` event-type registry with:
   - `commercial.key_issued`
   - `commercial.key_rotated`
   - `commercial.key_revoked`
   - `commercial.webhook_dispatched`
   - `commercial.webhook_failed`
   - `commercial.webhook_exhausted` (retry budget used)
   - `commercial.tier_limit_exceeded`
   - `commercial.cap_exhausted_output_tokens`

2. `src/knoema/billing/api_keys.py` edits:
   - Inject `AuditLog` via constructor (optional; falls back to no-op logger when not supplied for unit tests).
   - `issue_key` -> `commercial.key_issued` with `subject=tenant_id`, `metadata={api_key_id, tier, issuer}`; NEVER log the plaintext secret.
   - `rotate_key` -> `commercial.key_rotated` with `metadata={old_api_key_id, new_api_key_id, tier}`.
   - `revoke_key` -> `commercial.key_revoked` with `metadata={api_key_id, reason}`.

3. `src/knoema/billing/webhooks.py` edits:
   - Each dispatch -> `commercial.webhook_dispatched` with `metadata={delivery_id, event_type, url_hash}` (URL hashed, not logged plaintext).
   - Each retry failure -> `commercial.webhook_failed`.
   - Retry budget exhaustion -> `commercial.webhook_exhausted`.

4. `src/knoema/billing/gateway.py` edits:
   - Tier-violation (Free attempting pass-through) -> `commercial.tier_limit_exceeded`.
   - Monthly output-token cap exceeded -> `commercial.cap_exhausted_output_tokens` with `metadata={cap, observed, tier}`.

5. `src/knoema/safety/audit_log.py` retention:
   - Default retention window: 90 days (Korean PIPA sufficient, aligns with internal privacy policy draft).
   - `AuditLog.purge_older_than(days=90)` helper.
   - CLI stub `scripts/audit_log_show.py tenant_id [--since 2026-04-01]` (read-only, no edit path).

6. `tests/test_commercial_audit_integration.py` (new):
   - Issue key -> audit row present with no plaintext secret.
   - Rotate key -> old and new key IDs captured.
   - Revoke key -> row present.
   - Webhook dispatcher sample path -> dispatched + failed + exhausted sequence captured.
   - Tier violation -> row present with tier metadata.
   - Cap exhaustion -> row present with cap / observed numbers.
   - `audit_log_show.py` filters by tenant correctly.

7. `docs/audit-log.md` (new):
   - Event-type catalog with what each means and what metadata is included.
   - Retention policy (90 days default).
   - Forensic query examples via `audit_log_show.py`.
   - Cross-link in `docs/legal/privacy_policy_v1_ko.md` and `..._en.md` (add a one-line pointer; do not rewrite the policies).

### 2.3 Completion Report

Commit message: `feat(audit): cover commercial key and webhook events in audit log`.

Acceptance evidence:
- All 8 new event types appear in the registry and are produced by unit tests.
- No plaintext secret ever appears in a logged metadata blob (regex test).
- Retention purge correctly removes records older than the configured window.

---

## 3. Slot C - Customer Onboarding CLI

Effort estimate: 3-4 hours.
Rationale: v5 legal drafts and pricing page tell a customer what Pro/Team/Enterprise tiers cost, but the engine has no path to provision a real customer. Slot C adds a CLI so a user can create a tenant, issue a key, rotate it, view usage, and revoke it without writing Python.

### 3.1 Inputs

- `src/knoema/billing/api_keys.py`
- `src/knoema/billing/gateway.py`
- `src/knoema/cli/` - existing click-based CLI skeleton.

### 3.2 Deliverables

1. `src/knoema/cli/customer.py` (new):
   - `knoema customer create --tenant-id <id> --tier <free|pro|team|enterprise> --display-name <str>`:
     - Creates a tenant row in `var/billing/tenants.json` (simple file-backed registry for PoC; no DB).
     - Emits `commercial.key_issued` audit event via Slot B hook.
     - Prints the new key secret ONCE to stdout with a clear "This is the only time you will see this key" warning, a 7-line box, and a `\n` after the box.
     - Exit 0 on success, 2 on invalid tier, 3 on duplicate tenant.
   - `knoema customer issue-key --tenant-id <id>`:
     - Issues an additional key for an existing tenant. Prints secret once.
   - `knoema customer rotate-key --tenant-id <id> --api-key-id <id>`:
     - Rotates the specified key; prints new secret once; marks old key revoked after a 24-hour grace window recorded in metadata.
   - `knoema customer revoke-key --tenant-id <id> --api-key-id <id> --reason <str>`:
     - Immediate revocation.
   - `knoema customer show-usage --tenant-id <id> [--month YYYY-MM]`:
     - Reads `var/billing/usage_*.jsonl`, filters by tenant and month, prints an aggregated table (model, input tokens, output tokens, cost_usd) + monthly total.
     - Output is deterministic (sorted rows) so test assertions are stable.
   - `knoema customer list`:
     - Lists all tenants with tier and key count; excludes secrets.

2. `tests/test_cli_customer.py` (new):
   - End-to-end: `create` -> `issue-key` -> call through gateway records usage -> `show-usage` shows the call -> `rotate-key` -> `revoke-key` all succeed.
   - Secret appears exactly once in stdout, never in audit log, never in tenants.json.
   - Duplicate tenant create -> exit 3.
   - Invalid tier -> exit 2.

3. `docs/customer-onboarding.md` (new):
   - 7-step quickstart with `curl` examples for a Pro-tier tenant hitting `/simulations/run`.
   - Explicit note: `var/billing/tenants.json` is the PoC registry; production will migrate to a DB (out of scope for v6).
   - Link from `docs/pricing.md` "How do I get a key?" anchor (Slot E add the anchor in Slot C, not Slot E, to avoid cross-slot order dependency).

### 3.3 Completion Report

Commit message: `feat(cli): add customer onboarding commands (create/issue/rotate/revoke/show-usage)`.

Acceptance evidence:
- E2E test passes and covers the full lifecycle.
- Secret never persists anywhere except stdout during creation or rotation.

---

## 4. Slot D - Public Replay Benchmark Publication

Effort estimate: 2-3 hours.
Rationale: Pricing page mentions "10K agent city-scale replay" as a Team/Enterprise differentiator but the number has never been published with methodology. Grant reviewers and first customers both ask for concrete throughput. Slot D publishes a deterministic benchmark with a CI regression guard.

### 4.1 Inputs

- `demo/replay/replay_{100,1000,5000,10000}agents_gangnam_7pm.msgpack`
- `demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack`
- Existing replay load code.

### 4.2 Deliverables

1. `scripts/bench_replay_throughput.py` (new):
   - Measures for each of the 5 replay artifacts: load time, total-tick wall-clock for a 20x sequential replay, peak RSS delta, frames-per-second.
   - Uses `perf_counter` and `psutil.Process().memory_info().rss`.
   - Writes JSON to `docs/benchmarks/replay-perf.json` with sorted keys and ISO timestamps to keep the file deterministic.
   - Also writes human-readable `docs/benchmarks/replay-perf.md` with a markdown table + methodology + hardware note (host CPU/RAM from `platform.uname()` and `psutil.virtual_memory().total`).
   - `--check` mode: re-runs the benchmark and compares to the committed JSON; fails with a non-zero exit if any of load_time, total_tick_wall, or frames_per_second regresses by more than 15% (tolerance accounts for Windows perf noise).

2. `tests/test_bench_replay_perf.py` (new):
   - Calls `bench_replay_throughput.py --check` against the committed JSON.
   - Skips gracefully in CI if env var `KNOEMA_SKIP_PERF_TESTS=1` (so that a slow runner does not cause false failures in PRs that do not touch replay).

3. `.github/workflows/bench_replay_perf.yml` (new):
   - Runs weekly on main + on PRs that modify `demo/replay/`, `src/knoema/replay*`, or the bench script itself.
   - Uploads `replay-perf.json` as an artifact for review.

4. `docs/benchmarks/replay-perf.md` content:
   - Table columns: agent count, grid, load_time_s, tick_wall_s_per_20x, fps_20x, rss_delta_mb, msgpack_size_mb, msgpack_sha256.
   - Source commit SHA of the artifacts (obtained from `git log -1 --format=%H <path>`).
   - Hardware caveat: "Single-thread sequential on Windows 10, i5-class CPU. Throughput on Linux / modern server-class hardware is typically 2-4x higher but not yet published."
   - Link to methodology script.

5. `mkdocs.yml` edit: add `Benchmarks: benchmarks/replay-perf.md` under Reference.

### 4.3 Completion Report

Commit message: `feat(benchmarks): publish replay throughput numbers with regression guard`.

Acceptance evidence:
- `docs/benchmarks/replay-perf.md` renders under mkdocs-strict.
- `replay-perf.json` is deterministic (re-run produces byte-identical JSON modulo the timestamp field, which is explicitly replaced in `--check` mode before comparison).
- All 5 replay SHA256 values embedded match v6 §0.6.

---

## 5. Slot E - Opt-in Observability (OpenTelemetry + Prometheus)

Effort estimate: 3-4 hours.
Rationale: Self-hosted Enterprise customers will need to plug into their own metrics and tracing stack. Cloud-tier customers need internal ops dashboards. Shipping opt-in OTel and Prometheus from the start avoids later retrofits.

### 5.1 Inputs

- `src/knoema/api/server.py`
- `src/knoema/billing/gateway.py`
- `src/knoema/api/usage_middleware.py` (from v6 Slot A)

### 5.2 Deliverables

1. `src/knoema/observability/__init__.py`, `src/knoema/observability/tracing.py`, `src/knoema/observability/metrics.py`:
   - `setup_tracing(exporter: str | None)`:
     - `None` (default) = no-op; no trace data leaves the process.
     - `"otlp"` = OTLP exporter at `OTEL_EXPORTER_OTLP_ENDPOINT`.
     - Instruments FastAPI, LiteLLM calls, billing gateway.
   - `setup_metrics(enabled: bool)`:
     - `False` (default) = no `/metrics` endpoint.
     - `True` = mounts Prometheus `/metrics` on the FastAPI app.
     - Metrics:
       - `knoema_requests_total{route, method, status, tier}`
       - `knoema_request_duration_seconds_bucket{route}`
       - `knoema_billing_tokens_total{tenant_id_hash, direction, tier}` (tenant_id hashed, never plaintext)
       - `knoema_webhook_dispatch_total{status}`
       - `knoema_rate_limit_hits_total{tier}`

2. `src/knoema/api/server.py` edit:
   - Reads `KNOEMA_OTEL_EXPORTER` and `KNOEMA_METRICS_ENABLED` env vars.
   - Calls `setup_tracing` / `setup_metrics` during lifespan startup when enabled.
   - Emits a structured log line on startup stating which observability modes are active.

3. `tests/test_observability.py`:
   - Default = no metrics endpoint (assert 404).
   - `KNOEMA_METRICS_ENABLED=1` -> 200 at `/metrics` with Prometheus exposition format.
   - `KNOEMA_OTEL_EXPORTER=otlp` with mock exporter captures at least one span per request.
   - Tenant ID is hashed, never plaintext in any metric label (regex test).

4. `docs/observability.md`:
   - When and why to enable.
   - OTLP endpoint example with Grafana Tempo, Honeycomb, Jaeger.
   - Prometheus scrape config example.
   - Cardinality warning: tenant-id hashing caps unique label count; per-route buckets are documented.
   - Cross-link from `docs/audit-log.md` ("For live metrics see observability.md; for forensic records see this page.")

5. `pyproject.toml` edit:
   - Add `[project.optional-dependencies]` entry `observability = ["opentelemetry-api>=1.25,<2", "opentelemetry-sdk>=1.25,<2", "opentelemetry-instrumentation-fastapi>=0.45b0", "prometheus-client>=0.20,<1.0"]`.
   - Do NOT add these to the base install list; they remain opt-in.

### 5.3 Completion Report

Commit message: `feat(observability): add opt-in otel tracing and prometheus metrics`.

Acceptance evidence:
- Default install does NOT import opentelemetry anywhere in the hot path (test asserts).
- With env var enabled, `/metrics` returns 200 with expected metric families.
- Tenant-ID plaintext scan over all metric labels returns 0 matches.

---

## 6. Slot F - Rolling Uptime on Status Page

Effort estimate: 2-3 hours.
Rationale: v5 Slot F shipped a 30-day history bar but no quantitative uptime. The SLA template commits to 99.5% (Pro) and 99.9% (Team). Slot F computes rolling 7/30/90-day uptime from `site-snapshot/status-history.jsonl` and displays SLA-compliance badges so customers and grant reviewers see a number, not just a bar.

### 6.1 Inputs

- `site-snapshot/status-history.jsonl` (append-only, written by v5 Slot F `fetch_status.py`).
- `scripts/build_status_page.py`
- `legal/sla_template_v1_en.md` - authoritative SLA targets.

### 6.2 Deliverables

1. `scripts/compute_uptime.py` (new):
   - Reads `status-history.jsonl`, computes 7-day, 30-day, 90-day uptime percentages for each monitored component (HF Space, CI, replay artifacts).
   - Component is considered "up" for a given sample when `status in {"RUNNING", "success", "verified"}`.
   - Writes `site-snapshot/uptime.json` with sorted keys (deterministic).
   - Handles sparse history (< 7 days) by reporting `"insufficient_data": true` and not claiming a percentage.

2. `scripts/build_status_page.py` edits:
   - Reads `uptime.json` and renders a compact 3-column table (7d / 30d / 90d) per component.
   - Adds SLA-compliance badges:
     - Green when rolling 30d uptime >= 99.9%.
     - Amber when rolling 30d uptime >= 99.5% but < 99.9%.
     - Red when rolling 30d uptime < 99.5%.
     - Gray "insufficient data" when < 7 days of history.
   - Keeps existing 30-day history bar below the new table.
   - Size budget: `site-snapshot/status.html` <= 8 KB after the addition (was 5,151 bytes; new budget accommodates the table + badges).

3. `tests/test_uptime_computation.py` (new):
   - Synthetic history with one 15-minute outage in a 30-day window -> 30d uptime = 99.965% (check to 3 decimals).
   - Sparse history (3 days) -> `insufficient_data=True`.
   - Badge color mapping is correct at the boundaries (99.9, 99.5).
   - Output JSON is deterministic across repeated runs with the same input.

4. `.github/workflows/status_page.yml` edit:
   - Add a step before `build_status_page.py`: `python scripts/compute_uptime.py` so every 15-minute tick refreshes uptime too.

5. `docs/status.md` edit:
   - One-paragraph explanation of the uptime window definitions and the sampling cadence.
   - Cross-link to the SLA template (`docs/legal/sla_template_v1_en.md`).

### 6.3 Completion Report

Commit message: `feat(status): add rolling 7/30/90-day uptime with sla badges`.

Acceptance evidence:
- `uptime.json` matches hand-computed values on a fixture history.
- `status.html` size is <= 8192 bytes after the change.
- Badge color correctly flips at the 99.9 and 99.5 boundaries in the test fixture.

---

## 7. Global Completion Report (after Slot F)

Create `planning/NIGHT_REPORT_knoema_sequential_v6_2026-04-22.md` with:

1. Execution summary table of all 6 slot commits (A through F).
2. Final verification gate output: pytest, ruff, mypy, encoding guard, gradio compat, plotly enum safety, mkdocs strict.
3. Replay SHA invariance confirmation for all 5 artifacts listed in §0.6.
4. v5 artifact content-identity confirmation for `ATTRIBUTIONS.md`, `sbom.cdx.json`, `site-snapshot/pricing.html`.
5. Secret-pattern and forbidden-entity scan results on the cumulative v6 diff: 0 / 0.
6. Audit-log event-type registry snapshot: all 8 new `commercial.*` events present.
7. `site-snapshot/status.html` final byte size.
8. `docs/benchmarks/replay-perf.json` final contents.

---

## 8. What This Handoff Does NOT Include

- PyPI release (`pip install knoema-engine`). Deferred until the user decides to make the engine public.
- Docker image / self-host packaging. Deferred to a future handoff once distribution channel is decided.
- GDPR / PIPA data-subject export and delete endpoints. Deferred pending legal review of scope.
- Interactive pricing calculator. Static table only (v5 decision).
- Hosted third-party status service. Static page only (v5 decision).
- Rebrand (Knoema name change). Blocked on user's name decision.
- Live Stripe / Toss / Paddle integration test. Each requires a real merchant account; skip gracefully when env vars are unset.
- UI for customer onboarding. CLI only in v6; web-based admin dashboard is out of scope.
- Real-user traces or production telemetry. Observability is opt-in scaffolding only.

---

## 9. Stop Conditions (halt and report, do not push through)

1. Any v5 artifact from §0.6 changes byte-content and a slot has not explicitly declared the change.
2. `git push origin main` denied (credential fix should prevent this; if it happens, halt per §0.4 wording).
3. Any Windows-only encoding issue on status / benchmark scripts (use UTF-8 explicitly everywhere).
4. `mkdocs build --strict` fails.
5. `opentelemetry-*` or `prometheus-client` fails to install in CI (fallback: mark Slot E tests with env-gated skip and proceed).
6. Any raw secret, PAT, or key appears in a staged diff (pre-commit scan must block).
7. Any forbidden entity string from §0.2 appears in a staged diff.
8. Audit-log event produces plaintext secret in metadata (regex scan in tests must catch).
9. Benchmark regression > 15% on any metric without an explicit accepted-regression comment in the PR.
10. `site-snapshot/status.html` exceeds 8,192 bytes after Slot F.
11. Any slot modifies `playground/` (v6 explicitly does not touch it).
