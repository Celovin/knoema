"""Inventory and faction helpers for game-style action effects."""

from __future__ import annotations

from dataclasses import dataclass, field

from knoema.types import Action


def _validate_item_id(item_id: str) -> str:
    normalized = item_id.strip()
    if not normalized:
        raise ValueError("item_id must not be blank")
    return normalized


@dataclass(slots=True)
class Inventory:
    item_ids: list[str] = field(default_factory=list)

    def add(self, item_id: str) -> None:
        self.item_ids.append(_validate_item_id(item_id))

    def remove(self, item_id: str) -> bool:
        normalized = _validate_item_id(item_id)
        try:
            self.item_ids.remove(normalized)
        except ValueError:
            return False
        return True

    def has(self, item_id: str) -> bool:
        normalized = item_id.strip()
        return bool(normalized) and normalized in self.item_ids


@dataclass(slots=True)
class Faction:
    reputation_by_id: dict[str, float] = field(default_factory=dict)

    def join(self, faction_id: str) -> float:
        normalized = faction_id.strip()
        if not normalized:
            raise ValueError("faction_id must not be blank")
        self.reputation_by_id[normalized] = 0.5
        return self.reputation_by_id[normalized]

    def betray(self, faction_id: str) -> float:
        normalized = faction_id.strip()
        if not normalized:
            raise ValueError("faction_id must not be blank")
        self.reputation_by_id[normalized] = -0.7
        return self.reputation_by_id[normalized]

    def reputation(self, faction_id: str) -> float:
        return float(self.reputation_by_id.get(faction_id.strip(), 0.0))

    def as_dict(self) -> dict[str, float]:
        return dict(self.reputation_by_id)


def apply_inventory_action(inventory: Inventory | None, action: Action) -> Inventory | None:
    if action.action_type not in {"use_item", "pickup_item", "drop_item", "craft_item"}:
        return inventory

    resolved = inventory if inventory is not None else Inventory()
    item_id = str(action.metadata.get("item_id", "")).strip()
    if action.action_type == "pickup_item" and item_id:
        resolved.add(item_id)
    elif action.action_type in {"use_item", "drop_item"} and item_id:
        resolved.remove(item_id)
    elif action.action_type == "craft_item":
        for material in action.metadata.get("materials", []):
            if isinstance(material, str) and material.strip():
                resolved.remove(material)
        crafted_item = item_id or "crafted_item"
        resolved.add(crafted_item)
    return resolved


def apply_faction_action(
    factions: dict[str, float] | None,
    action: Action,
) -> dict[str, float] | None:
    if action.action_type not in {"faction_join", "faction_betray"}:
        return factions

    faction_id = str(action.metadata.get("faction_id", "")).strip()
    if not faction_id:
        return factions
    resolved = Faction(reputation_by_id=dict(factions or {}))
    if action.action_type == "faction_join":
        resolved.join(faction_id)
    else:
        resolved.betray(faction_id)
    return resolved.as_dict()
