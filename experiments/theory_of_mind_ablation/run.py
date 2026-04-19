"""Write a deterministic Sally-Anne tier-ablation summary."""

from __future__ import annotations

import json
from pathlib import Path

from knoema.theory_of_mind import run_sally_anne_tier_ablation

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
SUMMARY_PATH = RESULTS_DIR / "summary.json"


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = run_sally_anne_tier_ablation().to_json_dict()
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
