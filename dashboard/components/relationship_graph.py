"""Relationship graph derivation and rendering."""

from __future__ import annotations

import math
from collections import Counter

from dashboard.data import ActionRow


def build_relationship_edges(rows: list[ActionRow]) -> list[dict[str, object]]:
    counts = Counter((row.agent_id, row.target) for row in rows if row.target)
    if not counts:
        return []
    max_count = max(counts.values())
    return [
        {
            "source": source,
            "target": target,
            "interactions": count,
            "weight": round(count / max_count, 3),
        }
        for (source, target), count in sorted(counts.items())
    ]


def make_relationship_figure(edges: list[dict[str, object]]):
    import plotly.graph_objects as go

    nodes = sorted(
        {
            str(node)
            for edge in edges
            for node in (edge["source"], edge["target"])
            if node is not None
        }
    )
    if not nodes:
        return go.Figure()

    positions = {
        node: (
            math.cos((2 * math.pi * index) / len(nodes)),
            math.sin((2 * math.pi * index) / len(nodes)),
        )
        for index, node in enumerate(nodes)
    }

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])
        source_x, source_y = positions[source]
        target_x, target_y = positions[target]
        edge_x.extend([source_x, target_x, None])
        edge_y.extend([source_y, target_y, None])

    node_x = [positions[node][0] for node in nodes]
    node_y = [positions[node][1] for node in nodes]
    incoming = Counter(str(edge["target"]) for edge in edges)
    outgoing = Counter(str(edge["source"]) for edge in edges)
    sizes = [24 + ((incoming[node] + outgoing[node]) * 8) for node in nodes]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"width": 1.5, "color": "#7A8699"},
            hoverinfo="none",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=nodes,
            textposition="top center",
            marker={"size": sizes, "color": "#2F80ED", "line": {"width": 1, "color": "#111827"}},
        )
    )
    figure.update_layout(
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        showlegend=False,
        xaxis={"visible": False},
        yaxis={"visible": False},
        height=420,
    )
    return figure


def render_relationship_graph(rows: list[ActionRow]) -> None:
    import streamlit as st

    edges = build_relationship_edges(rows)
    if not edges:
        st.info("Targeted actions will appear as relationship edges.")
        return
    st.plotly_chart(make_relationship_figure(edges), use_container_width=True)
    st.dataframe(edges, hide_index=True, use_container_width=True)
