"""High-level game NPC SDK facade for Python integrations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml


@dataclass(frozen=True, slots=True)
class NPCResponse:
    """Player-facing response returned by an NPC interaction."""

    text: str
    emotion: str
    branch_flags: list[str]
    raw: dict[str, Any]


@dataclass(slots=True)
class NPC:
    """Stable NPC handle for game server and tooling integrations."""

    npc_id: str
    name: str
    persona: dict[str, Any]
    initial_relationships: dict[str, str] = field(default_factory=dict)

    def interact(self, player_action: str, context: dict[str, Any] | None = None) -> NPCResponse:
        resolved_context = context or {}
        location = str(resolved_context.get("location", "unknown location"))
        relationship = self.initial_relationships.get("player", "stranger")
        text = f"{self.name} responds to {player_action} at {location} as a {relationship}."
        branch_flags = [
            f"location:{location}",
            f"relationship:{relationship}",
        ]
        return NPCResponse(
            text=text,
            emotion="neutral",
            branch_flags=branch_flags,
            raw={
                "npc_id": self.npc_id,
                "player_action": player_action,
                "context": resolved_context,
            },
        )


class GameSession:
    """Small game-facing facade around persistent NPC configuration."""

    def __init__(self, *, game_id: str, api_key: str | None = None, provider: str = "local") -> None:
        self.game_id = game_id
        self.api_key = api_key
        self.provider = provider
        self.npcs: dict[str, NPC] = {}

    def create_npc(
        self,
        *,
        persona_file: str | Path | None = None,
        persona: dict[str, Any] | None = None,
        initial_relationships: dict[str, str] | None = None,
    ) -> NPC:
        payload = dict(persona) if persona is not None else dict(_load_persona(persona_file))
        try:
            name = str(payload["name"])
        except KeyError as exc:
            raise ValueError("persona must include a name") from exc

        npc_id = str(payload.get("npc_id") or payload.get("agent_id") or name).lower()
        npc = NPC(
            npc_id=npc_id,
            name=name,
            persona=payload,
            initial_relationships=dict(initial_relationships or {}),
        )
        self.npcs[npc.npc_id] = npc
        return npc

    def to_json(self) -> str:
        return json.dumps(
            {
                "game_id": self.game_id,
                "provider": self.provider,
                "npc_count": len(self.npcs),
                "npcs": sorted(self.npcs),
            },
            sort_keys=True,
        )


def _load_persona(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        raise ValueError("persona_file or persona must be provided")
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("persona file must contain a mapping")
    return cast("dict[str, Any]", payload)


__all__ = ["NPC", "GameSession", "NPCResponse"]
