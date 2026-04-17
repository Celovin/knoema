"""Knoema Streamlit dashboard."""

from __future__ import annotations

import time
from pathlib import Path

import streamlit as st

from dashboard.components.agent_view import render_agent_view
from dashboard.components.conversation_log import render_conversation_log
from dashboard.components.realtime_view import (
    PlaybackWindow,
    playback_window,
    render_realtime_view,
    tick_bounds,
)
from dashboard.components.relationship_graph import render_relationship_graph
from dashboard.data import (
    ActionRow,
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
    window, refresh_seconds = _select_playback_window(filtered_rows)
    visible_rows = window.rows

    tab_agents, tab_graph, tab_log, tab_live = st.tabs(
        ["Agents", "Relationships", "Log", "Realtime"]
    )
    with tab_agents:
        render_agent_view(visible_rows)
    with tab_graph:
        render_relationship_graph(visible_rows)
    with tab_log:
        render_conversation_log(visible_rows, limit=limit)
    with tab_live:
        render_realtime_view(window)

    _maybe_auto_refresh(refresh_seconds)


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


def _select_playback_window(rows: list[ActionRow]) -> tuple[PlaybackWindow, int | None]:
    bounds = tick_bounds(rows)
    if bounds is None:
        return PlaybackWindow(tick_start=0, tick_end=0, rows=[], total_rows=0), None

    min_tick, max_tick = bounds
    tick_span = max(1, max_tick - min_tick + 1)
    with st.sidebar:
        st.header("Playback")
        live_tail = st.checkbox("Live tail", value=True)
        trailing_ticks = st.slider(
            "Trailing ticks",
            min_value=1,
            max_value=tick_span,
            value=min(10, tick_span),
            step=1,
        )
        if live_tail:
            tick_end = max_tick
            st.caption(f"Following latest tick: {max_tick}")
        else:
            tick_end = st.slider(
                "Current tick",
                min_value=min_tick,
                max_value=max_tick,
                value=max_tick,
                step=1,
            )
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        refresh_seconds = st.slider(
            "Refresh seconds",
            min_value=1,
            max_value=30,
            value=5,
            step=1,
            disabled=not auto_refresh,
        )

    return (
        playback_window(
            rows,
            tick_end=tick_end,
            trailing_ticks=trailing_ticks,
        ),
        refresh_seconds if auto_refresh else None,
    )


def _maybe_auto_refresh(refresh_seconds: int | None) -> None:
    if refresh_seconds is None:
        return
    with st.sidebar:
        st.caption(f"Refreshing every {refresh_seconds} seconds.")
    time.sleep(refresh_seconds)
    st.rerun()


if __name__ == "__main__":
    main()
