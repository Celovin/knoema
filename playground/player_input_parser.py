"""Parse free-form player text into Luvoire actions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

PLAYER_HELP = {
    "en": (
        "Available commands: `attack <target>`, `say <message>`, "
        "`/quest start`, or plain text to speak."
    ),
    "ko": (
        "\uc0ac\uc6a9 \uac00\ub2a5\ud55c \uba85\ub839: `\uacf5\uaca9 <\ub300\uc0c1>`, "
        "`\ub9d0\ud574 <\uba54\uc2dc\uc9c0>`, `/quest \uc2dc\uc791`, "
        "\ub610\ub294 \uc77c\ubc18 \ubb38\uc7a5 \uc785\ub825."
    ),
}


@dataclass(frozen=True, slots=True)
class ParsedPlayerInput:
    action_type: str
    target: str | None
    content: str
    metadata: dict[str, Any]


def parse_player_input(
    text: str,
    *,
    agent_id: str,
    timestamp: datetime,
    location: str,
    roster: list[tuple[str, str]],
    language: str = "en",
) -> ParsedPlayerInput | None:
    raw = text.strip()
    metadata = {
        "player_controlled": True,
        "timestamp": timestamp.isoformat(),
        "location": location,
        "language": language,
    }
    if not raw:
        return ParsedPlayerInput(
            action_type="speak",
            target=None,
            content="...",
            metadata=metadata,
        )

    lowered = raw.lower()
    if lowered == "/help":
        return None

    target = _resolve_target(raw, roster, agent_id)
    if lowered.startswith("attack") or raw.startswith("\uacf5\uaca9"):
        action_type = "attack_target"
    elif (
        lowered.startswith("say")
        or raw.startswith("\ub9d0\ud574")
        or raw.startswith("\ub9d0\ud55c\ub2e4")
    ):
        action_type = "speak"
    elif lowered.startswith("/quest") and (
        "start" in lowered or "\uc2dc\uc791" in raw or "\uc218\ub77d" in raw
    ):
        action_type = "quest_accept"
    else:
        action_type = "speak"

    return ParsedPlayerInput(
        action_type=action_type,
        target=target,
        content=raw,
        metadata=metadata,
    )


def player_help_text(language: str = "en") -> str:
    return PLAYER_HELP["ko" if language == "ko" else "en"]


def _resolve_target(
    text: str,
    roster: list[tuple[str, str]],
    agent_id: str,
) -> str | None:
    lowered = text.lower()
    for candidate_id, candidate_name in roster:
        if candidate_id == agent_id:
            continue
        if re.search(rf"\b{re.escape(candidate_id.lower())}\b", lowered):
            return candidate_id
        if candidate_name and candidate_name.lower() in lowered:
            return candidate_id
    return None
