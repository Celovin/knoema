
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

## Sequential v5 Slot A - Billing Gateway, Webhooks, and API Keys (2026-04-22)

- Commit: 387963506baf7c57e4b805efd893bc428e48a19e
- Scope: added the commercial billing package with tier limits, Decimal-based markup, a LiteLLM-backed gateway, JSONL usage spool, Stripe usage adapter, signed webhook dispatcher, and hash-only tenant API key management.
- Acceptance proof: BYO-key calls record zero Knoema-side variable cost; Pro pass-through applies exact Decimal 30% markup; Enterprise records analytics with zero variable cost; tier-exceeded checks block the upstream mock client; webhook HMAC fixture and retry behavior passed; API key issue / verify / rotate / revoke passed with constant-time comparison coverage.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; staged diff forbidden-entity scan returned 0 matches; `mkdocs build --strict` passed.
- Gate results: pytest 643 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; `git push origin main` succeeded.

## Sequential v5 Slot B - Commercial Legal Drafts (2026-04-22)

- Commit: f07cf6844c067c0653e2b01945e37699a6c20385
- Scope: added draft commercial terms, privacy policies, DPA template, attribution manifest, SLA template, security posture, refund and cancellation policies, rendered MkDocs copies, and attribution consistency tests.
- Acceptance proof: all 10 legal files carry `STATUS: DRAFT - LEGAL REVIEW PENDING`; placeholder scan for `TBD`, `XXX`, and `<insert>` returned 0 matches; Korean privacy draft uses `개인정보처리방침`; CAT-28 DOI/ISBN/ISSN coverage and Nemotron license fragments are asserted by tests.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; staged diff forbidden-entity scan returned 0 matches; `mkdocs build --strict` passed.
- Gate results: pytest 645 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; `git push origin main` succeeded.

## Sequential v5 Slot C - Attribution Consolidation and SBOM (2026-04-22)

- Commit: 9d0643800cfb2dfe5363de8c868d8ba5a60d88b3
- Scope: added deterministic attribution and CycloneDX 1.5 SBOM builders, committed `ATTRIBUTIONS.md` and `sbom.cdx.json`, wired GitHub Actions drift checks, and added artifact repeatability tests.
- Acceptance proof: `python scripts/build_attributions.py --check` and `python scripts/build_sbom.py --check` exited 0; attribution corruption probe failed as expected; SBOM covers all runtime dependencies from `pyproject.toml` with non-empty license and supplier fields and no author email leakage.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; staged diff forbidden-entity scan returned 0 matches; `mkdocs build --strict` passed.
- Gate results: pytest 650 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; `git push origin main` succeeded.

## Sequential v5 Slot D - Payment Seller Onboarding References (2026-04-22)

- Commit: 6eeb925bd4c92ac1bab5472bf1db9117b171d328
- Scope: added Toss Payments Korean onboarding notes, Paddle English onboarding notes, a payment onboarding index, MkDocs navigation, and a secret-safe payment environment checker.
- Acceptance proof: all three payment onboarding docs exist; Paddle onboarding explicitly records the open Korean sole proprietor support question; `python scripts/check_payment_env.py` printed only set/unset status and no key values.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; staged diff forbidden-entity and raw-secret scans returned 0 matches; `python -m mkdocs build --strict` passed.
- Gate results: pytest 650 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; `git push origin main` succeeded.

## Sequential v5 Slot E - Public Pricing Page (2026-04-22)

- Commit: 465a3f1701851cde5eb3acb5cc6f4c54a22fd5aa
- Scope: added `docs/pricing.md`, a self-contained responsive `site-snapshot/pricing.html`, MkDocs Pricing nav placement, changelog entry, and Markdown/HTML parity tests.
- Acceptance proof: Free / Pro / Team / Enterprise pricing, token caps, concurrency, support, SLA target, LLM cost model, tax notes, provider role notes, legal links, and placeholder Paddle/Toss checkout templates are present; static HTML size is 8,489 bytes and has no external CSS/font/script dependency.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; staged diff forbidden-entity and raw-secret scans returned 0 matches; `python -m mkdocs build --strict` passed.
- Gate results: pytest 653 passed, 4 skipped, 5 warnings; ruff clean after import sorting; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; `git push origin main` succeeded.

## Sequential v5 Slot F - Static Status Page and 15-minute Cron (2026-04-22)

- Commit: 5d674639064f0a10c0556342f6b1879979a3e7a6
- Scope: added status fetching, status page generation, initial `site-snapshot/status.json`, `site-snapshot/status.html`, `site-snapshot/status-history.jsonl`, MkDocs status docs, tests, and a 15-minute GitHub Actions updater.
- Acceptance proof: live snapshot recorded HF Space stage `RUNNING`, latest deploy workflow time `2026-04-21T23:06:17Z`, last 10 main-branch Actions run statuses, and replay artifact verification; HTML includes HF Space, CI, replay artifact badges, Last updated timestamp, and a 30-day history bar; status HTML size is 5,151 bytes.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; staged diff forbidden-entity and raw-secret scans returned 0 matches; `python -m mkdocs build --strict` passed.
- Gate results: pytest 655 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed; `git push origin main` succeeded.

## Sequential v6 Slot A - API Server Commercial Gating (2026-04-22)

- Commit message: `feat(api): wire billing into api server with tier-based auth and rate limit`.
- Scope: replaced the legacy write-surface guard with tenant API-key authentication, added tier-aware token buckets, connected the API app to the billing key manager and usage meter, added request usage spooling for authenticated simulation runs, kept public read and anonymous stream access available, and expanded billing API keys to carry tier and credential-source metadata.
- Acceptance proof: missing tenant bearer token returns 401 with `WWW-Authenticate: Bearer`; valid Pro simulation run returns `X-Knoema-Tenant-Tier: pro`; Free access to `gpt-4o` returns 402 with an upgrade message; Pro tier rate limiting returns 429 with `Retry-After`, `X-Knoema-RateLimit-Tier`, and `X-Knoema-RateLimit-Remaining`; one authenticated run writes exactly one `UsageRecord` JSONL row; revoked keys return 401; invalid token checks still exercise constant-time comparison.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; protected v5 artifacts were not modified by the Slot A patch; Slot A diff scans returned 0 forbidden-entity matches and 0 raw-secret matches.
- Gate results: pytest 662 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed. MkDocs strict was not run for Slot A because no docs navigation or Markdown page changed.

## Sequential v6 Slot B - Commercial Audit Coverage (2026-04-22)

- Commit message: `feat(audit): cover commercial key and webhook events in audit log`.
- Scope: added a commercial JSONL audit log with the 8 required `commercial.*` event types, a 90-day purge helper, a read-only tenant filter CLI, audit hooks for API key issue / rotate / revoke, webhook dispatch / failure / exhaustion, and LLM gateway tier-limit / cap-exhaustion paths. Added the public audit-log page and privacy-policy pointers.
- Acceptance proof: the registry exactly matches the 8 required event types; API key lifecycle tests log key IDs and tiers without plaintext secrets; webhook tests log hashed endpoint URLs only; gateway tests produce tier-limit and cap-exhaustion records; `audit_log_show.py` filters by tenant and `--since`; purge removes records older than the configured window.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; Slot B diff scans returned 0 forbidden-entity matches and 0 raw-secret matches; no protected v5 artifact was modified.
- Gate results: pytest 668 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; `python -m mkdocs build --strict` passed; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed.

## Sequential v6 Slot C - Customer Onboarding CLI (2026-04-22)

- Commit: 195cb2c6a739a450e2643095478653f1e59f75b2
- Commit message: `feat(cli): add customer onboarding commands (create/issue/rotate/revoke/show-usage)`.
- Scope: added file-backed tenant onboarding through `knoema customer create`, `issue-key`, `rotate-key`, `revoke-key`, `show-usage`, and `list`; moved tenant registry persistence into billing so the API server can load CLI-issued keys; documented the 7-step Pro tenant curl quickstart and linked it from Pricing.
- Acceptance proof: CLI lifecycle test covers create -> API `/simulations/run` with CLI-issued Pro key -> issue-key -> gateway usage -> show-usage -> rotate-key -> revoke-key -> list. The raw bearer token appears exactly once in stdout and never in `tenants.json`, audit JSONL, or list output.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; Slot C diff scans returned 0 forbidden-entity matches and 0 raw-secret matches; no protected v5 artifact was modified.
- Gate results: pytest 670 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; `python -m mkdocs build --strict` passed; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed.

## Sequential v6 Slot D - Public Replay Benchmark Publication (2026-04-22)

- Commit: 8d72ad70789f0908147937bd03197b4e5d8ed120
- Commit message: `feat(benchmarks): publish replay throughput numbers with regression guard`.
- Scope: added `scripts/bench_replay_throughput.py`, committed public JSON and Markdown replay throughput artifacts, added a regression test and weekly/path-filtered GitHub Actions benchmark workflow, and surfaced the benchmark page in MkDocs Reference navigation.
- Acceptance proof: `python scripts/bench_replay_throughput.py --check` passed repeatedly; committed rows cover all five replay artifacts with SHA256, artifact source commit, load time, 20x sequential replay wall time, FPS, RSS delta, and msgpack size. Current committed 10K rows report stub `fps_20x=128.386958` and Nemotron `fps_20x=128.83332`.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; Slot D diff scans returned 0 forbidden-entity matches and 0 raw-secret matches; no protected v5 artifact was modified.
- Gate results: pytest 671 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; `python -m mkdocs build --strict` passed; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed.

## Sequential v6 Slot E - Opt-in Observability (2026-04-22)

- Commit: ef809522a7553aa3139b83e0d0285af3ceb7ca5c
- Commit message: `feat(observability): add opt-in otel tracing and prometheus metrics`.
- Scope: added lazy-loaded observability modules for Prometheus and OpenTelemetry, wired env-gated API setup, request metrics, hashed-tenant billing token metrics, webhook/rate-limit counters, LLM gateway tracing span hooks, optional dependency extra, and observability docs. Also stabilized the Slot D replay benchmark check after full-suite load showed a false-positive performance regression at the 15% boundary.
- Acceptance proof: default `/metrics` returns 404 and a fresh default server import does not load any `opentelemetry*` module; `KNOEMA_METRICS_ENABLED=1` exposes Prometheus text with request and latency families; tenant IDs are hashed in `knoema_billing_tokens_total` and plaintext tenant IDs are absent; `KNOEMA_OTEL_EXPORTER=otlp` with a mocked exporter captures request spans.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; Slot E diff scans returned 0 forbidden-entity matches and 0 raw-secret matches; no protected v5 artifact was modified.
- Gate results: pytest 676 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; `python -m mkdocs build --strict` passed; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed.

## Sequential v6 Slot F - Rolling Uptime Status Page (2026-04-22)

- Commit: 8652a767cfb7e33aabdfdb585c2b5bca487ad516
- Commit message: `feat(status): add rolling 7/30/90-day uptime with sla badges`.
- Scope: added deterministic rolling uptime computation for 7-day, 30-day, and 90-day windows; rendered component-level uptime and 30-day SLA badges on the static status page; made status-history append idempotent; updated the status workflow to append history, compute uptime, and re-render without a second append; documented uptime semantics and SLA thresholds.
- Acceptance proof: 15-minute sample windows count HF Space `RUNNING`, CI `success`, and replay `verified` as up; histories under 7 days render as insufficient data; one 15-minute outage in 30 days computes 99.965%; status HTML includes Rolling uptime, 7d/30d/90d columns, and 30d SLA badge; final `site-snapshot/status.html` is 7,336 bytes after the latest status bot sample.
- Regression proof: 100 / 1K / 5K / 10K replay msgpack SHA256 values and Nemotron 10K SHA256 remained unchanged; Slot F staged diff scans returned 0 forbidden-entity matches and 0 raw-secret matches; no protected v5 artifact was modified.
- Gate results: pytest 680 passed, 4 skipped, 5 warnings; ruff clean; mypy clean; `python -m mkdocs build --strict` passed; encoding guard 3 passed; Gradio compatibility pass; Plotly enum safety 4 passed.
