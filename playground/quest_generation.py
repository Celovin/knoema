"""Deterministic procedural quest generation for the playground."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from knoema.environment import Environment
from knoema.persona import Persona


@dataclass(frozen=True, slots=True)
class ProceduralQuest:
    quest_id: str
    title: str
    objective: str
    giver_agent_id: str
    target_agent_id: str | None
    location: str
    success_conditions: tuple[str, ...]
    failure_conditions: tuple[str, ...]
    reward: str | None
    quest_source: str = "procedural"

    def to_metadata(self) -> dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "quest_title": self.title,
            "quest_objective": self.objective,
            "giver_agent_id": self.giver_agent_id,
            "target_agent_id": self.target_agent_id,
            "location": self.location,
            "success_conditions": list(self.success_conditions),
            "failure_conditions": list(self.failure_conditions),
            "reward": self.reward,
            "quest_source": self.quest_source,
        }


def generate_procedural_quest(
    agents: Sequence[Persona],
    environment: Environment,
    *,
    session_id: str,
    language: str = "en",
) -> ProceduralQuest:
    if not agents:
        raise ValueError("agents must not be empty")

    giver = max(agents, key=_giver_priority)
    other_agents = [agent for agent in agents if agent.agent_id != giver.agent_id]
    quest_kind = _quest_kind(giver, environment)
    target = _select_target(other_agents, session_id=session_id, quest_kind=quest_kind)
    location = environment.get_context(giver.agent_id).location
    focus = _focus_phrase(environment, quest_kind=quest_kind, language=language)
    title, objective = _quest_copy(
        quest_kind=quest_kind,
        focus=focus,
        giver=giver,
        target=target,
        location=location,
        language=language,
    )
    success_conditions = _success_conditions(
        quest_kind=quest_kind,
        focus=focus,
        target=target,
        location=location,
        language=language,
    )
    failure_conditions = _failure_conditions(
        quest_kind=quest_kind,
        focus=focus,
        target=target,
        location=location,
        language=language,
    )
    reward = _reward_phrase(giver, language=language)
    quest_suffix = hashlib.sha1(session_id.encode("utf-8")).hexdigest()[:10]
    return ProceduralQuest(
        quest_id=f"quest_{giver.agent_id}_{quest_suffix}",
        title=title,
        objective=objective,
        giver_agent_id=giver.agent_id,
        target_agent_id=(None if target is None else target.agent_id),
        location=location,
        success_conditions=success_conditions,
        failure_conditions=failure_conditions,
        reward=reward,
    )


def _giver_priority(agent: Persona) -> float:
    personality = agent.personality
    return (
        personality.conscientiousness * 1.6
        + personality.achievement * 1.2
        + personality.benevolence
        + personality.need_for_cognition * 0.8
        + personality.agreeableness * 0.4
        + (0.25 if agent.factions else 0.0)
        + (0.1 if agent.inventory and agent.inventory.item_ids else 0.0)
    )


def _quest_kind(agent: Persona, environment: Environment) -> str:
    personality = agent.personality
    context_text = _environment_text(environment)
    inventory_items = list(agent.inventory.item_ids) if agent.inventory is not None else []
    if any(
        token in context_text
        for token in (
            "repair",
            "damaged",
            "broken",
            "inspection",
            "hazard",
            "storm",
            "wind",
            "outage",
            "safety",
        )
    ):
        return "stabilize"
    if inventory_items:
        return "deliver"
    if personality.agreeableness + personality.trait_empathy + personality.benevolence >= 1.95:
        return "check_in"
    if personality.need_for_cognition + personality.conscientiousness + personality.fairness >= 2.05:
        return "verify"
    if personality.achievement + personality.power >= 1.35:
        return "coordinate"
    return "survey"


def _environment_text(environment: Environment) -> str:
    fragments = [" > ".join(environment.location_path)]
    for key, value in sorted(environment.conditions.items()):
        fragments.append(f"{key} {value}")
    return " ".join(fragment.lower() for fragment in fragments)


def _focus_phrase(environment: Environment, *, quest_kind: str, language: str) -> str:
    social_context = str(environment.conditions.get("social_context", "")).strip()
    weather = str(environment.conditions.get("weather", "")).strip()
    location_leaf = environment.location_path[-1]
    combined = _environment_text(environment)
    if quest_kind == "stabilize":
        if "stall" in combined:
            return "손상된 장터 부스" if language == "ko" else "the damaged market stall"
        if "inspection" in combined:
            return "점검 준비" if language == "ko" else "the upcoming inspection"
        if "repair" in combined:
            return "공간 정비" if language == "ko" else "the repair backlog"
        return "현장 리스크" if language == "ko" else "the local risk"
    if quest_kind == "deliver":
        return "핵심 물자" if language == "ko" else "the needed supplies"
    if quest_kind == "check_in":
        if social_context:
            return social_context if language != "ko" else "긴장된 분위기"
        return "긴장된 분위기" if language == "ko" else "the rising tension"
    if quest_kind == "verify":
        if "record" in combined or "ledger" in combined or "receipt" in combined:
            return "기록 불일치" if language == "ko" else "the record mismatch"
        if "inspection" in combined:
            return "점검 체크리스트" if language == "ko" else "the inspection checklist"
        return "운영 세부사항" if language == "ko" else "the operational details"
    if quest_kind == "coordinate":
        if social_context:
            return "공동 일정" if language == "ko" else "the shared plan"
        return "현장 조율" if language == "ko" else "the current coordination load"
    if weather and weather.lower() != "clear":
        return weather if language != "ko" else f"{weather} 대비"
    return location_leaf if language != "ko" else f"{location_leaf} 현장"


def _select_target(
    agents: Sequence[Persona],
    *,
    session_id: str,
    quest_kind: str,
) -> Persona | None:
    if not agents:
        return None
    if quest_kind == "check_in":
        return max(
            agents,
            key=lambda agent: (
                agent.personality.neuroticism + agent.personality.agreeableness,
                agent.agent_id,
            ),
        )
    if quest_kind == "verify":
        return max(
            agents,
            key=lambda agent: (
                agent.personality.conscientiousness + agent.personality.need_for_cognition,
                agent.agent_id,
            ),
        )
    ordered = sorted(agents, key=lambda agent: agent.agent_id)
    bucket = int(hashlib.sha1(f"{session_id}|{quest_kind}".encode()).hexdigest()[:8], 16)
    return ordered[bucket % len(ordered)]


def _quest_copy(
    *,
    quest_kind: str,
    focus: str,
    giver: Persona,
    target: Persona | None,
    location: str,
    language: str,
) -> tuple[str, str]:
    target_label = (
        target.agent_id if target is not None else ("the group" if language != "ko" else "주변 인원")
    )
    if language == "ko":
        if quest_kind == "stabilize":
            return (
                f"{focus} 안정화",
                f"{location}에서 {target_label}와 협력해 {focus}를 다음 혼잡 구간 전에 정리하세요.",
            )
        if quest_kind == "deliver":
            return (
                "핵심 물자 전달",
                f"{location}에서 필요한 물자를 챙겨 {target_label}에게 넘기고 작업 흐름을 끊기지 않게 하세요.",
            )
        if quest_kind == "check_in":
            return (
                f"{target_label} 상태 확인",
                f"{location}에서 {target_label}와 대화해 {focus}를 가라앉히고 다음 행동을 정리하세요.",
            )
        if quest_kind == "verify":
            return (
                f"{focus} 검증",
                f"{location}에서 {focus}를 확인하고 한 가지 불일치나 누락을 바로잡으세요.",
            )
        if quest_kind == "coordinate":
            return (
                "즉석 조율",
                f"{location} 상황을 묶어 {target_label}와 실행 가능한 공통 계획을 세우세요.",
            )
        return (
            f"{focus} 점검",
            f"{location}를 둘러보며 {focus}에 대한 다음 행동 하나를 찾아 보고하세요.",
        )
    if quest_kind == "stabilize":
        return (
            f"Stabilize {focus}",
            f"Work with {target_label} at {location} and secure {focus} before the next busy window.",
        )
    if quest_kind == "deliver":
        return (
            "Deliver the needed supplies",
            f"Move the needed supplies through {location} and hand them to {target_label} before work stalls.",
        )
    if quest_kind == "check_in":
        return (
            f"Check on {target_label}",
            f"Speak with {target_label} at {location} and reduce the pressure around {focus}.",
        )
    if quest_kind == "verify":
        return (
            f"Verify {focus}",
            f"Inspect {focus} at {location} and close at least one mismatch before the session ends.",
        )
    if quest_kind == "coordinate":
        return (
            "Coordinate the shared plan",
            f"Turn the current pressure at {location} into a concrete plan with {target_label}.",
        )
    return (
        f"Survey {focus}",
        f"Observe {location}, identify the pressure around {focus}, and report back with a next step.",
    )


def _success_conditions(
    *,
    quest_kind: str,
    focus: str,
    target: Persona | None,
    location: str,
    language: str,
) -> tuple[str, ...]:
    target_label = (
        target.agent_id if target is not None else ("the group" if language != "ko" else "주변 인원")
    )
    if language == "ko":
        base = (
            f"{target_label}가 {location}에서 퀘스트를 인지하고 응답한다.",
            f"{focus}와 연결된 행동이나 계획이 세션 안에 한 번 이상 나온다.",
        )
        if quest_kind == "deliver":
            return (
                base[0],
                "전달이나 교환에 해당하는 행동이 기록된다.",
            )
        if quest_kind == "verify":
            return (
                base[0],
                "관찰, 기억 조회, 혹은 계획 제안으로 점검 흐름이 이어진다.",
            )
        return base
    base = (
        f"{target_label} acknowledges the quest at {location}.",
        f"At least one action or plan references {focus} before the session ends.",
    )
    if quest_kind == "deliver":
        return (
            base[0],
            "A handoff, trade, or item action appears in the log.",
        )
    if quest_kind == "verify":
        return (
            base[0],
            "An observe, query_memory, or propose_plan action continues the verification flow.",
        )
    return base


def _failure_conditions(
    *,
    quest_kind: str,
    focus: str,
    target: Persona | None,
    location: str,
    language: str,
) -> tuple[str, ...]:
    target_label = (
        target.agent_id if target is not None else ("the group" if language != "ko" else "주변 인원")
    )
    if language == "ko":
        return (
            f"{target_label}가 {location}에서 끝까지 퀘스트를 받아들이지 않는다.",
            f"{focus}가 마지막 tick까지 해결 단서 없이 남는다.",
        )
    return (
        f"{target_label} never accepts the quest at {location}.",
        f"{focus} is still unresolved by the final tick.",
    )


def _reward_phrase(giver: Persona, *, language: str) -> str | None:
    personality = giver.personality
    if personality.benevolence >= 0.8 and personality.achievement < 0.65:
        return None
    if language == "ko":
        if personality.achievement + personality.power >= 1.35:
            return "공개적인 신뢰 상승"
        if personality.conscientiousness >= 0.75:
            return "다음 일정 우선권"
        return "작은 감사와 평판 상승"
    if personality.achievement + personality.power >= 1.35:
        return "public credit and status"
    if personality.conscientiousness >= 0.75:
        return "priority on the next task"
    return "small gratitude and reputation"


__all__ = ["ProceduralQuest", "generate_procedural_quest"]
