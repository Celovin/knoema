from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask29_build_app_exposes_competitive_comparison_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "competitive-comparison-panel"
    )

    assert panel.label == playground_app.LABELS["ko"]["competitive_panel"]


def test_subtask29_competitive_comparison_markdown_covers_required_frameworks() -> None:
    markdown = playground_app._competitive_comparison_markdown("English")

    for name in [
        "Knoema",
        "Stanford Generative Agents",
        "Google DeepMind Concordia",
        "MiroFish",
        "CAMEL-AI",
        "Microsoft AutoGen",
    ]:
        assert name in markdown

    assert "https://github.com/666ghj/MiroFish" in markdown
    assert "https://github.com/camel-ai/camel" in markdown
