from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def test_subtask1_graph_is_stacked_above_timeline_with_scrollable_timeline() -> None:
    app = playground_app.build_app()

    assert not any(
        type(child).__name__ == "Row"
        and {type(grandchild).__name__ for grandchild in getattr(child, "children", [])} == {"Markdown", "Plot"}
        for child in app.children
    )

    plot_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Plot" and getattr(child, "elem_id", None) == "relationship-graph"
    )
    timeline_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Markdown" and getattr(child, "elem_id", None) == "timeline-panel"
    )

    assert plot_index < timeline_index


def test_subtask1_graph_height_and_timeline_scroll_tokens_are_exposed() -> None:
    figure = playground_app._relationship_figure([])

    assert figure.layout.height == playground_app.GRAPH_HEIGHT_PX
    assert playground_app.GRAPH_HEIGHT_PX == 620
    assert playground_app.TIMELINE_MAX_HEIGHT_PX == 360
    assert "#relationship-graph" in playground_app.FOOTER_CSS
    assert "#timeline-panel" in playground_app.FOOTER_CSS
    assert "overflow-y: auto;" in playground_app.FOOTER_CSS
