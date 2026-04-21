from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def test_batch_v_playground_exposes_scenario_synthesis_panel() -> None:
    app = playground_app.build_app()
    elem_ids = {getattr(component, "elem_id", None) for component in app.blocks.values()}

    assert "scenario-synthesis-panel" in elem_ids
    assert "scenario-synthesis-input" in elem_ids
    assert "scenario-synthesis-button" in elem_ids
    assert "scenario-synthesis-output" in elem_ids


def test_batch_v_playground_synthesis_updates_agent_sliders() -> None:
    updates = playground_app._scenario_synthesis_updates(
        "A market dispute with 2 merchants and 1 customer",
        "English",
    )

    assert updates[0]["value"] == 3
    assert updates[1]["value"].startswith("Merchant")
    assert updates[3]["value"] == ""
    assert isinstance(updates[-1]["value"], str)
    assert "Synthesized scenario YAML" in updates[-1]["value"]
