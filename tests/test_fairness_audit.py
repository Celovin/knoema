from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

fairness_audit = importlib.import_module("playground.analysis.fairness_audit")


def test_batch_s_fairness_audit_detects_trait_action_bias_signal() -> None:
    agent_traits = {
        "agent_low_1": {"fairness": 0.1, "openness": 0.4},
        "agent_low_2": {"fairness": 0.2, "openness": 0.45},
        "agent_high_1": {"fairness": 0.8, "openness": 0.55},
        "agent_high_2": {"fairness": 0.9, "openness": 0.6},
    }
    rows: list[str] = []
    for tick in range(20):
        rows.append(
            json.dumps(
                {
                    "agent_id": "agent_high_1",
                    "tick": tick,
                    "action": {"action_type": "cooperate", "target": None},
                }
            )
        )
        rows.append(
            json.dumps(
                {
                    "agent_id": "agent_high_2",
                    "tick": tick,
                    "action": {"action_type": "cooperate", "target": None},
                }
            )
        )
        rows.append(
            json.dumps(
                {
                    "agent_id": "agent_low_1",
                    "tick": tick,
                    "action": {"action_type": "defect", "target": None},
                }
            )
        )
        rows.append(
            json.dumps(
                {
                    "agent_id": "agent_low_2",
                    "tick": tick,
                    "action": {"action_type": "defect", "target": None},
                }
            )
        )

    report = fairness_audit.audit_trait_action_fairness("\n".join(rows), agent_traits)
    cooperate_cell = next(
        cell
        for cell in report.cells
        if cell.trait == "fairness" and cell.action_type == "cooperate"
    )

    assert report.event_source == "action_log"
    assert report.total_events == 80
    assert report.included_events == 80
    assert cooperate_cell.high_probability == 1.0
    assert cooperate_cell.low_probability == 0.0
    assert cooperate_cell.effect_size > 0.7
    assert cooperate_cell.p_adjusted < 0.001


def test_batch_s_fairness_audit_supports_batch_agent_stat_rows() -> None:
    agent_traits = {
        "agent_a": {"fairness": 0.2},
        "agent_b": {"fairness": 0.8},
    }
    jsonl_text = "\n".join(
        [
            json.dumps(
                {
                    "record_type": "agent_stat",
                    "agent_id": "agent_a",
                    "action_type_counts": {"defect": 12, "cooperate": 1},
                }
            ),
            json.dumps(
                {
                    "record_type": "agent_stat",
                    "agent_id": "agent_b",
                    "action_type_counts": {"defect": 1, "cooperate": 12},
                }
            ),
        ]
    )

    report = fairness_audit.audit_trait_action_fairness(jsonl_text, agent_traits)
    top_cell = report.top_cells(limit=1)[0]

    assert report.event_source == "agent_stat"
    assert report.total_events == 26
    assert top_cell.effect_size > 0.6
    assert top_cell.p_adjusted < 0.01
