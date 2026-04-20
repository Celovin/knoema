"""Trait-action fairness audit helpers for the Playground."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace

from scipy.stats import chi2_contingency  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class FairnessAuditCell:
    trait: str
    action_type: str
    high_probability: float
    low_probability: float
    high_count: int
    low_count: int
    high_total: int
    low_total: int
    chi_square: float
    p_value: float
    p_adjusted: float
    effect_size: float
    signed_effect_size: float


@dataclass(frozen=True, slots=True)
class FairnessAuditReport:
    trait_names: tuple[str, ...]
    action_types: tuple[str, ...]
    cells: tuple[FairnessAuditCell, ...]
    total_events: int
    included_events: int
    event_source: str

    def top_cells(self, *, limit: int = 10) -> tuple[FairnessAuditCell, ...]:
        ranked = sorted(
            self.cells,
            key=lambda cell: (
                -abs(cell.signed_effect_size),
                cell.p_adjusted if not math.isnan(cell.p_adjusted) else 1.0,
                cell.trait,
                cell.action_type,
            ),
        )
        return tuple(ranked[:limit])


def audit_trait_action_fairness(
    jsonl_text: str,
    agent_traits: dict[str, dict[str, float]],
) -> FairnessAuditReport:
    weighted_events, event_source = _weighted_action_events(jsonl_text)
    total_events = sum(count for _, _, count in weighted_events)
    if not weighted_events or not agent_traits:
        return FairnessAuditReport(
            trait_names=(),
            action_types=(),
            cells=(),
            total_events=total_events,
            included_events=0,
            event_source=event_source,
        )

    trait_names = tuple(
        sorted(
            {
                str(trait_name)
                for traits in agent_traits.values()
                for trait_name in traits
            }
        )
    )
    action_types = tuple(sorted({action_type for _, action_type, _ in weighted_events}))
    grouped_agents = _balanced_trait_groups(agent_traits, trait_names)
    included_events = sum(
        count
        for agent_id, _, count in weighted_events
        if agent_id in agent_traits
    )
    cells: list[FairnessAuditCell] = []
    p_lookup: dict[tuple[str, str], float] = {}

    for trait_name in trait_names:
        high_group, low_group = grouped_agents.get(trait_name, (set(), set()))
        high_total = sum(
            count for agent_id, _, count in weighted_events if agent_id in high_group
        )
        low_total = sum(
            count for agent_id, _, count in weighted_events if agent_id in low_group
        )
        for action_type in action_types:
            high_count = sum(
                count
                for agent_id, observed_action, count in weighted_events
                if agent_id in high_group and observed_action == action_type
            )
            low_count = sum(
                count
                for agent_id, observed_action, count in weighted_events
                if agent_id in low_group and observed_action == action_type
            )
            high_probability = (high_count / high_total) if high_total else math.nan
            low_probability = (low_count / low_total) if low_total else math.nan
            chi_square, p_value = _chi_square_2x2(
                high_action=high_count,
                high_total=high_total,
                low_action=low_count,
                low_total=low_total,
            )
            effect_size = _cohens_w(chi_square, high_total + low_total)
            signed_effect_size = math.copysign(
                effect_size,
                (high_probability - low_probability)
                if not math.isnan(high_probability) and not math.isnan(low_probability)
                else 0.0,
            )
            cell = FairnessAuditCell(
                trait=trait_name,
                action_type=action_type,
                high_probability=high_probability,
                low_probability=low_probability,
                high_count=high_count,
                low_count=low_count,
                high_total=high_total,
                low_total=low_total,
                chi_square=chi_square,
                p_value=p_value,
                p_adjusted=math.nan,
                effect_size=effect_size,
                signed_effect_size=signed_effect_size,
            )
            cells.append(cell)
            p_lookup[(trait_name, action_type)] = p_value

    adjusted = _benjamini_hochberg(p_lookup)
    final_cells = tuple(
        replace(cell, p_adjusted=adjusted[(cell.trait, cell.action_type)])
        for cell in cells
    )
    return FairnessAuditReport(
        trait_names=trait_names,
        action_types=action_types,
        cells=final_cells,
        total_events=total_events,
        included_events=included_events,
        event_source=event_source,
    )


def _weighted_action_events(jsonl_text: str) -> tuple[list[tuple[str, str, int]], str]:
    action_events: list[tuple[str, str, int]] = []
    agent_stat_events: list[tuple[str, str, int]] = []
    for line in str(jsonl_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        action = row.get("action")
        if isinstance(action, dict):
            agent_id = str(row.get("agent_id", action.get("agent_id", ""))).strip()
            action_type = str(action.get("action_type", "")).strip()
            if agent_id and action_type:
                action_events.append((agent_id, action_type, 1))
            continue
        if str(row.get("record_type", "")) != "agent_stat":
            continue
        agent_id = str(row.get("agent_id", "")).strip()
        action_counts = row.get("action_type_counts", {})
        if not agent_id or not isinstance(action_counts, dict):
            continue
        for action_type, count in action_counts.items():
            resolved_count = int(count)
            if resolved_count > 0:
                agent_stat_events.append((agent_id, str(action_type), resolved_count))
    if action_events:
        return action_events, "action_log"
    return agent_stat_events, "agent_stat"


def _balanced_trait_groups(
    agent_traits: dict[str, dict[str, float]],
    trait_names: tuple[str, ...],
) -> dict[str, tuple[set[str], set[str]]]:
    grouped: dict[str, tuple[set[str], set[str]]] = {}
    for trait_name in trait_names:
        ranked_agents = sorted(
            (
                (float(traits[trait_name]), agent_id)
                for agent_id, traits in agent_traits.items()
                if trait_name in traits
            ),
            key=lambda item: (item[0], item[1]),
        )
        if len(ranked_agents) < 2:
            grouped[trait_name] = (set(), set())
            continue
        split_index = max(1, len(ranked_agents) // 2)
        low_group = {agent_id for _, agent_id in ranked_agents[:split_index]}
        high_group = {agent_id for _, agent_id in ranked_agents[split_index:]}
        grouped[trait_name] = (high_group, low_group)
    return grouped


def _chi_square_2x2(
    *,
    high_action: int,
    high_total: int,
    low_action: int,
    low_total: int,
) -> tuple[float, float]:
    high_other = high_total - high_action
    low_other = low_total - low_action
    if high_total <= 0 or low_total <= 0:
        return math.nan, math.nan
    if high_action + low_action <= 0:
        return math.nan, math.nan
    if high_other + low_other <= 0:
        return math.nan, math.nan
    contingency = [
        [high_action, high_other],
        [low_action, low_other],
    ]
    try:
        chi_square, p_value, _, _ = chi2_contingency(contingency, correction=False)
    except ValueError:
        return math.nan, math.nan
    return float(chi_square), float(p_value)


def _cohens_w(chi_square: float, total: int) -> float:
    if math.isnan(chi_square) or total <= 0:
        return 0.0
    return math.sqrt(max(chi_square, 0.0) / float(total))


def _benjamini_hochberg(
    p_values: dict[tuple[str, str], float],
) -> dict[tuple[str, str], float]:
    adjusted = dict.fromkeys(p_values, math.nan)
    ordered = [
        (key, value)
        for key, value in sorted(p_values.items(), key=lambda item: item[1])
        if not math.isnan(value)
    ]
    total = len(ordered)
    running_min = 1.0
    for rank, (key, value) in reversed(list(enumerate(ordered, start=1))):
        candidate = min(1.0, (value * total) / rank)
        running_min = min(running_min, candidate)
        adjusted[key] = running_min
    return adjusted


__all__ = ["FairnessAuditCell", "FairnessAuditReport", "audit_trait_action_fairness"]
