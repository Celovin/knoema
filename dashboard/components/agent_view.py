"""Agent summary cards for the dashboard."""

from __future__ import annotations

from collections import Counter, defaultdict

from dashboard.data import ActionRow


def build_agent_cards(rows: list[ActionRow]) -> list[dict[str, object]]:
    grouped: dict[str, list[ActionRow]] = defaultdict(list)
    for row in rows:
        grouped[row.agent_id].append(row)

    cards: list[dict[str, object]] = []
    for agent_id, agent_rows in sorted(grouped.items()):
        action_counts = Counter(row.action_type for row in agent_rows)
        targets = {row.target for row in agent_rows if row.target}
        last_row = max(agent_rows, key=lambda row: (row.timestamp, row.tick))
        top_action = action_counts.most_common(1)[0][0] if action_counts else "unknown"
        cards.append(
            {
                "agent_id": agent_id,
                "actions": len(agent_rows),
                "top_action": top_action,
                "unique_targets": len(targets),
                "last_seen": last_row.timestamp,
                "last_line": last_row.content,
            }
        )
    return cards


def render_agent_view(rows: list[ActionRow]) -> None:
    import streamlit as st

    cards = build_agent_cards(rows)
    if not cards:
        st.info("Load a simulation log to inspect agent state.")
        return

    columns = st.columns(min(3, len(cards)))
    for index, card in enumerate(cards):
        with columns[index % len(columns)]:
            st.metric(str(card["agent_id"]), int(card["actions"]))
            st.caption(f"Top action: {card['top_action']}")
            st.write(str(card["last_line"]))
