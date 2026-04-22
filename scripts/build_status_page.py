from __future__ import annotations

import argparse
import html
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_STATUS_PATH = Path("site-snapshot/status.json")
DEFAULT_HISTORY_PATH = Path("site-snapshot/status-history.jsonl")
DEFAULT_OUTPUT_PATH = Path("site-snapshot/status.html")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _ci_state(status: Mapping[str, Any]) -> str:
    runs = status.get("github_actions", {}).get("runs", [])
    if not isinstance(runs, list) or not runs:
        return "unknown"
    latest = runs[0]
    if not isinstance(latest, dict):
        return "unknown"
    run_status = str(latest.get("status") or "unknown")
    if run_status != "completed":
        return run_status
    conclusion = latest.get("conclusion")
    return str(conclusion or "unknown")


def _history_entry(status: Mapping[str, Any]) -> dict[str, Any]:
    replay = status.get("replay_artifacts", {})
    return {
        "timestamp": status["generated_at"],
        "space_stage": status.get("space", {}).get("stage", "UNKNOWN"),
        "ci_state": _ci_state(status),
        "replay_verified": bool(replay.get("verified")),
    }


def append_history(
    status: Mapping[str, Any],
    history_path: Path = DEFAULT_HISTORY_PATH,
) -> list[dict[str, Any]]:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    entry = _history_entry(status)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return load_history(history_path)


def load_history(history_path: Path = DEFAULT_HISTORY_PATH) -> list[dict[str, Any]]:
    if not history_path.exists():
        return []
    history: list[dict[str, Any]] = []
    for line in history_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            history.append(payload)
    return history


def _history_window(
    history: list[dict[str, Any]],
    *,
    now: datetime,
) -> list[dict[str, Any]]:
    cutoff = now - timedelta(days=30)
    filtered = [
        entry
        for entry in history
        if isinstance(entry.get("timestamp"), str)
        and _parse_timestamp(str(entry["timestamp"])) >= cutoff
    ]
    return sorted(filtered, key=lambda entry: str(entry["timestamp"]))


def _badge(label: str, value: str, state: str) -> str:
    safe_label = html.escape(label)
    safe_value = html.escape(value)
    safe_state = html.escape(state.lower())
    return f'<span class="badge {safe_state}"><b>{safe_label}</b>{safe_value}</span>'


def _history_bar(history: list[dict[str, Any]]) -> str:
    if not history:
        return '<p class="muted">No history samples yet.</p>'
    marks = []
    for entry in history[-30:]:
        stage_ok = str(entry.get("space_stage")) == "RUNNING"
        ci_ok = str(entry.get("ci_state")) == "success"
        replay_ok = bool(entry.get("replay_verified"))
        state = "ok" if stage_ok and ci_ok and replay_ok else "warn"
        title = html.escape(
            f"{entry.get('timestamp')}: space={entry.get('space_stage')}, "
            f"ci={entry.get('ci_state')}, replay={replay_ok}"
        )
        marks.append(f'<span class="bar {state}" title="{title}"></span>')
    return "\n".join(marks)


def _run_rows(status: Mapping[str, Any]) -> str:
    runs = status.get("github_actions", {}).get("runs", [])
    if not isinstance(runs, list) or not runs:
        return '<tr><td colspan="5">No GitHub Actions runs were available.</td></tr>'
    rows = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        name = html.escape(str(run.get("name") or "unknown"))
        status_text = html.escape(str(run.get("status") or "unknown"))
        conclusion = html.escape(str(run.get("conclusion") or ""))
        updated = html.escape(str(run.get("updated_at") or ""))
        url = html.escape(str(run.get("html_url") or "#"))
        rows.append(
            "<tr>"
            f"<td><a href=\"{url}\">{name}</a></td>"
            f"<td>{status_text}</td>"
            f"<td>{conclusion}</td>"
            f"<td>{updated}</td>"
            f"<td>{html.escape(str(run.get('event') or ''))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_status_page(status: Mapping[str, Any], history: list[dict[str, Any]]) -> str:
    generated_at = str(status.get("generated_at") or "")
    now = _parse_timestamp(generated_at) if generated_at else datetime.now(UTC)
    history = _history_window(history, now=now)
    space_stage = str(status.get("space", {}).get("stage") or "UNKNOWN")
    ci_state = _ci_state(status)
    replay = status.get("replay_artifacts", {})
    replay_verified = bool(replay.get("verified"))
    replay_count = str(replay.get("count") or 0)
    deploy_time = str(status.get("github_actions", {}).get("last_deploy_time") or "unknown")

    badges = "\n".join(
        [
            _badge("HF Space", space_stage, "ok" if space_stage == "RUNNING" else "warn"),
            _badge("CI", ci_state, "ok" if ci_state == "success" else "warn"),
            _badge(
                "Replay artifacts",
                f"{replay_count} verified" if replay_verified else f"{replay_count} check failed",
                "ok" if replay_verified else "warn",
            ),
        ]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Knoema Status</title>
  <style>
    :root {{
      color-scheme: light;
      --paper: #f8f9f4;
      --ink: #17231e;
      --muted: #657168;
      --line: #d2dacd;
      --ok: #1f7a50;
      --warn: #c8664f;
      --teal: #1d7b83;
      --white: #fffefa;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Aptos, "Segoe UI", "Noto Sans", sans-serif;
      line-height: 1.5;
    }}
    main {{ width: min(1060px, calc(100% - 32px)); margin: 0 auto; padding: 42px 0 56px; }}
    h1 {{
      margin: 0 0 12px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: clamp(2.3rem, 4vw, 4.4rem);
      line-height: 1;
      font-weight: 600;
    }}
    .muted {{ color: var(--muted); }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 12px; margin: 28px 0; }}
    .badge {{
      display: inline-flex;
      gap: 10px;
      align-items: center;
      min-height: 44px;
      padding: 9px 13px;
      border: 1px solid var(--line);
      background: var(--white);
    }}
    .badge b {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
    .badge.ok {{ border-color: color-mix(in srgb, var(--ok), var(--line)); color: var(--ok); }}
    .badge.warn {{ border-color: color-mix(in srgb, var(--warn), var(--line)); color: var(--warn); }}
    section {{ margin-top: 30px; }}
    .history {{ display: flex; align-items: end; gap: 4px; min-height: 44px; }}
    .bar {{ display: inline-block; width: 18px; height: 34px; background: var(--ok); }}
    .bar.warn {{ background: var(--warn); }}
    table {{ width: 100%; border-collapse: collapse; background: var(--white); border: 1px solid var(--line); }}
    th, td {{ padding: 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; }}
    a {{ color: var(--teal); }}
    @media (max-width: 720px) {{
      main {{ width: min(100% - 22px, 1060px); padding-top: 26px; }}
      table {{ font-size: 0.88rem; }}
      th, td {{ padding: 10px 8px; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>Knoema Status</h1>
    <p class="muted">Last updated {html.escape(generated_at)}. Last deploy time: {html.escape(deploy_time)}.</p>
    <div class="badges" aria-label="Status badges">
      {badges}
    </div>
    <section>
      <h2>30-day history</h2>
      <div class="history" aria-label="30-day historical status bar">
        {_history_bar(history)}
      </div>
    </section>
    <section>
      <h2>Recent GitHub Actions runs</h2>
      <table>
        <thead><tr><th>Run</th><th>Status</th><th>Conclusion</th><th>Updated</th><th>Event</th></tr></thead>
        <tbody>
          {_run_rows(status)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def build_status_page(
    *,
    status_path: Path = DEFAULT_STATUS_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    history_path: Path = DEFAULT_HISTORY_PATH,
) -> None:
    status = json.loads(status_path.read_text(encoding="utf-8"))
    history = append_history(status, history_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_status_page(status, history), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static Knoema status page.")
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS_PATH)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    build_status_page(
        status_path=args.status,
        history_path=args.history,
        output_path=args.output,
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
