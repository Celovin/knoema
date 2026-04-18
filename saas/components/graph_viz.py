"""Relationship graph data builders for Streamlit pages."""

from __future__ import annotations

from typing import Any

from saas.services.experiment_store import relationship_graph_rows


def build_relationship_graph(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    edges = relationship_graph_rows(rows)
    nodes = sorted({edge["source"] for edge in edges} | {edge["target"] for edge in edges})
    return {
        "nodes": [{"id": node, "label": node} for node in nodes],
        "edges": edges,
    }
