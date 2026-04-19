from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from knoema.theory_of_mind import run_sally_anne_tier_ablation


def test_phase44_sally_anne_tier_ablation_reports_material_tiers() -> None:
    result = run_sally_anne_tier_ablation()

    assert result.baseline_accuracy == 1.0
    assert len(result.rows) == 6
    assert any(row.material_effect for row in result.rows)
    assert next(row for row in result.rows if row.tier_id == "tier_c").material_effect is False


def test_phase44_sally_anne_tier_ablation_is_deterministic() -> None:
    first = run_sally_anne_tier_ablation().to_json_dict()
    second = run_sally_anne_tier_ablation().to_json_dict()

    assert first == second


def test_phase44_sally_anne_tier_ablation_script_writes_summary() -> None:
    subprocess.run(
        [sys.executable, "experiments/theory_of_mind_ablation/run.py"],
        check=True,
        cwd=Path.cwd(),
    )
    summary = json.loads(
        Path("experiments/theory_of_mind_ablation/results/summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["baseline_accuracy"] == 1.0
    assert "tier_c" not in summary["material_tiers"]
    assert "tier_a" in summary["material_tiers"]
