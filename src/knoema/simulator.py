"""Main simulation runner."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

from knoema.decision import DecisionEngine
from knoema.emotion import EmotionState
from knoema.environment import Environment
from knoema.events import EventDispatcher, EventScheduler
from knoema.llm import LocalClient
from knoema.memory import ShortTermMemoryBuffer
from knoema.persona import Persona
from knoema.prompts import PromptLanguage
from knoema.protocols import LLMClient
from knoema.relationship import RelationshipGraph
from knoema.types import Action, Memory, WorldEvent


@dataclass(slots=True)
class SimulationLogEntry:
    tick: int
    timestamp: datetime
    agent_id: str
    action: Action

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        payload["action"]["timestamp"] = self.action.timestamp.isoformat()
        return payload


class Simulator:
    """Coordinate agents, environment, scheduled events, and decisions."""

    def __init__(
        self,
        *,
        agents: list[Persona],
        environment: Environment,
        tick_duration_minutes: int = 30,
        start_time: datetime | None = None,
        llm: LLMClient | None = None,
        language: str | PromptLanguage = "en",
    ) -> None:
        if not agents:
            raise ValueError("agents must not be empty")
        if tick_duration_minutes < 1:
            raise ValueError("tick_duration_minutes must be positive")
        self.agents = agents
        self.environment = environment
        if start_time is not None:
            self.environment.current_time = start_time
        self.tick_duration = timedelta(minutes=tick_duration_minutes)
        self.relationships = RelationshipGraph()
        self.emotions = {agent.agent_id: EmotionState() for agent in agents}
        self.short_term_memories = {
            agent.agent_id: ShortTermMemoryBuffer(capacity=50) for agent in agents
        }
        self.scheduler = EventScheduler()
        self.dispatcher = EventDispatcher()
        self.decision_engine = DecisionEngine(
            llm or LocalClient(_default_action_response),
            language=language,
        )
        self.logs: list[SimulationLogEntry] = []
        for agent in agents:
            self.relationships.add_agent(agent.agent_id)

    def run(self, *, duration_days: int) -> list[SimulationLogEntry]:
        if duration_days < 1:
            raise ValueError("duration_days must be positive")
        ticks = int((duration_days * 24 * 60) / (self.tick_duration.total_seconds() / 60))
        for tick in range(ticks):
            self._run_tick(tick)
            self.environment.advance_time(self.tick_duration)
        return list(self.logs)

    def export_logs(self, path: str | Path) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            for entry in self.logs:
                file.write(json.dumps(entry.to_json_dict(), ensure_ascii=False) + "\n")

    def _run_tick(self, tick: int) -> None:
        for event in self.scheduler.due(self.environment.current_time):
            self.environment.record_event(event)
            self.dispatcher.dispatch(event)
        for agent in self.agents:
            action = self._decide_for_agent(agent)
            self._record_action(tick, agent, action)

    def _decide_for_agent(self, agent: Persona) -> Action:
        context = self.environment.get_context(agent.agent_id)
        return self.decision_engine.decide(
            persona=agent,
            memories=self.short_term_memories[agent.agent_id].recent(8),
            relationships=self.relationships.neighbors(agent.agent_id),
            environment=context,
            emotion=self.emotions[agent.agent_id].current,
            trigger=context.recent_events[-1] if context.recent_events else None,
        )

    def _record_action(self, tick: int, agent: Persona, action: Action) -> None:
        self.logs.append(
            SimulationLogEntry(
                tick=tick,
                timestamp=self.environment.current_time,
                agent_id=agent.agent_id,
                action=action,
            )
        )
        event = WorldEvent(
            timestamp=self.environment.current_time,
            event_type=f"agent.{action.action_type}",
            participants=[participant for participant in [agent.agent_id, action.target] if participant],
            location=action.location,
            description=action.content,
        )
        self.environment.record_event(event)
        self.short_term_memories[agent.agent_id].add(
            Memory(
                id=f"mem-{uuid.uuid4().hex}",
                agent_id=agent.agent_id,
                timestamp=self.environment.current_time,
                content=action.content,
                memory_type="episodic",
                importance=0.5,
            )
        )
        if action.target is not None:
            self.relationships.update_after_interaction(agent.agent_id, action.target, action, "neutral")


def _default_action_response(messages: object) -> str:
    return '{"action_type": "wait", "target": null, "content": "observes the situation."}'


__all__ = ["SimulationLogEntry", "Simulator"]
