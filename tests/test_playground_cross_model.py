from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def test_batch_p_cross_model_comparison_returns_three_results(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("DEMO_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEMO_ANTHROPIC_API_KEY", raising=False)

    results = playground_simulation.run_cross_model_comparison(
        scenario_name="Dorm: two agents",
        models=["GPT", "Claude", "Replay"],
        ticks=1,
        agent_count=2,
        master_seed=20260421,
        language="en",
    )

    assert set(results) == {"GPT", "Claude", "Replay"}
    assert all(result.log_count > 0 for result in results.values())
    assert 0.0 <= playground_simulation.cross_model_overlap_ratio(results) <= 1.0
    correlations = playground_simulation.cross_model_action_correlations(results)
    assert {(stat.left, stat.right) for stat in correlations} == {
        ("GPT", "Claude"),
        ("GPT", "Replay"),
        ("Claude", "Replay"),
    }


def test_batch_p_playground_exposes_cross_model_panel() -> None:
    app = playground_app.build_app()
    elem_ids = {
        getattr(component, "elem_id", None)
        for component in app.blocks.values()
    }

    assert "cross-model-panel" in elem_ids
    assert "cross-model-button" in elem_ids
    assert "cross-model-gpt" in elem_ids
    assert "cross-model-claude" in elem_ids
    assert "cross-model-replay" in elem_ids
