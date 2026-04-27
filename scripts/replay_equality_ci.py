"""Replay-equality CI gate.

Re-runs the two committed deterministic scenarios (synthetic_seoul and
crimemind_compare) and asserts that each scenario's summary_sha256 matches
the committed value. Intended to be wired into CI alongside the existing
``scripts/verify_replay_shas.py`` byte-level msgpack invariant check.

Exit codes:
    0  -- both summaries match
    1  -- at least one summary diverges (specific file is printed)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def _run_synthetic_seoul() -> dict[str, Any]:
    from scenarios.synthetic_seoul import run_scenario

    return run_scenario.run()


def _run_crimemind_compare() -> dict[str, Any]:
    from scenarios.crimemind_compare import compare

    return compare.run()


def _committed_summary(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []
    targets = (
        (
            "synthetic_seoul",
            _run_synthetic_seoul,
            ROOT
            / "scenarios"
            / "synthetic_seoul"
            / "results"
            / "synthetic_seoul_summary.json",
        ),
        (
            "crimemind_compare",
            _run_crimemind_compare,
            ROOT
            / "scenarios"
            / "crimemind_compare"
            / "results"
            / "comparison_summary.json",
        ),
    )
    for label, builder, committed_path in targets:
        if not committed_path.exists():
            failures.append(f"{label}: committed summary missing at {committed_path}")
            continue
        committed = _committed_summary(committed_path)
        fresh = builder()
        if fresh["summary_sha256"] != committed["summary_sha256"]:
            failures.append(
                f"{label}: drift -- fresh={fresh['summary_sha256'][:16]}... "
                f"committed={committed['summary_sha256'][:16]}..."
            )
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(f"replay-equality CI: {len(targets)} scenarios verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
