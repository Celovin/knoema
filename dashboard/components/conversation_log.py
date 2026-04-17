"""Conversation log table helpers."""

from __future__ import annotations

from dashboard.data import ActionRow, rows_to_dicts


def recent_rows(rows: list[ActionRow], *, limit: int = 200) -> list[ActionRow]:
    if limit < 1:
        raise ValueError("limit must be positive")
    return sorted(rows, key=lambda row: (row.timestamp, row.tick))[-limit:]


def render_conversation_log(rows: list[ActionRow], *, limit: int = 200) -> None:
    import streamlit as st

    recent = recent_rows(rows, limit=limit)
    st.dataframe(
        rows_to_dicts(recent),
        hide_index=True,
        use_container_width=True,
        column_config={
            "content": st.column_config.TextColumn("content", width="large"),
            "timestamp": st.column_config.TextColumn("timestamp", width="medium"),
        },
    )
