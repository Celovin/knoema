# Status

The public status snapshot is generated from Hugging Face Space runtime state, the latest GitHub Actions runs on `main`, and replay artifact SHA256 checks.

- Static page: `site-snapshot/status.html`
- Machine-readable status: `site-snapshot/status.json`
- Rolling history: `site-snapshot/status-history.jsonl`

The automation runs every 15 minutes and on pushes to `main`. It appends one history row per build, renders a 30-day status bar, and commits updated status artifacts back to `main` with `chore(status): update status page`.

Rolling uptime is computed from the same 15-minute samples for 7-day, 30-day, and 90-day windows. A component sample is counted as up when the recorded status is `RUNNING`, `success`, or `verified`; sparse histories under 7 days are labeled insufficient data. SLA badge thresholds mirror the public status page: green at 99.9% or higher, amber from 99.5% to below 99.9%, and red below 99.5%. Contract language remains governed by the [SLA template](legal/sla_template_v1_en.md).

Run the same build locally:

```powershell
.venv\Scripts\python.exe scripts\fetch_status.py
.venv\Scripts\python.exe scripts\build_status_page.py
.venv\Scripts\python.exe scripts\compute_uptime.py
.venv\Scripts\python.exe scripts\build_status_page.py --no-append
```

The status page is informational. Billing, legal drafts, and service-level language remain controlled by [docs/pricing.md](pricing.md), [docs/billing.md](billing.md), and [docs/legal.md](legal.md).
