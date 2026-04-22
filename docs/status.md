# Status

The public status snapshot is generated from Hugging Face Space runtime state, the latest GitHub Actions runs on `main`, and replay artifact SHA256 checks.

- Static page: `site-snapshot/status.html`
- Machine-readable status: `site-snapshot/status.json`
- Rolling history: `site-snapshot/status-history.jsonl`

The automation runs every 15 minutes and on pushes to `main`. It appends one history row per build, renders a 30-day status bar, and commits updated status artifacts back to `main` with `chore(status): update status page`.

Run the same build locally:

```powershell
.venv\Scripts\python.exe scripts\fetch_status.py
.venv\Scripts\python.exe scripts\build_status_page.py
```

The status page is informational. Billing, legal drafts, and service-level language remain controlled by [docs/pricing.md](pricing.md), [docs/billing.md](billing.md), and [docs/legal.md](legal.md).
