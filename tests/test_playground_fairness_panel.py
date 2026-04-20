from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def test_batch_s_playground_exposes_fairness_panel() -> None:
    app = playground_app.build_app()
    elem_ids = {
        getattr(component, "elem_id", None)
        for component in app.blocks.values()
    }

    assert "fairness-panel" in elem_ids
    assert "fairness-heatmap" in elem_ids
    assert "fairness-summary" in elem_ids
