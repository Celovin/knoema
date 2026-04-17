"""Knoema Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from dashboard.components.agent_view import render_agent_view
from dashboard.components.conversation_log import render_conversation_log
from dashboard.components.relationship_graph import render_relationship_graph
from dashboard.data import (
    filter_rows,
    load_jsonl,
    loads_jsonl,
    normalize_log_records,
    summarize_logs,
)

SAMPLE_LOG = Path(__file__).with_name("sample_simulation.jsonl")


def main() -> None:
    st.set_page_config(page_title="Knoema Dashboard", layout="wide")
    st.title("Knoema Dashboard")

    records = _load_records()
    rows = normalize_log_records(records) if records else []
    summary = summarize_logs(rows)

    _render_metrics(summary)

    agents = ["All", *sorted({row.agent_id for row in rows})]
    with st.sidebar:
        st.header("Filters")
        agent_id = st.selectbox("Agent", agents, index=0)
        search = st.text_input("Search")
        limit = st.slider("Rows", min_value=10, max_value=500, value=120, step=10)

    filtered_rows = filter_rows(rows, agent_id=agent_id, search=search)

    tab_agents, tab_graph, tab_log = st.tabs(["Agents", "Relationships", "Log"])
    with tab_agents:
        render_agent_view(filtered_rows)
    with tab_graph:
        render_relationship_graph(filtered_rows)
    with tab_log:
        render_conversation_log(filtered_rows, limit=limit)


def _load_records() -> list[dict[str, object]]:
    with st.sidebar:
        st.header("Input")
        use_sample = st.checkbox("Use bundled sample", value=True)
        uploaded = st.file_uploader("Upload JSONL", type=["jsonl", "json"])
        path_text = st.text_input("Local JSONL path", value="")

    if uploaded is not None:
        text = uploaded.getvalue().decode("utf-8")
        return loads_jsonl(text)
    if path_text.strip():
        return load_jsonl(path_text.strip())
    if use_sample and SAMPLE_LOG.exists():
        return load_jsonl(SAMPLE_LOG)
    return []


def _render_metrics(summary: dict[str, object]) -> None:
    col_actions, col_agents, col_ticks, col_window = st.columns(4)
    col_actions.metric("Actions", int(summary["total_actions"]))
    col_agents.metric("Agents", int(summary["agent_count"]))
    col_ticks.metric("Ticks", int(summary["tick_count"]))
    window = f"{summary['time_start']} -> {summary['time_end']}" if summary["time_start"] else "-"
    col_window.metric("Window", window)


if __name__ == "__main__":
    main()
