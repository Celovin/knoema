# Codex Sequential Handoff v5 - Commercial Stack Preparation

Author: Celovin (Choi Jihwan)
Date: 2026-04-22 (fifth handoff, bundled four-slot)
Working directory: `C:\Users\admin\Projects\knoema`
Deadline anchors: Didimdol grant 2026-04-29 18:00 KST; commercial PoC readiness target 2026-05-31.

Prerequisite: v4 (`planning/codex_handoff_sequential_2026-04-22d.md`) MUST be closed before Slot B of this handoff starts. Slot A of v5 may run independently of v4. If v4 is still in-flight when this handoff begins, Codex MUST wait for v4 to complete before entering v5 Slot B, Slot C, or Slot D.

Scope of v5: commercial readiness foundations - metering / billing gateway, Commercial Terms of Service + Privacy + DPA template drafts, consolidated attribution surface, and payment-seller onboarding reference documentation. Rebrand (Knoema name change) is deliberately excluded from this handoff and will be handled in a future v6 handoff once the target name is selected by the user.

Context:
- Nemotron-Personas-Korea license verified as `CC-BY-4.0` on 2026-04-22. Commercial use is explicitly permitted. Attribution required per CC BY 4.0.
- User-chosen payment infrastructure: Toss Payments (Korean domestic) + Paddle (Merchant of Record for global).
- User-chosen LLM cost architecture: tiered hybrid (Free = BYO-key, Pro/Team = metered pass-through with markup, Enterprise = dedicated instance).

---

## 0. Execution Contract

### 0.1 Sequential Only

Slots run in order: A -> B -> C -> D -> E -> F. Each slot closes fully (gates green, merged) before the next starts.

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
.venv/Scripts/python.exe -m pip install 'litellm>=1.40,<2.0' 'stripe>=10.0,<12.0'
```

Required env vars: `HF_TOKEN`, `OPENAI_API_KEY`, plus NEW optional: `STRIPE_TEST_SECRET_KEY` (used only by integration tests; skip gracefully when unset).

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
7. `git add <slot paths>` + `git commit -m "<slot commit message>"` + `git push origin main`.

None of the v5 slots touch `playground/`. Skip HF Space gates.

### 0.6 Forbidden Regression

The following msgpack files MUST remain byte-identical at the end of v5. Any change = halt.

- `replay_100agents_gangnam_7pm.msgpack`: `8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab`
- `replay_1000agents_gangnam_7pm.msgpack`: `0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b`
- `replay_5000agents_gangnam_7pm.msgpack`: `d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01`
- `replay_10000agents_gangnam_7pm.msgpack`: `af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2`

The Nemotron-variant 10K msgpack SHA (produced by v4 Slot B) must also remain unchanged once recorded.

### 0.7 Actions Reserved for the User

- Actually registering as a Toss Payments merchant.
- Actually registering as a Paddle seller.
- Stripe account creation and live-key generation.
- Legal review of the ToS / Privacy / DPA drafts.
- Publishing any commercial terms to the public website.
- Executing any actual customer contract.

### 0.8 Slot Completion Report

After each slot, append a section to `planning/codex_session_report_2026-04-22.md`. After Slot D, create `planning/NIGHT_REPORT_knoema_sequential_v5_2026-04-22.md`.

---

## 1. Slot A - Metering and Billing Gateway

Effort estimate: 4-6 hours.
Rationale: Tiered hybrid model (Free BYO-key / Pro+Team metered pass-through / Enterprise dedicated) requires a gateway that routes LLM calls, records usage per customer, applies tier limits, and surfaces data for Stripe Meter. This slot wires the primitives without a real Stripe account; tests use Stripe's test secret key when available and stub metering otherwise.

### 1.1 Inputs

- `src/knoema/agents/` - where current LLM calls happen.
- `src/knoema/llm_gateway.py` or equivalent - existing abstraction if present; match its contract.
- `docs/api/llm-gateway.md` - existing doc reference for continuity.

### 1.2 Deliverables

1. `src/knoema/billing/__init__.py` + `src/knoema/billing/gateway.py`:
   - `LLMGateway` class wrapping LiteLLM's `completion()` with:
     - `tenant_id`, `api_key_source` ({`byo_key`, `pass_through`, `dedicated`}), `model` arguments.
     - `byo_key` path: consumer provides their own OpenAI / Anthropic key; Knoema records zero-margin metering (counts only, no billing row).
     - `pass_through` path: Knoema's master key is used; per-call token counts recorded with configurable markup (default 30%).
     - `dedicated` path: customer-assigned model endpoint; flat per-tenant billing row; token counts still recorded for analytics.
     - Deterministic logging of every call's prompt hash (SHA256), completion hash, token counts, latency, and cost basis.
   - `UsageMeter` class:
     - In-memory + JSONL spool (`var/billing/usage_<yyyymmdd>.jsonl`).
     - `record(tenant_id, model, input_tokens, output_tokens, cost_usd, tier)` method.
     - `flush_to_stripe(stripe_secret_key)` method that batches records to Stripe Meter API; no-op (graceful skip) when `STRIPE_TEST_SECRET_KEY` is unset.

2. `src/knoema/billing/tiers.py`:
   - `TIER_LIMITS` constant: dict keyed by tier name with monthly token cap, concurrent-request cap, and allowed models list.
     - `free`: BYO-key only, no Knoema-side metered cost, 1 concurrent request.
     - `pro`: 2M output tokens/month, 4 concurrent requests, pass-through with markup.
     - `team`: 10M output tokens/month, 16 concurrent requests, pass-through + workspace sharing.
     - `enterprise`: configurable per contract, dedicated instance.

3. `src/knoema/billing/markup.py`:
   - `compute_markup_price(base_cost_usd, tier) -> Decimal`: returns billed price with the tier's markup (30% for pro/team, 0% for free, 0% for enterprise which uses flat contract).
   - Use `decimal.Decimal` for all currency math; never float.

4. `src/knoema/billing/stripe_adapter.py`:
   - Thin wrapper around the `stripe` Python package.
   - `submit_usage_record(subscription_item_id, quantity, timestamp)` method.
   - Graceful no-op when `STRIPE_TEST_SECRET_KEY` is unset; prints a message and returns a mock record ID.

5. `tests/test_billing_gateway.py`:
   - Asserts BYO-key path produces zero Knoema-side cost entries.
   - Asserts pass-through path applies 30% markup correctly (using `Decimal` equality).
   - Asserts enterprise path records analytics but emits zero variable cost.
   - Asserts deterministic prompt-hash logging across repeated calls.
   - Uses a mock LiteLLM client; no network.

6. `tests/test_billing_tiers.py`:
   - Validates tier limits shape and type.
   - Asserts quota-enforcement logic: when a tenant exceeds its monthly cap, the gateway returns a tier-exceeded error without calling the upstream model.

7. `tests/integration/test_stripe_adapter.py` (marked `@pytest.mark.slow`, skipped unless `KNOEMA_ENABLE_STRIPE_TEST=1`):
   - Uses Stripe test mode only.
   - Verifies submit-usage-record round-trip against a Stripe test subscription item.

8. `docs/billing.md`:
   - Tier table (Free / Pro / Team / Enterprise) with monthly caps and pricing architecture.
   - Markup policy explanation.
   - Stripe Meter integration flow diagram (ASCII or mermaid).
   - How customers' existing BYO keys are kept secret (never persisted, passed through per-call).
   - How Knoema's master keys are kept secret (env var only, never in repo).

9. `src/knoema/billing/webhooks.py` - outbound webhook dispatcher:
   - `WebhookDispatcher(secret, endpoint_url, events)` class.
   - Customer-configurable webhook URL per tenant for events: `usage.recorded`, `tier.exceeded`, `subscription.updated`.
   - HMAC-SHA256 signature on every payload using `X-Knoema-Signature` header.
   - Retry with exponential backoff: 1s, 4s, 16s, 64s; give up after 4 attempts.
   - Timeout: 5 seconds per attempt.
   - Never blocks the upstream LLM call path (async queue).

10. `src/knoema/billing/api_keys.py` - tenant API key management primitives:
    - `issue(tenant_id, scope) -> (key_id, raw_secret)` - returns a display-once raw secret; stores only the SHA256 hash in the persistence layer stub.
    - `verify(raw_secret) -> tenant_id | None` - constant-time comparison against stored hashes.
    - `revoke(key_id)` - soft delete with revoked_at timestamp.
    - `rotate(key_id) -> (new_key_id, new_raw_secret)` - atomic: old key remains valid for 24 hours during rotation.
    - In-memory persistence stub for now; interface must be pluggable for Postgres later.

11. `tests/test_billing_webhooks.py` + `tests/test_billing_api_keys.py`:
    - Webhook: HMAC signature round-trip, retry behavior with mocked HTTP.
    - API keys: issue/verify/revoke/rotate, constant-time comparison verified.
    - No network, no real persistence.

12. `docs/billing.md`:
    - Tier table (Free / Pro / Team / Enterprise) with monthly caps and pricing architecture.
    - Markup policy explanation.
    - Stripe Meter integration flow diagram (ASCII or mermaid).
    - How customers' existing BYO keys are kept secret (never persisted, passed through per-call).
    - How Knoema's master keys are kept secret (env var only, never in repo).
    - Webhook events catalog with example payloads.
    - API key lifecycle (issue, rotate, revoke).

13. `mkdocs.yml`:
    - Add `Billing and Metering: billing.md` to the Reference nav section, between `Didimdol One-Pager` and `Privacy`.

### 1.3 Acceptance Criteria

- All new billing tests pass offline (no Stripe account required).
- `decimal.Decimal` used everywhere currency is computed; no `float` arithmetic in billing code.
- BYO-key path records zero Knoema-side cost.
- Pass-through path applies exactly 30% markup (verified via `Decimal` equality, not approximate).
- Tier-exceeded response does NOT call the upstream LLM.
- No API key or secret present in any committed file (automated grep-based check in the test suite).
- Raw API key secret is returned exactly once at `issue()` time; all subsequent reads are hash-only.
- Webhook HMAC signature verifies correctly against a known fixture vector.
- `mkdocs build --strict` passes with the new doc registered.
- Forbidden-entity scan on the diff: 0 matches.
- Existing replay SHA256 values unchanged per §0.6.

### 1.4 Git

Commit message: `feat(billing): add tiered llm gateway, webhooks, and api key management`
Paths: `src/knoema/billing/`, `tests/test_billing_gateway.py`, `tests/test_billing_tiers.py`, `tests/test_billing_webhooks.py`, `tests/test_billing_api_keys.py`, `tests/integration/test_stripe_adapter.py`, `docs/billing.md`, `mkdocs.yml`, `CHANGELOG.md`.

---

## 2. Slot B - Commercial Legal Documents (ToS + Privacy + DPA)

Effort estimate: 3-5 hours.
Rationale: Commercial sales require signed terms. This slot ships drafts in Korean and English for three documents (Terms of Service, Privacy Policy, Data Processing Agreement template). Drafts are Codex-generated first drafts explicitly marked "DRAFT - LEGAL REVIEW PENDING" and are not intended for public posting without user / counsel review.

Prerequisite: v4 Slot B (Nemotron integration) must be merged so attribution references are stable.

### 2.1 Inputs

- `docs/persona_seeding.md` - Nemotron license and citation block (from v4 Slot B).
- `demo/replay/profiles/personality_cat28/CITATION.md` - CAT-28 academic sources.
- `LICENSE-NEMOTRON.md` - Nemotron license verbatim (from v4 Slot B).
- `docs/safety/content_filter_policy.md`, `docs/safety/red_team_report.md` - existing safety framings to reference.

### 2.2 Deliverables

1. `legal/commercial_terms_v1_ko.md` (한국어):
   - 서비스 정의, 이용 자격, 계정 관리, 결제·환불, 라이선스 부여 범위, 사용 제한, 지적재산권, 기밀유지, 면책·제한책임, 해지, 준거법 (대한민국 법률, Celovin 관할), 분쟁해결.
   - 사용 제한 필수 조항:
     - 실제 특정 개인을 identifiable하게 프로파일링하는 용도 금지.
     - 법집행 기관의 operational profiling 용도 금지 (academic / pedagogical 협업은 개별 계약으로만).
     - 군사·무기·대량살상 용도 금지.
     - Tier 3 및 Tier 4 범죄학 archetype 생성 금지 (재명시).
     - Nemotron 원본 데이터셋을 직접 재배포하여 Knoema 경쟁 제품을 만드는 용도 금지 (derivative 사용은 CC BY 4.0 범위 내 허용).
   - 면책 조항: 최대 배상 = 최근 12개월 지불액.
   - 헤더 상단에 `> STATUS: DRAFT - LEGAL REVIEW PENDING (do not publish)` 명시.

2. `legal/commercial_terms_v1_en.md`:
   - English mirror of the Korean ToS.
   - Identical usage restrictions, identical liability cap.
   - Same draft-status header.

3. `legal/privacy_policy_v1_ko.md`:
   - 개인정보보호법(PIPA) 기준.
   - 수집 항목: 계정 이메일, 결제 메타데이터 (Toss·Paddle 경유), 사용량 로그 (tenant_id + 토큰 카운트; 프롬프트 내용은 서버에 저장하지 않음).
   - 보유기간·파기절차·제3자 제공·국외이전 항목.
   - 만 14세 미만 서비스 불가.
   - 권리 행사 절차 (열람·정정·삭제·처리정지).
   - Draft 상태 헤더.

4. `legal/privacy_policy_v1_en.md`:
   - GDPR + CCPA baseline.
   - Same data minimization principles.
   - Data Subject Rights section (GDPR) + California Privacy Rights section (CCPA).
   - Draft status header.

5. `legal/dpa_template.md` (English, B2B template):
   - Controller/Processor relationship for enterprise customers.
   - Sub-processor list (Toss, Paddle, Stripe, HuggingFace, AWS / equivalent infra).
   - Security measures summary.
   - Breach notification timelines.
   - Draft status header.

6. `legal/attribution.md`:
   - Central attribution manifest consolidating Nemotron (NVIDIA, NAVER Cloud, KOSIS, Supreme Court, NHIS, KREI), CAT-28 academic sources, criminology archetype literature, Gradio, Plotly, HuggingFace Hub, LiteLLM, Stripe SDK.
   - Each entry: name, URL / DOI / ISBN, license, attribution text.
   - Must be consistent with `LICENSE-NEMOTRON.md` and `CITATION.md` files.

7. `legal/sla_template_v1_en.md` (Enterprise tier SLA template):
   - Uptime commitment: 99.5% monthly for Enterprise, 99.0% for Team, best-effort for Pro/Free.
   - Support response time: Enterprise 4 business hours, Team 1 business day, Pro 3 business days.
   - Service credits: 10% credit at 99.0-99.5% uptime, 25% at 98.0-99.0%, 50% below 98.0%.
   - Scheduled maintenance exclusions and notification windows.
   - Force-majeure clauses.
   - Draft status header.

8. `legal/security_posture_v1_en.md` (Customer-facing security whitepaper, 3-5 pages):
   - Data classification (customer prompts, usage logs, synthetic data outputs).
   - Encryption in transit (TLS 1.3) and at rest (AES-256).
   - Access control (principle of least privilege, 2FA for Celovin internal access).
   - Secret management (environment variables, never committed, rotation cadence).
   - Incident response workflow with breach notification target of 72 hours per GDPR.
   - Third-party sub-processors list (HuggingFace Hub, OpenAI, Stripe, Toss, Paddle).
   - Note: NOT a SOC 2 report; explicit disclaimer that external audit is pending.
   - Draft status header.

9. `legal/refund_cancellation_policy_v1_ko.md` + `legal/refund_cancellation_policy_v1_en.md`:
   - 환불 정책: 결제 후 7일 이내 미사용 시 전액 환불; 사용 후 비례 환불 없음.
   - 월 구독 해지는 언제든 가능, 당월 말까지 서비스 유지.
   - 연 구독은 결제 후 30일 이내만 환불; 이후는 남은 월수 비례 공제 후 잔액 환불 불가.
   - 디지털 재화 특례 (전자상거래법 제17조) 명시.
   - Paddle/Toss 환불 처리 흐름 도식 (간단 flow).
   - Draft status header, 한·영 mirror.

10. `tests/test_legal_attribution_consistency.py`:
    - Parses `legal/attribution.md`.
    - Asserts every identifier (DOI / ISBN / ISSN) listed in `demo/replay/profiles/personality_cat28/CITATION.md` also appears in `legal/attribution.md`.
    - Asserts Nemotron attribution block matches the license text in `LICENSE-NEMOTRON.md`.

11. `docs/legal.md`:
    - User-facing landing page pointing to each of the 9 legal files.
    - Prominent banner: these are drafts; review with counsel before publishing.

12. `mkdocs.yml`:
    - Add a new top-level `Legal (Drafts)` section with entries for the 9 legal files + `docs/legal.md`.

### 2.3 Acceptance Criteria

- All 9 legal documents exist and carry the `STATUS: DRAFT - LEGAL REVIEW PENDING` header.
- Attribution consistency test passes.
- `mkdocs build --strict` passes with the new Legal section.
- No placeholder like `TBD`, `XXX`, or `<insert>` appears in the body of any legal file; any unresolved item must be a clearly-marked TODO comment in an HTML comment (`<!-- TODO: ... -->`) inside the markdown source.
- Forbidden-entity scan: 0 matches.
- Korean drafts use accurate Korean legal terminology (PIPA: 개인정보처리방침, not 개인정보보호정책).
- English drafts use US-English legal register consistent with GDPR / CCPA convention.

### 2.4 Git

Commit message: `docs(legal): add draft commercial terms, privacy, dpa, and attribution`
Paths: `legal/`, `docs/legal.md`, `tests/test_legal_attribution_consistency.py`, `mkdocs.yml`, `CHANGELOG.md`.

---

## 3. Slot C - Attribution Consolidation

Effort estimate: 1-2 hours.
Rationale: After v4 Slot B (Nemotron) and v5 Slot B (legal docs), attribution data lives in multiple files (`LICENSE-NEMOTRON.md`, `CITATION.md`, `legal/attribution.md`, each profile yaml's `literature_sources`). This slot adds a single runtime `ATTRIBUTIONS.md` at repo root that concatenates every attribution surface for easy packaging into distributed artifacts.

### 3.1 Deliverables

1. `scripts/build_attributions.py`:
   - Reads `LICENSE-NEMOTRON.md`, `demo/replay/profiles/personality_cat28/CITATION.md`, `legal/attribution.md`, `demo/replay/profiles/_research/*_research.md` Citation Appendix sections, and every archetype yaml's `literature_sources`.
   - Emits `ATTRIBUTIONS.md` at repo root with sections: Nemotron / CAT-28 / Criminology Research / Third-Party Libraries / Patent & Trademark Notices.
   - Deterministic output (sorted keys, stable ordering).
   - Regenerable; exits non-zero if any attribution source has changed since the last committed `ATTRIBUTIONS.md` without the script being rerun.

2. `ATTRIBUTIONS.md` (committed artifact):
   - Generated by the script above.
   - Single source of truth for end-users who need to comply with downstream attribution obligations.

3. `.github/workflows/attribution_drift.yml`:
   - CI action that runs `scripts/build_attributions.py --check` on every push.
   - Fails CI if the committed `ATTRIBUTIONS.md` drifts from what the script would generate.

4. `tests/test_attribution_build.py`:
   - Asserts `scripts/build_attributions.py` produces byte-identical output on repeat runs.
   - Asserts the generated `ATTRIBUTIONS.md` contains NVIDIA, CC-BY-4.0, KOSIS, CAT-28 authors, and the Whitechapel / Holmes / Gunness research citations.

5. `docs/legal.md` - add a link to `ATTRIBUTIONS.md` at the top.

6. `scripts/build_sbom.py` - SBOM (Software Bill of Materials) generator:
   - Emits `sbom.cdx.json` at repo root in CycloneDX 1.5 JSON format.
   - Reads `pyproject.toml`, `poetry.lock` or `requirements*.txt`, and Node lockfiles if present.
   - Each component entry: name, version, purl (package URL), license SPDX identifier, supplier.
   - Deterministic output (sorted by component name).
   - Must NOT require network access (reads locally installed metadata via `importlib.metadata`).

7. `sbom.cdx.json` - committed artifact, regenerable via the script.

8. `.github/workflows/sbom_drift.yml`:
   - CI action that runs `python scripts/build_sbom.py --check` on every push.
   - Fails CI if the committed `sbom.cdx.json` drifts from what the script would generate.

9. `tests/test_sbom_build.py`:
   - Asserts the emitted SBOM is valid CycloneDX 1.5 JSON against a schema check.
   - Asserts that every dependency listed in `pyproject.toml` appears in the SBOM.
   - Asserts no PII leaks (e.g., author emails are scrubbed if the format exposes them).

### 3.2 Acceptance Criteria

- `python scripts/build_attributions.py` produces `ATTRIBUTIONS.md` byte-identical to the committed version.
- `python scripts/build_attributions.py --check` exits 0 on the clean tree.
- Deliberately corrupting any attribution source file and rerunning `--check` produces a non-zero exit (regression-detected).
- `python scripts/build_sbom.py` produces `sbom.cdx.json` that validates against the CycloneDX 1.5 JSON schema.
- Every runtime dependency in `pyproject.toml` has a corresponding SBOM entry with a non-empty license field.
- GitHub Actions (attribution_drift.yml and sbom_drift.yml) pass on the commit introducing them.
- Forbidden-entity scan: 0 matches.

### 3.3 Git

Commit message: `feat(legal): consolidate attributions and generate SBOM`
Paths: `scripts/build_attributions.py`, `scripts/build_sbom.py`, `ATTRIBUTIONS.md`, `sbom.cdx.json`, `.github/workflows/attribution_drift.yml`, `.github/workflows/sbom_drift.yml`, `tests/test_attribution_build.py`, `tests/test_sbom_build.py`, `docs/legal.md`, `CHANGELOG.md`.

---

## 4. Slot D - Payment Seller Onboarding Reference

Effort estimate: 1-2 hours.
Rationale: User has chosen Toss Payments (KR) and Paddle (global) but has not yet registered as a seller on either platform. This slot ships documentation only: a checklist, field-by-field guidance, and a validation script that Codex can run to confirm the user has supplied the needed environment variables before attempting any real payment integration. No live seller registration is performed by Codex; that remains a user action per §0.7.

### 4.1 Deliverables

1. `docs/payments/toss-onboarding-ko.md`:
   - Step-by-step Toss Payments 가맹점 신청 절차 for Celovin 개인사업자.
   - Required documents: 사업자등록증, 대표자 신분증, 계좌사본, 홈페이지 URL, 약관·개인정보처리방침 게시 확인.
   - Toss Payments API key pair structure (`TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY`), environment variable naming convention.
   - Common 반려 사유 checklist.

2. `docs/payments/paddle-onboarding-en.md`:
   - Paddle seller onboarding for Celovin as a Korean sole proprietor (or fallback to a Celovin-owned US entity if Paddle's KR support is insufficient).
   - Must cite Paddle's public documentation URLs verifying whether Korean sole proprietors are accepted sellers. If the answer is unclear, document the uncertainty and list the concrete question to ask Paddle support.
   - Verification Option (VO) listing:
     - VO-1: Celovin as KR sole proprietor (preferred).
     - VO-2: Celovin establishes a US LLC via Stripe Atlas and uses that entity for Paddle (fallback).
     - VO-3: Use Wise Business + direct invoicing (no Paddle).
   - Required seller documents (business registration, government ID of beneficial owner, bank account proof).
   - Paddle API key structure (`PADDLE_API_KEY`, `PADDLE_WEBHOOK_SECRET`), environment variable naming convention.

3. `scripts/check_payment_env.py`:
   - Reads `.env.local` via `dotenv` (never prints values).
   - Prints a status table: which of `TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY`, `PADDLE_API_KEY`, `PADDLE_WEBHOOK_SECRET`, `STRIPE_TEST_SECRET_KEY` are set vs unset.
   - Exits 0 always (this is a diagnostic tool, not a gate).

4. `docs/payments/index.md`:
   - Landing page linking to Toss and Paddle onboarding docs + the environment-check script usage.

5. `mkdocs.yml`:
   - Add a `Payments (Onboarding)` section with three entries: `docs/payments/index.md`, `docs/payments/toss-onboarding-ko.md`, `docs/payments/paddle-onboarding-en.md`.

### 4.2 Acceptance Criteria

- All three payment documents exist and pass mkdocs strict build.
- `scripts/check_payment_env.py` runs without printing any secret values (even partially).
- Forbidden-entity scan: 0 matches.
- Paddle onboarding doc explicitly states the current uncertainty about KR sole proprietor support and names the open question.

### 4.3 Git

Commit message: `docs(payments): add toss and paddle seller onboarding references`
Paths: `docs/payments/`, `scripts/check_payment_env.py`, `mkdocs.yml`, `CHANGELOG.md`.

---

## 5. Slot E - Public Pricing Page

Effort estimate: 2-3 hours.
Rationale: Commercial conversations need a published pricing page. Tier comparison, CTA blocks, and checkout placeholder URLs produce a first surface prospects can point at. Ships as a static mkdocs page plus a minimal HTML/CSS variant for future embedding on a marketing site.

### 5.1 Deliverables

1. `docs/pricing.md` - mkdocs pricing page:
   - Tier comparison table: Free / Pro ($49/mo) / Team ($199/mo) / Enterprise (contact us).
   - Per-tier columns: monthly token cap, concurrent requests, support tier, SLA target, LLM cost model (BYO-key vs metered pass-through 30% markup vs dedicated).
   - CTA blocks under each tier: Free = "Start with your own OpenAI key", Pro = "Subscribe with card (Toss KR / Paddle global)", Team = "Subscribe with card", Enterprise = "Contact sales@celovin.com".
   - Checkout URL placeholders: `https://checkout.paddle.com/<product-id-placeholder>` and Toss equivalents, clearly marked as placeholders until seller accounts are live.
   - Pricing footnote: amounts are pre-tax (VAT added per jurisdiction); Paddle handles global tax, Toss handles KR tax.
   - Cross-links to `docs/billing.md` (architecture), `legal/commercial_terms_v1_en.md` (ToS), `docs/legal.md` (drafts banner).

2. `site-snapshot/pricing.html` - self-contained HTML/CSS mirror:
   - No external fonts, no external CSS.
   - Uses the same accent palette as `site-snapshot/` convention if one already exists; otherwise neutral grayscale plus one accent color.
   - Mobile-responsive via flex/grid CSS.
   - File size ≤30 KB.
   - Purpose: drop-in embedding on a future marketing microsite without mkdocs runtime.

3. `tests/test_pricing_page_parity.py`:
   - Parses `docs/pricing.md` and `site-snapshot/pricing.html`.
   - Asserts identical tier names, token caps, prices between the two.
   - Asserts no forbidden-entity strings.

4. `mkdocs.yml`:
   - Add `Pricing: pricing.md` to the top-level nav right after `Home` and before `Knoema Bench`.

### 5.2 Acceptance Criteria

- `docs/pricing.md` renders correctly under `mkdocs build --strict`.
- `site-snapshot/pricing.html` opens via `file://` in Chrome/Firefox/Safari and displays the tier table correctly.
- Tier parity test passes.
- No hardcoded secret, API key, or merchant ID in either page.
- Forbidden-entity scan: 0 matches.

### 5.3 Git

Commit message: `feat(marketing): add public pricing page (mkdocs + static HTML mirror)`
Paths: `docs/pricing.md`, `site-snapshot/pricing.html`, `tests/test_pricing_page_parity.py`, `mkdocs.yml`, `CHANGELOG.md`.

---

## 6. Slot F - Public Status Page (Static)

Effort estimate: 1-2 hours.
Rationale: Commercial prospects and paying customers expect a status page. A minimal static HTML status page auto-generated from HF Space runtime state and GitHub CI results is enough for launch and upgradeable later to a hosted solution (Statuspage.io) without rewriting.

### 6.1 Deliverables

1. `scripts/fetch_status.py`:
   - Queries HF Space runtime stage via `HfApi().space_info('celovin/knoema-playground').runtime.stage`.
   - Queries the last 10 GitHub Actions workflow runs on `main` via `gh api` (uses `GITHUB_TOKEN` if set, falls back to unauthenticated for public read).
   - Emits a JSON artifact `site-snapshot/status.json` with: current Space stage, last deploy time, last 10 CI run statuses, last updated timestamp.
   - Deterministic output ordering.

2. `scripts/build_status_page.py`:
   - Consumes `site-snapshot/status.json`.
   - Emits `site-snapshot/status.html` with:
     - Three-component overview: HF Space / CI / Replay artifacts.
     - Each component: green/amber/red badge.
     - 30-day historical bar (from committed `site-snapshot/status-history.jsonl` appended on each build).
   - Self-contained HTML/CSS, ≤25 KB.
   - Prominent "Last updated" timestamp.

3. `.github/workflows/status_page.yml`:
   - Runs every 15 minutes on schedule plus on every push to main.
   - Executes the two scripts above, appends to `site-snapshot/status-history.jsonl`, commits the updated `status.json`, `status.html`, and history file back to main.
   - Uses a bot-style commit message: `chore(status): update status page`.

4. `tests/test_status_page.py`:
   - Mocks `HfApi` and `gh api` responses.
   - Asserts the built HTML contains all three component badges.
   - Asserts the JSON matches the expected schema.

5. `docs/status.md`:
   - Mkdocs-embedded mirror pointing to `site-snapshot/status.html` as canonical and explaining the auto-update cadence.

### 6.2 Acceptance Criteria

- `python scripts/fetch_status.py` and `python scripts/build_status_page.py` run end-to-end with mocked APIs in tests.
- `site-snapshot/status.html` renders in Chrome/Firefox/Safari via `file://`.
- The committed JSON schema validates cleanly.
- GitHub Actions workflow passes on the commit introducing it.
- `mkdocs build --strict` passes with `docs/status.md` registered.
- Forbidden-entity scan: 0 matches.

### 6.3 Git

Commit message: `feat(status): add static status page with auto-update workflow`
Paths: `scripts/fetch_status.py`, `scripts/build_status_page.py`, `site-snapshot/status.html`, `site-snapshot/status.json`, `site-snapshot/status-history.jsonl`, `.github/workflows/status_page.yml`, `tests/test_status_page.py`, `docs/status.md`, `mkdocs.yml`, `CHANGELOG.md`.

---

## 7. Global Completion Report

After Slot F passes, create `planning/NIGHT_REPORT_knoema_sequential_v5_2026-04-22.md`:

```markdown
## Handoff v5 - Completion (YYYY-MM-DD)

### Slot A: Billing gateway, webhooks, and API keys
- Commit: <sha>
- Tiers wired: Free / Pro / Team / Enterprise
- Markup verified: Decimal equality, 30% on pro/team
- Tier-exceeded: blocks upstream call
- Webhook HMAC round-trip verified
- API key issue / verify / rotate / revoke tested

### Slot B: Commercial legal drafts (9 docs)
- Commit: <sha>
- Documents: ToS (ko/en), Privacy (ko/en), DPA (en), attribution.md, SLA (en), Security posture (en), Refund policy (ko/en)
- Draft status: all nine marked "LEGAL REVIEW PENDING"

### Slot C: Attribution consolidation and SBOM
- Commit: <sha>
- ATTRIBUTIONS.md: regenerable, CI drift check wired
- sbom.cdx.json: CycloneDX 1.5 valid, drift check wired

### Slot D: Payment onboarding docs
- Commit: <sha>
- Toss (ko), Paddle (en), env check script

### Slot E: Public pricing page
- Commit: <sha>
- mkdocs page + static HTML mirror, tier parity verified

### Slot F: Static status page with auto-update
- Commit: <sha>
- HF Space + CI + replay components wired, 15-minute cron refresh

### Full gates
- pytest final: N passed, M skipped
- Ruff: clean
- Mypy: clean
- Forbidden-entity scan: 0 matches
- Regression baseline SHAs (§0.6): all 4 + Nemotron variant unchanged
- mkdocs build --strict: clean
- New CI workflows: attribution_drift, sbom_drift, status_page all green
```

---

## 8. What This Handoff Does NOT Include

- Rebrand (Knoema -> new name). Deferred to a future v6 handoff pending user name decision.
- Actual Toss or Paddle seller registration.
- Actual Stripe account creation.
- Legal review or publication of the draft documents.
- Regeneration of any existing replay msgpack.
- HF Space upload of any kind.
- Any code that transmits PII outside the repository.
- Any live commercial transaction.
- Interactive pricing calculator (JS-driven). Static table only.
- Hosted third-party status service (Statuspage.io, BetterUptime). Static page only.

---

## 9. Stop Conditions

Halt immediately if:

1. Standard gate fails non-transient.
2. `git push origin main` denied despite permanent credential fix.
3. Any committed file contains a raw API key, PAT, or secret (grep-based scan).
4. Any §0.6 forbidden-regression SHA changes.
5. Forbidden-entity scan returns any match.
6. `.env.local` missing when a slot explicitly requires env vars (note: v5 slots must degrade gracefully when optional env vars are unset).
7. v4 prerequisite not met when starting Slot B (Nemotron integration must be merged).
8. Any legal document contains a "TBD" / "XXX" / "<insert>" literal in its body (comments are OK).
9. SBOM fails CycloneDX 1.5 schema validation.
10. Pricing or status page file size exceeds the specified ≤30 KB / ≤25 KB bounds.
11. Any slot's effort estimate exceeded by more than 2x.

On halt: write reason, current slot (A/B/C/D/E/F), reproduction command, last-good SHA, and any partially-completed artifact paths to `planning/codex_blockers.md` and return to the user.
