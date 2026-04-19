from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_phase45_planning_depth_summary_includes_depth_five() -> None:
    subprocess.run(
        [sys.executable, "experiments/planning_depth/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    summary = json.loads(
        Path("experiments/planning_depth/results/summary.json").read_text(encoding="utf-8")
    )

    assert summary["depth_levels"] == [2, 3, 4, 5]
    assert summary["results"]["5"]["goal_achievement_rate"] > summary["results"]["5"][
        "planning_off_goal_achievement_rate"
    ]
    assert summary["acceptance"]["five_level_outperforms_planning_off"] is True
