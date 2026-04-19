"""Main simulation runner."""

from __future__ import annotations

import json
import uuid
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from knoema.cognition import Monologue, MonologueGenerator, SocialLearner
from knoema.decision import DecisionEngine
from knoema.emotion import EmotionState
from knoema.environment import Environment, EnvironmentContext
from knoema.events import EventDispatcher, EventScheduler
from knoema.game import (
    RoutineEntry,
    active_routine_entry,
    apply_faction_action,
    apply_inventory_action,
)
from knoema.llm import LocalClient
from knoema.memory import ShortTermMemoryBuffer, SQLiteFaissMemoryStore
from knoema.persona import Persona
from knoema.planning import AgentContext, HierarchicalPlanner, WorldState
from knoema.prompts import PromptLanguage, normalize_prompt_language
from knoema.protocols import LLMClient
from knoema.relationship import RelationshipGraph
from knoema.theory_of_mind import TheoryOfMindEngine
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
        if not payload["action"].get("metadata"):
            payload["action"].pop("metadata", None)
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
        planning_depth: int = 3,
    ) -> None:
        if not agents:
            raise ValueError("agents must not be empty")
        if tick_duration_minutes < 1:
            raise ValueError("tick_duration_minutes must be positive")
        if planning_depth < 1:
            raise ValueError("planning_depth must be positive")
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
        self.long_term_memories = {
            agent.agent_id: SQLiteFaissMemoryStore(":memory:") for agent in agents
        }
        self.scheduler = EventScheduler()
        self.dispatcher = EventDispatcher()
        self.language = normalize_prompt_language(language)
        resolved_llm = llm or LocalClient(_default_action_response)
        self.decision_engine = DecisionEngine(
            resolved_llm,
            language=self.language,
        )
        self.monologue_generator = MonologueGenerator(
            None if isinstance(resolved_llm, LocalClient) else resolved_llm
        )
        self.theory_of_mind = TheoryOfMindEngine.from_personas(agents)
        self.planner = HierarchicalPlanner(default_depth=planning_depth)
        self.planning_depth = planning_depth
        self.social_learner = SocialLearner()
        self.logs: list[SimulationLogEntry] = []
        self.monologues: list[Monologue] = []
        self.monologue_valence: dict[tuple[str, int], float] = {}
        for agent in agents:
            self.relationships.add_agent(agent.agent_id)
            if agent.planning and agent.goals:
                self.planner.decompose(
                    agent.goals[0],
                    AgentContext(
                        agent_id=agent.agent_id,
                        location=" > ".join(self.environment.location_path),
                        active_goals=tuple(agent.goals),
                        plan_depth=planning_depth,
                    ),
                )

    def run(self, *, duration_days: int) -> list[SimulationLogEntry]:
        if duration_days < 1:
            raise ValueError("duration_days must be positive")
        self.run_ticks(self.ticks_for_days(duration_days))
        return list(self.logs)

    def run_ticks(self, tick_count: int, *, start_tick: int = 0) -> list[SimulationLogEntry]:
        if tick_count < 0:
            raise ValueError("tick_count must not be negative")
        if start_tick < 0:
            raise ValueError("start_tick must not be negative")
        for offset in range(tick_count):
            self.step(start_tick + offset)
        return list(self.logs)

    def step(self, tick: int) -> None:
        if tick < 0:
            raise ValueError("tick must not be negative")
        self._run_tick(tick)
        self.environment.advance_time(self.tick_duration)

    def ticks_for_days(self, duration_days: int) -> int:
        if duration_days < 1:
            raise ValueError("duration_days must be positive")
        return int((duration_days * 24 * 60) / (self.tick_duration.total_seconds() / 60))

    def export_logs(self, path: str | Path) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            for entry in self.logs:
                file.write(json.dumps(entry.to_json_dict(), ensure_ascii=False) + "\n")

    def close(self) -> None:
        stores = getattr(self, "long_term_memories", {})
        for store in stores.values():
            try:
                store.close()
            except Exception:
                continue
        self.long_term_memories = {}

    def __del__(self) -> None:  # pragma: no cover - best-effort cleanup
        with suppress(Exception):
            self.close()

    def _run_tick(self, tick: int) -> None:
        for event in self.scheduler.due(self.environment.current_time):
            self.environment.record_event(event)
            self.dispatcher.dispatch(event)
        for agent in self.agents:
            routine_entry = self._apply_routine(agent)
            context = self.environment.get_context(agent.agent_id)
            if routine_entry is not None:
                context = self._routine_context(context, routine_entry)
            monologue = self.monologue_generator.generate(
                agent,
                context,
                tick=tick,
                language=self.language,
            )
            self._record_monologue(monologue)
            action = self._decide_for_agent(agent, context=context, routine_entry=routine_entry)
            self._record_action(tick, agent, action)

    def _decide_for_agent(
        self,
        agent: Persona,
        *,
        context: EnvironmentContext | None = None,
        routine_entry: RoutineEntry | None = None,
    ) -> Action:
        resolved_context = context or self.environment.get_context(agent.agent_id)
        salient_trigger = self._salient_trigger(resolved_context, agent.agent_id)
        current_task = None
        if agent.planning:
            current_task = self.planner.select_next_task(
                agent.agent_id,
                WorldState(tick=len(self.logs), facts={"planning_enabled": True}),
            )
        if agent.social_learning:
            imitation = self.social_learner.consider_imitation(
                agent.agent_id,
                WorldState(tick=len(self.logs), facts={"social_learning_enabled": True}),
            )
            if imitation is not None:
                return imitation
        if routine_entry is not None and salient_trigger is None:
            return self._routine_default_action(agent, resolved_context, routine_entry)
        return self.decision_engine.decide(
            persona=agent,
            memories=self.short_term_memories[agent.agent_id].recent(8),
            relationships=self.relationships.neighbors(agent.agent_id),
            environment=resolved_context,
            emotion=self.emotions[agent.agent_id].current,
            trigger=salient_trigger,
            theory_of_mind_context=self.theory_of_mind.context_for(agent.agent_id),
            current_task=current_task,
        )

    def _apply_routine(self, agent: Persona) -> RoutineEntry | None:
        routine_entry = active_routine_entry(agent.routine, self.environment.current_time)
        if routine_entry is not None:
            self.environment.set_agent_location(agent.agent_id, routine_entry.location_path)
        return routine_entry

    def _routine_context(
        self,
        context: EnvironmentContext,
        routine_entry: RoutineEntry,
    ) -> EnvironmentContext:
        if self.language == "ko":
            routine_note = (
                f"일과에 따라 현재 위치는 {context.location}이며 기본 행동은 "
                f"{routine_entry.default_action}입니다."
            )
        else:
            routine_note = (
                f"Currently at {context.location} per daily routine. "
                f"Default action: {routine_entry.default_action}."
            )
        return EnvironmentContext(
            agent_id=context.agent_id,
            timestamp=context.timestamp,
            location_path=context.location_path,
            conditions=dict(context.conditions),
            recent_events=list(context.recent_events),
            routine_note=routine_note,
        )

    def _salient_trigger(
        self,
        context: EnvironmentContext,
        agent_id: str,
    ) -> WorldEvent | None:
        for event in reversed(context.recent_events):
            if event.timestamp != context.timestamp:
                continue
            if event.event_type.startswith("agent.") and agent_id not in event.participants:
                continue
            return event
        return None

    def _routine_default_action(
        self,
        agent: Persona,
        context: EnvironmentContext,
        routine_entry: RoutineEntry,
    ) -> Action:
        if self.language == "ko":
            content = f"{agent.name}은 일과에 따라 {context.location}에서 움직인다."
        else:
            content = f"{agent.name} follows the daily routine at {context.location}."
        return Action(
            agent_id=agent.agent_id,
            timestamp=context.timestamp,
            action_type=str(routine_entry.default_action),
            target=routine_entry.default_target,
            content=content,
            location=context.location,
            metadata={
                "routine": True,
                "start_hour": routine_entry.start_hour,
                "end_hour": routine_entry.end_hour,
            },
        )

    def _record_monologue(self, monologue: Monologue) -> None:
        self.monologues.append(monologue)
        self.monologue_valence[(monologue.agent_id, monologue.tick)] = self.emotions[
            monologue.agent_id
        ].current.valence

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
        memory = Memory(
            id=f"mem-{uuid.uuid4().hex}",
            agent_id=agent.agent_id,
            timestamp=self.environment.current_time,
            content=action.content,
            memory_type="episodic",
            importance=0.5,
        )
        self.short_term_memories[agent.agent_id].add(memory)
        self.long_term_memories[agent.agent_id].add(memory)
        agent.inventory = apply_inventory_action(agent.inventory, action)
        agent.factions = apply_faction_action(agent.factions, action)
        if action.target is not None:
            self.relationships.update_after_interaction(agent.agent_id, action.target, action, "neutral")
        self._share_observation(agent, action)
        if agent.planning:
            self.planner.complete_active_task(agent.agent_id)

    def _share_observation(self, actor: Persona, action: Action) -> None:
        outcome: Literal["success", "neutral"] = (
            "success" if action.action_type not in {"observe", "wait"} else "neutral"
        )
        for observer in self.agents:
            if not observer.social_learning or observer.agent_id == actor.agent_id:
                continue
            self.social_learner.observe(
                observer.agent_id,
                actor.agent_id,
                action,
                outcome,
                context=WorldState(tick=len(self.logs), facts={"observed": True}),
                observed_at=self.environment.current_time,
            )


def _default_action_response(messages: object) -> str:
    return '{"action_type": "wait", "target": null, "content": "observes the situation."}'


__all__ = ["SimulationLogEntry", "Simulator"]
