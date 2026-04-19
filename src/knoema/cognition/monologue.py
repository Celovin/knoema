"""Private inner-monologue generation for agents."""

from __future__ import annotations

from dataclasses import dataclass

from knoema.environment import EnvironmentContext
from knoema.persona import Persona
from knoema.prompts import normalize_prompt_language
from knoema.protocols import LLMClient, Message
from knoema.types import PERSONALITY_NEUTRAL_DEFAULTS


@dataclass(frozen=True, slots=True)
class Monologue:
    agent_id: str
    tick: int
    text: str
    language: str


class MonologueGenerator:
    """Generate a private thought for an agent before their public action."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm

    def generate(
        self,
        agent: Persona,
        context: EnvironmentContext,
        *,
        tick: int,
        language: str = "en",
    ) -> Monologue:
        resolved_language = normalize_prompt_language(language)
        if self.llm is None:
            text = _template_monologue(agent, context, resolved_language)
        else:
            text = _llm_monologue(self.llm, agent, context, resolved_language)
        return Monologue(
            agent_id=agent.agent_id,
            tick=tick,
            text=_normalize_text(text),
            language=resolved_language,
        )


def _template_monologue(
    agent: Persona,
    context: EnvironmentContext,
    language: str,
) -> str:
    field_name, direction = _dominant_trait(agent)
    templates = _trait_templates(language)
    if field_name in templates:
        high, low = templates[field_name]
        return high if direction == "high" else low
    location = context.location_path[-1]
    if language == "ko":
        if direction == "high":
            return f"나는 지금 {location}에서 내 성향이 더 강하게 드러나고 있다는 걸 느낀다."
        return f"나는 지금 {location}에서 조금 더 신중하게 움직여야 한다고 느낀다."
    return (
        f"I can feel my strongest tendencies surfacing in {location} right now."
        if direction == "high"
        else f"I need to move a little more carefully in {location} right now."
    )


def _llm_monologue(
    llm: LLMClient,
    agent: Persona,
    context: EnvironmentContext,
    language: str,
) -> str:
    system_prompt = (
        "You write a single private first-person thought for the agent. "
        "It is never spoken aloud and must not mention being an AI."
    )
    recent_events = "; ".join(event.description for event in context.recent_events[-3:]) or "none"
    user_prompt = (
        "Write exactly one private first-person thought, under 20 words.\n"
        f"Agent: {agent.name}\n"
        f"Location: {context.location}\n"
        f"Current goals: {', '.join(agent.goals) or 'none'}\n"
        f"Recent events: {recent_events}\n"
        f"Language: {language}\n"
        "Do not write dialogue, JSON, or stage directions."
    )
    messages: list[Message] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return str(llm.complete(messages, temperature=0.2, max_tokens=80))


def _dominant_trait(agent: Persona) -> tuple[str, str]:
    personality_values = agent.personality.to_dict()
    dominant_field = max(
        personality_values,
        key=lambda field_name: abs(
            float(personality_values[field_name]) - PERSONALITY_NEUTRAL_DEFAULTS[field_name]
        ),
    )
    direction = (
        "high"
        if personality_values[dominant_field] >= PERSONALITY_NEUTRAL_DEFAULTS[dominant_field]
        else "low"
    )
    return dominant_field, direction


def _normalize_text(text: str) -> str:
    cleaned = " ".join(str(text).strip().split())
    cleaned = cleaned.strip("\"' ")
    return cleaned or "..."


def _trait_templates(language: str) -> dict[str, tuple[str, str]]:
    if language == "ko":
        return {
            "conscientiousness": (
                "나는 성실성이 강해서 지금 해야 할 순서를 먼저 정리하고 싶다.",
                "나는 너무 성급해지지 않게 한 번 더 점검해야 한다.",
            ),
            "agreeableness": (
                "나는 분위기를 해치지 않으면서도 관계를 지키는 쪽을 먼저 떠올린다.",
                "나는 지금 감정보다 경계를 더 분명히 세우고 싶다.",
            ),
            "neuroticism": (
                "나는 작은 신호도 놓치면 안 된다는 긴장이 먼저 올라온다.",
                "나는 지금 평정심을 유지한 채 상황을 가볍게 보려 한다.",
            ),
            "honesty_humility": (
                "나는 지금도 정직하게 말하는 쪽이 결국 덜 후회될 거라고 느낀다.",
                "나는 이번에는 내 이익을 조금 더 먼저 계산하고 있다.",
            ),
            "machiavellianism": (
                "나는 이 흐름을 내 쪽으로 유리하게 돌릴 틈을 먼저 찾고 있다.",
                "나는 조작보다 직선적인 대응이 더 낫다고 느낀다.",
            ),
            "trait_empathy": (
                "나는 상대가 지금 어떤 감정인지 먼저 읽고 싶다.",
                "나는 지금 감정에 휩쓸리지 않고 사실만 보려 한다.",
            ),
            "fairness": (
                "나는 누가 손해를 보고 있는지부터 따져 봐야 마음이 놓인다.",
                "나는 이번에는 공정보다 실용적인 정리를 먼저 생각한다.",
            ),
            "self_direction": (
                "나는 남이 정한 틀보다 내가 납득하는 방식으로 움직이고 싶다.",
                "나는 지금은 자유보다 합의된 틀을 따르는 편이 낫다고 본다.",
            ),
            "power": (
                "나는 지금 누가 주도권을 쥐는지가 결과를 바꾼다고 느낀다.",
                "나는 주도권보다 관계 안정이 더 중요하다고 느낀다.",
            ),
            "universalism": (
                "나는 지금 이 선택이 더 넓은 사람들에게 어떤 영향을 줄지 생각한다.",
                "나는 이번엔 전체보다 가까운 범위를 먼저 챙기게 된다.",
            ),
            "security": (
                "나는 변동성보다 안전한 다음 수를 고르고 싶다.",
                "나는 지금은 안정성보다 기회를 잡는 쪽으로 기운다.",
            ),
        }
    return {
        "conscientiousness": (
            "I need to line up the next steps before I act.",
            "I should slow down before I make this messier.",
        ),
        "agreeableness": (
            "I keep looking for the move that protects the relationship.",
            "I need a firmer boundary than a softer tone right now.",
        ),
        "neuroticism": (
            "I can feel the tension rising before anyone says it out loud.",
            "I need to stay calm and keep this lighter than it feels.",
        ),
        "honesty_humility": (
            "I would rather stay straight about this than win the moment cheaply.",
            "I am already calculating what serves me best here.",
        ),
        "machiavellianism": (
            "I can already see how to steer this interaction to my advantage.",
            "A direct response feels cleaner than playing angles this time.",
        ),
        "trait_empathy": (
            "I need to read what the other person is feeling before I move.",
            "I should stay with the facts instead of absorbing everyone else's mood.",
        ),
        "fairness": (
            "I need to check who carries the cost before I commit.",
            "A practical answer matters more than perfect fairness here.",
        ),
        "self_direction": (
            "I want to move in the direction that makes sense to me, not just the expected one.",
            "I should lean on the shared structure instead of improvising alone.",
        ),
        "power": (
            "Who holds the leverage here will shape everything that follows.",
            "Control matters less than keeping the room steady right now.",
        ),
        "universalism": (
            "I keep widening the frame to who else this choice could touch.",
            "I am narrowing my focus to the immediate circle first.",
        ),
        "security": (
            "I want the safer next move more than the flashier one.",
            "I am willing to trade a little stability for momentum here.",
        ),
    }


__all__ = ["Monologue", "MonologueGenerator"]
