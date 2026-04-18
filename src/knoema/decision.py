"""Decision engine that converts agent context into the next action."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from knoema.environment import EnvironmentContext
from knoema.persona import Persona
from knoema.prompts import PromptLanguage, normalize_prompt_language, render_decision_user_prompt
from knoema.protocols import LLMClient, Message
from knoema.relationship import Relationship
from knoema.theory_of_mind import TheoryOfMindContext
from knoema.types import Action, AgentID, Emotion, Memory, WorldEvent


class DecisionEngine:
    """Prompt an LLM-like client and parse the selected action."""

    def __init__(self, llm: LLMClient, *, language: str | PromptLanguage = "en") -> None:
        self.llm = llm
        self.language = normalize_prompt_language(language)

    def decide(
        self,
        *,
        persona: Persona,
        memories: Sequence[Memory],
        relationships: Mapping[AgentID, Relationship],
        environment: EnvironmentContext,
        emotion: Emotion,
        trigger: WorldEvent | None = None,
        theory_of_mind_context: TheoryOfMindContext | None = None,
    ) -> Action:
        messages = build_decision_messages(
            persona=persona,
            memories=memories,
            relationships=relationships,
            environment=environment,
            emotion=emotion,
            trigger=trigger,
            theory_of_mind_context=theory_of_mind_context,
            language=self.language,
        )
        response = self.llm.complete(messages, temperature=0.2, max_tokens=512)
        return parse_action_response(
            response,
            agent_id=persona.agent_id,
            timestamp=environment.timestamp,
            location=environment.location,
        )


def decide(
    persona: Persona,
    memories: list[Memory],
    relationships: dict[AgentID, Relationship],
    environment: EnvironmentContext,
    emotion: Emotion,
    trigger: WorldEvent | None,
    llm: LLMClient,
    theory_of_mind_context: TheoryOfMindContext | None = None,
    language: str | PromptLanguage = "en",
) -> Action:
    """Functional facade for the decision engine."""

    return DecisionEngine(llm, language=language).decide(
        persona=persona,
        memories=memories,
        relationships=relationships,
        environment=environment,
        emotion=emotion,
        trigger=trigger,
        theory_of_mind_context=theory_of_mind_context,
    )


def build_decision_messages(
    *,
    persona: Persona,
    memories: Sequence[Memory],
    relationships: Mapping[AgentID, Relationship],
    environment: EnvironmentContext,
    emotion: Emotion,
    trigger: WorldEvent | None,
    theory_of_mind_context: TheoryOfMindContext | None = None,
    language: str | PromptLanguage = "en",
) -> list[Message]:
    memory_lines = "\n".join(
        f"- {memory.timestamp.isoformat()} [{memory.memory_type}] {memory.content}"
        for memory in memories[:8]
    )
    relationship_lines = "\n".join(
        f"- {target}: type={relationship.relationship_type}, "
        f"weight={relationship.weight:.2f}, trust={relationship.trust:.2f}"
        for target, relationship in relationships.items()
    )
    trigger_text = trigger.description if trigger is not None else "No immediate trigger."
    theory_of_mind_lines = None if theory_of_mind_context is None else theory_of_mind_context.render_lines()
    resolved_language = normalize_prompt_language(language)
    if resolved_language == "en":
        lines = [
            "Choose the next action as strict JSON.",
            'Schema: {"action_type": str, "target": str | null, "content": str}',
            f"Time: {environment.timestamp.isoformat()}",
            f"Location: {environment.location}",
            f"Conditions: {json.dumps(environment.conditions, ensure_ascii=False, sort_keys=True)}",
            f"Emotion: valence={emotion.valence:.2f}, arousal={emotion.arousal:.2f}, dominance={emotion.dominance:.2f}",
            f"Trigger: {trigger_text}",
            "Memories:",
            memory_lines or "- None",
            "Relationships:",
            relationship_lines or "- None",
        ]
        if theory_of_mind_lines:
            lines.extend(
                [
                    "Theory of mind:",
                    *theory_of_mind_lines,
                ]
            )
        user_content = "\n".join(lines)
    else:
        user_content = render_decision_user_prompt(
            memories=memories,
            relationships=relationships,
            environment=environment,
            emotion=emotion,
            trigger=trigger,
            theory_of_mind_notes=theory_of_mind_lines,
            language=resolved_language,
        )
    return [
        {"role": "system", "content": persona.to_system_prompt(language=resolved_language)},
        {"role": "user", "content": user_content},
    ]


def parse_action_response(
    response: str,
    *,
    agent_id: AgentID,
    timestamp: datetime,
    location: str,
) -> Action:
    payload = _parse_json_object(response)
    action_type = str(payload.get("action_type") or "speak")
    target_value = payload.get("target")
    target = str(target_value) if target_value not in {None, ""} else None
    content = str(payload.get("content") or response).strip()
    if not content:
        content = "..."
    return Action(
        agent_id=agent_id,
        timestamp=timestamp,
        action_type=action_type,
        target=target,
        content=content,
        location=location,
    )


def _parse_json_object(response: str) -> dict[str, Any]:
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"content": response}
        try:
            parsed = json.loads(response[start : end + 1])
        except json.JSONDecodeError:
            return {"content": response}
    if not isinstance(parsed, dict):
        return {"content": response}
    return parsed


__all__ = [
    "DecisionEngine",
    "build_decision_messages",
    "decide",
    "parse_action_response",
]
