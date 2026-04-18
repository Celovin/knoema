"""High-level game NPC SDK facade for Python integrations."""

from __future__ import annotations

import json
import re
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

    def __post_init__(self) -> None:
        self.npc_id = _normalize_npc_id(self.npc_id)
        self.name = _required_text(self.name, "name")
        self.persona = dict(self.persona)
        self.initial_relationships = {
            _required_text(key, "relationship key"): _required_text(
                value,
                f"relationship value for {key}",
            )
            for key, value in self.initial_relationships.items()
        }

    def interact(self, player_action: str, context: dict[str, Any] | None = None) -> NPCResponse:
        resolved_action = _required_text(player_action, "player_action")
        resolved_context = dict(context or {})
        location = _text_or_default(resolved_context.get("location"), "unknown location")
        relationship = _text_or_default(self.initial_relationships.get("player"), "stranger")
        text = f"{self.name} responds to {resolved_action} at {location} as a {relationship}."
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
                "player_action": resolved_action,
                "context": resolved_context,
            },
        )


class GameSession:
    """Small game-facing facade around persistent NPC configuration."""

    def __init__(self, *, game_id: str, api_key: str | None = None, provider: str = "local") -> None:
        self.game_id = _required_text(game_id, "game_id")
        self.api_key = api_key
        self.provider = _required_text(provider, "provider")
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
            name = _required_text(payload["name"], "persona name")
        except KeyError as exc:
            raise ValueError("persona must include a name") from exc

        npc_id = _normalize_npc_id(payload.get("npc_id") or payload.get("agent_id") or name)
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


def _required_text(value: object, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} must not be empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text


def _text_or_default(value: object, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_npc_id(value: object) -> str:
    raw = _required_text(value, "npc_id")
    normalized = re.sub(r"[^a-z0-9._-]+", "-", raw.lower()).strip("-._")
    if not normalized or re.search(r"[a-z0-9]", normalized) is None:
        raise ValueError("npc_id must contain at least one alphanumeric character")
    return normalized


__all__ = ["NPC", "GameSession", "NPCResponse"]
