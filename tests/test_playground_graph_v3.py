from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def test_force_graph_assets_exist() -> None:
    assert playground_app.FORCE_GRAPH_HTML_PATH.exists()
    assert playground_app.FORCE_GRAPH_VENDOR_PATH.exists()


def test_relationship_graph_html_uses_iframe_srcdoc_for_non_empty_rows() -> None:
    html = playground_app._relationship_graph_html(
        [
            {
                "source": "agent_1",
                "target": "agent_2",
                "relationship_type": "ally",
                "weight": 0.8,
                "trust": 0.9,
            }
        ],
        language="en",
        theme_mode="dark",
    )

    assert 'data-luvoire-force-graph="1"' in html
    assert 'data-luvoire-payload="' in html
    assert "srcdoc=" in html
    assert "LUVOIRE_FORCE_GRAPH_BOOT" in html
    assert "3d-force-graph.min.js" in html


def test_relationship_graph_theme_update_rebuilds_force_graph_markup() -> None:
    html = playground_app._relationship_graph_html(
        [
            {
                "source": "agent_1",
                "target": "agent_2",
                "relationship_type": "ally",
                "weight": 0.8,
                "trust": 0.9,
            }
        ],
        language="en",
        theme_mode="light",
    )

    updated = playground_app._relationship_graph_theme_update(html, "dark")

    assert updated != html
    assert "dark" in updated
