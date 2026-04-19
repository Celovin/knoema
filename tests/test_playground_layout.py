from __future__ import annotations

import importlib
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask1_graph_is_stacked_above_timeline_with_scrollable_timeline() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    assert not any(
        type(child).__name__ == "Row"
        and {type(grandchild).__name__ for grandchild in getattr(child, "children", [])} == {"Markdown", "Plot"}
        for child in app.children
    )

    plot_index = next(
        index
        for index, child in enumerate(components)
        if type(child).__name__ == "Plot" and getattr(child, "elem_id", None) == "relationship-graph"
    )
    timeline_index = next(
        index
        for index, child in enumerate(components)
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


def test_subtask12_build_app_exposes_html_report_export_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    html_report_button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "html-report-button"
    )
    html_report_download = next(
        component
        for component in components
        if type(component).__name__ == "File"
        and getattr(component, "elem_id", None) == "html-report-download"
    )

    assert html_report_button.value == playground_app.LABELS["ko"]["html_report_button"]
    assert html_report_download.label == playground_app.LABELS["ko"]["html_report_download"]


def test_subtask12_export_html_report_writes_self_contained_html() -> None:
    figure = playground_app.go.Figure(
        data=[playground_app.go.Scatter(x=[0, 1], y=[1, 2], mode="lines+markers")]
    )

    report_path = playground_app._export_html_report(
        "### Timeline\n- agent_1 spoke",
        figure,
        '{"tick": 0, "agent_id": "agent_1"}',
        "Mode: Replay only | Agents: 2",
        "English",
    )

    report_file = Path(report_path)
    report_html = report_file.read_text(encoding="utf-8")

    try:
        assert report_file.suffix == ".html"
        assert "Knoema Playground HTML report" in report_html
        assert "Mode: Replay only | Agents: 2" in report_html
        assert "### Timeline" in report_html
        assert '"agent_id": "agent_1"' in unescape(report_html)
        assert "Plotly.newPlot" in report_html
    finally:
        report_file.unlink(missing_ok=True)
