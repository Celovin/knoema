"""Playback and live-tail helpers for simulation logs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from dashboard.data import ActionRow, rows_to_dicts


@dataclass(frozen=True, slots=True)
class PlaybackWindow:
    tick_start: int
    tick_end: int
    rows: list[ActionRow]
    total_rows: int

    @property
    def visible_rows(self) -> int:
        return len(self.rows)


def tick_bounds(rows: list[ActionRow]) -> tuple[int, int] | None:
    if not rows:
        return None
    ticks = [row.tick for row in rows]
    return min(ticks), max(ticks)


def playback_window(
    rows: list[ActionRow],
    *,
    tick_end: int,
    trailing_ticks: int,
) -> PlaybackWindow:
    if trailing_ticks < 1:
        raise ValueError("trailing_ticks must be positive")
    tick_start = tick_end - trailing_ticks + 1
    visible = [
        row
        for row in sorted(rows, key=lambda item: (item.tick, item.timestamp, item.agent_id))
        if tick_start <= row.tick <= tick_end
    ]
    return PlaybackWindow(
        tick_start=tick_start,
        tick_end=tick_end,
        rows=visible,
        total_rows=len(rows),
    )


def build_tick_summary(rows: list[ActionRow]) -> list[dict[str, object]]:
    grouped: dict[int, list[ActionRow]] = {}
    for row in rows:
        grouped.setdefault(row.tick, []).append(row)

    summary: list[dict[str, object]] = []
    for tick, tick_rows in sorted(grouped.items()):
        action_counts = Counter(row.action_type for row in tick_rows)
        top_action = action_counts.most_common(1)[0][0] if action_counts else "unknown"
        summary.append(
            {
                "tick": tick,
                "actions": len(tick_rows),
                "agents": len({row.agent_id for row in tick_rows}),
                "top_action": top_action,
                "timestamp": tick_rows[-1].timestamp,
            }
        )
    return summary


def render_realtime_view(window: PlaybackWindow) -> None:
    import streamlit as st

    st.metric("Visible actions", window.visible_rows, delta=window.total_rows - window.visible_rows)
    st.caption(f"Ticks {window.tick_start} to {window.tick_end}")

    tick_summary = build_tick_summary(window.rows)
    if tick_summary:
        st.line_chart(tick_summary, x="tick", y="actions")
        st.dataframe(tick_summary, hide_index=True, use_container_width=True)
    else:
        st.info("No actions in the selected playback window.")

    st.dataframe(
        rows_to_dicts(window.rows),
        hide_index=True,
        use_container_width=True,
        column_config={
            "content": st.column_config.TextColumn("content", width="large"),
            "timestamp": st.column_config.TextColumn("timestamp", width="medium"),
        },
    )


__all__ = [
    "PlaybackWindow",
    "build_tick_summary",
    "playback_window",
    "render_realtime_view",
    "tick_bounds",
]
