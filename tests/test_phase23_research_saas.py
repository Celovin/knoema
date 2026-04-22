from __future__ import annotations

import json
from pathlib import Path

from saas.components.graph_viz import build_relationship_graph
from saas.components.timeline import build_timeline_marks
from saas.components.token_meter import estimate_token_budget
from saas.services.experiment_store import (
    citation_bundle,
    compare_experiments,
    load_experiment_jsonl,
    memory_inspector_rows,
    relationship_graph_rows,
    summarize_experiment,
)
from saas.services.replay import ab_timeline, playback_window


def test_phase23_research_saas_files_exist() -> None:
    expected = [
        "saas/app.py",
        "saas/requirements.txt",
        "saas/pages/1_Simulation_Runner.py",
        "saas/pages/2_Experiment_Comparison.py",
        "saas/pages/3_Memory_Inspector.py",
        "saas/pages/4_Relationship_Explorer.py",
        "saas/pages/5_Cost_Budget.py",
        "saas/pages/6_Export_Citations.py",
        "saas/components/timeline.py",
        "saas/components/graph_viz.py",
        "saas/components/token_meter.py",
        "saas/services/experiment_store.py",
        "saas/services/replay.py",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase23_experiment_comparison_and_replay(tmp_path: Path) -> None:
    left_path = tmp_path / "left.jsonl"
    right_path = tmp_path / "right.jsonl"
    left_rows = [_record(0, "alice", "bob"), _record(1, "bob", None)]
    right_rows = [*left_rows, _record(2, "cara", "alice")]
    left_path.write_text("\n".join(json.dumps(row) for row in left_rows), encoding="utf-8")
    right_path.write_text("\n".join(json.dumps(row) for row in right_rows), encoding="utf-8")

    left = load_experiment_jsonl(left_path)
    right = load_experiment_jsonl(right_path)
    comparison = compare_experiments(left, right)

    assert summarize_experiment(left).action_count == 2
    assert comparison["action_delta"] == 1
    assert comparison["right_only_agents"] == ["cara"]
    assert playback_window(right, tick_start=1, tick_end=2) == right[1:]
    assert ab_timeline(left, right)[-1] == {"tick": 2, "A": 0, "B": 1, "delta": 1}


def test_phase23_memory_relationship_timeline_and_budget() -> None:
    rows = [_record(0, "alice", "bob"), _record(1, "bob", "alice")]

    assert memory_inspector_rows(rows)[0]["memory_proxy"] == "alice acts at tick 0"
    assert relationship_graph_rows(rows)[0]["interactions"] == 1
    assert build_relationship_graph(rows)["nodes"] == [
        {"id": "alice", "label": "alice"},
        {"id": "bob", "label": "bob"},
    ]
    assert build_timeline_marks(rows)[1]["label"] == "speak"
    assert estimate_token_budget(rows)["total_cost"] == 0.00068


def test_phase23_citation_bundle_exports_bibtex_and_apa() -> None:
    bundle = citation_bundle(title="Luvoire Research Experiment")

    assert "@software{luvoireengineresearchex" in bundle["bibtex"]
    assert "Celovin. (2026)." in bundle["apa"]


def _record(tick: int, agent_id: str, target: str | None) -> dict[str, object]:
    return {
        "tick": tick,
        "timestamp": f"2026-06-01T0{tick}:00:00",
        "agent_id": agent_id,
        "action": {
            "agent_id": agent_id,
            "timestamp": f"2026-06-01T0{tick}:00:00",
            "action_type": "speak",
            "target": target,
            "content": f"{agent_id} acts at tick {tick}",
            "location": "Luvoire Demo World > Lab",
        },
    }
