"""Timeline data builders for Streamlit pages."""

from __future__ import annotations

from typing import Any


def build_timeline_marks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "tick": row["tick"],
            "timestamp": row["timestamp"],
            "agent_id": row["agent_id"],
            "label": row["action"]["action_type"],
        }
        for row in rows
    ]
