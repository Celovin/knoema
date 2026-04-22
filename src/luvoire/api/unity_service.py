"""Unity-facing runtime service built on the core simulator."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from knoema.api.schemas import (
    MemoryItem,
    UnityActionAcceptedResponse,
    UnityActionPayload,
    UnityActionRequest,
    UnityMemoryResponse,
    UnityTickRequest,
    UnityTickResponse,
)
from knoema.environment import Environment
from knoema.llm import LocalClient
from knoema.persona import Persona
from knoema.simulator import Simulator
from knoema.types import Action, Personality, WorldEvent


class UnitySessionNotFoundError(KeyError):
    """Raised when a Unity session has not been initialized."""


@dataclass(slots=True)
class UnityRuntimeRecord:
    session_id: str
    agent_id: str
    simulator: Simulator
    response_state: dict[str, str]
    tick: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)


class UnityRuntimeService:
    """Manage lightweight Unity NPC sessions through the existing Simulator."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], UnityRuntimeRecord] = {}
        self._lock = threading.Lock()

    def tick(self, request: UnityTickRequest) -> UnityTickResponse:
        context = _decode_json_object(request.context_json, "context_json")
        record = self._get_or_create(request.session_id, request.agent_id, context)
        with record.lock:
            self._apply_context(record, context)
            self._record_player_event(record, request.player_action, context)
            record.response_state["response"] = _tick_response_json(
                agent_id=request.agent_id,
                player_action=request.player_action,
                context=context,
            )
            tick = record.tick
            record.simulator.step(tick)
            record.tick += 1
            action = record.simulator.logs[-1].action
            return UnityTickResponse(
                session_id=record.session_id,
                agent_id=record.agent_id,
                tick=tick,
                content=action.content,
                emotion=_emotion_label(record, record.agent_id),
                branch_flags=_branch_flags(record, context),
                action=_action_payload(action),
            )

    def memory(self, *, session_id: str, agent_id: str) -> UnityMemoryResponse:
        record = self._get_existing(session_id, agent_id)
        with record.lock:
            memory_buffer = record.simulator.short_term_memories.get(agent_id)
            if memory_buffer is None:
                raise UnitySessionNotFoundError(f"{session_id}:{agent_id}")
            return UnityMemoryResponse(
                session_id=session_id,
                agent_id=agent_id,
                memories=[MemoryItem.from_domain(memory) for memory in memory_buffer.recent()],
            )

    def apply_action(
        self,
        *,
        agent_id: str,
        request: UnityActionRequest,
    ) -> UnityActionAcceptedResponse:
        context = _decode_json_object(request.context_json, "context_json")
        metadata = _decode_json_object(request.metadata_json, "metadata_json")
        record = self._get_or_create(request.session_id, agent_id, context)
        with record.lock:
            self._apply_context(record, context)
            action = Action(
                agent_id=agent_id,
                timestamp=record.simulator.environment.current_time,
                action_type=request.action_type,
                target=request.target,
                content=request.content,
                location=request.location or _location_label(context),
                metadata=metadata,
            )
            record.simulator._record_action(record.tick, record.simulator.agents[0], action)
            tick = record.tick
            record.tick += 1
            record.simulator.environment.advance_time(record.simulator.tick_duration)
            return UnityActionAcceptedResponse(
                session_id=record.session_id,
                agent_id=record.agent_id,
                tick=tick,
                accepted=True,
                action=_action_payload(action),
            )

    def shutdown(self) -> None:
        with self._lock:
            records = list(self._records.values())
            self._records.clear()
        for record in records:
            record.simulator.close()

    def _get_existing(self, session_id: str, agent_id: str) -> UnityRuntimeRecord:
        key = (_required_text(session_id, "session_id"), _required_text(agent_id, "agent_id"))
        with self._lock:
            record = self._records.get(key)
        if record is None:
            raise UnitySessionNotFoundError(f"{session_id}:{agent_id}")
        return record

    def _get_or_create(
        self,
        session_id: str,
        agent_id: str,
        context: dict[str, Any],
    ) -> UnityRuntimeRecord:
        key = (_required_text(session_id, "session_id"), _required_text(agent_id, "agent_id"))
        with self._lock:
            existing = self._records.get(key)
            if existing is not None:
                return existing
            record = _create_record(session_id=key[0], agent_id=key[1], context=context)
            self._records[key] = record
            return record

    def _apply_context(self, record: UnityRuntimeRecord, context: dict[str, Any]) -> None:
        location_path = _location_path(context)
        record.simulator.environment.set_agent_location(record.agent_id, location_path)
        record.simulator.environment.conditions["unity_context"] = dict(context)

    def _record_player_event(
        self,
        record: UnityRuntimeRecord,
        player_action: str,
        context: dict[str, Any],
    ) -> None:
        event = WorldEvent(
            timestamp=record.simulator.environment.current_time,
            event_type="player.action",
            participants=[record.agent_id, "player"],
            location=_location_label(context),
            description=_required_text(player_action, "player_action"),
        )
        record.simulator.environment.record_event(event)


def _create_record(
    *,
    session_id: str,
    agent_id: str,
    context: dict[str, Any],
) -> UnityRuntimeRecord:
    response_state = {
        "response": _tick_response_json(
            agent_id=agent_id,
            player_action="waits for player input",
            context=context,
        )
    }
    agent = Persona(
        agent_id=agent_id,
        name=_agent_name(agent_id, context),
        age=30,
        background="Unity-controlled non-player character connected through the Knoema API.",
        personality=Personality(
            openness=0.5,
            conscientiousness=0.6,
            extraversion=0.45,
            agreeableness=0.65,
            neuroticism=0.25,
        ),
        values=["continuity", "clarity"],
        goals=["respond to player input", "preserve scene continuity"],
    )
    environment = Environment(
        start_time=datetime.now(UTC).replace(microsecond=0),
        location_path=_location_path(context),
        conditions={"runtime": "unity-sdk", "session_id": session_id},
    )
    environment.set_agent_location(agent_id, _location_path(context))
    simulator = Simulator(
        agents=[agent],
        environment=environment,
        tick_duration_minutes=1,
        llm=LocalClient(lambda messages: response_state["response"]),
        language="en",
    )
    return UnityRuntimeRecord(
        session_id=session_id,
        agent_id=agent_id,
        simulator=simulator,
        response_state=response_state,
    )


def _decode_json_object(value: str, field_name: str) -> dict[str, Any]:
    if not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return dict(parsed)


def _tick_response_json(
    *,
    agent_id: str,
    player_action: str,
    context: dict[str, Any],
) -> str:
    location = _location_label(context)
    safe_action = _required_text(player_action, "player_action")
    content = f"{agent_id} responds to '{safe_action}' at {location} and keeps the scene state consistent."
    return json.dumps(
        {
            "action_type": "speak",
            "target": "player",
            "content": content,
            "metadata": {"unity_sdk": True, "player_action": safe_action},
        },
        ensure_ascii=True,
        sort_keys=True,
    )


def _location_path(context: dict[str, Any]) -> tuple[str, ...]:
    raw_path = context.get("location_path")
    if isinstance(raw_path, list):
        path = tuple(str(item).strip() for item in raw_path if str(item).strip())
        if path:
            return path
    raw_location = context.get("location")
    if raw_location is not None and str(raw_location).strip():
        pieces = [piece.strip() for piece in str(raw_location).replace("/", ">").split(">")]
        return tuple(piece for piece in pieces if piece) or ("Unity", "Scene")
    return ("Unity", "Scene")


def _location_label(context: dict[str, Any]) -> str:
    return " > ".join(_location_path(context))


def _agent_name(agent_id: str, context: dict[str, Any]) -> str:
    raw_name = context.get("agent_name")
    if raw_name is not None and str(raw_name).strip():
        return str(raw_name).strip()
    return agent_id


def _required_text(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text


def _action_payload(action: Action) -> UnityActionPayload:
    return UnityActionPayload(
        action_type=str(action.action_type),
        target=action.target,
        content=action.content,
        location=action.location,
        timestamp=action.timestamp,
        metadata=dict(action.metadata),
    )


def _emotion_label(record: UnityRuntimeRecord, agent_id: str) -> str:
    emotion = record.simulator.emotions[agent_id].current
    if emotion.valence >= 0.25:
        return "positive"
    if emotion.valence <= -0.25:
        return "tense"
    return "neutral"


def _branch_flags(record: UnityRuntimeRecord, context: dict[str, Any]) -> list[str]:
    return [
        f"session:{record.session_id}",
        f"agent:{record.agent_id}",
        f"location:{_location_label(context)}",
    ]


__all__ = [
    "UnityRuntimeRecord",
    "UnityRuntimeService",
    "UnitySessionNotFoundError",
]
