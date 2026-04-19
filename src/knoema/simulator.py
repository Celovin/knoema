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


@dataclass(frozen=True, slots=True)
class RoutineConflict:
    resource_id: str
    queue: tuple[str, ...]
    position: int
    queue_size: int

    @property
    def holder_agent_id(self) -> str:
        return self.queue[0]

    @property
    def previous_agent_id(self) -> str | None:
        if self.position <= 1:
            return None
        return self.queue[self.position - 2]

    @property
    def next_agent_id(self) -> str | None:
        if self.position >= self.queue_size:
            return None
        return self.queue[self.position]


def _shared_resource_id(location_path: tuple[str, ...]) -> str | None:
    leaf = location_path[-1].strip().lower()
    if not leaf:
        return None
    if any(token in leaf for token in ("kitchen", "bar", "register", "counter", "desk")):
        return leaf.replace(" ", "_")
    return None


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
        routine_entries = {agent.agent_id: self._apply_routine(agent) for agent in self.agents}
        routine_conflicts = self._routine_conflicts(routine_entries)
        for agent in self.agents:
            routine_entry = routine_entries[agent.agent_id]
            routine_conflict = routine_conflicts.get(agent.agent_id)
            context = self.environment.get_context(agent.agent_id)
            if routine_entry is not None:
                context = self._routine_context_with_conflict(
                    context,
                    routine_entry,
                    routine_conflict=routine_conflict,
                )
            monologue = self.monologue_generator.generate(
                agent,
                context,
                tick=tick,
                language=self.language,
            )
            self._record_monologue(monologue)
            action = self._decide_for_agent(
                agent,
                context=context,
                routine_entry=routine_entry,
                routine_conflict=routine_conflict,
            )
            self._record_action(tick, agent, action)

    def _decide_for_agent(
        self,
        agent: Persona,
        *,
        context: EnvironmentContext | None = None,
        routine_entry: RoutineEntry | None = None,
        routine_conflict: RoutineConflict | None = None,
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
        if routine_entry is not None and routine_conflict is not None:
            return self._routine_conflict_action(
                agent,
                resolved_context,
                routine_entry,
                routine_conflict,
            )
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

    def _routine_conflicts(
        self,
        routine_entries: dict[str, RoutineEntry | None],
    ) -> dict[str, RoutineConflict]:
        grouped: dict[tuple[tuple[str, ...], str], list[Persona]] = {}
        for agent in self.agents:
            routine_entry = routine_entries.get(agent.agent_id)
            if routine_entry is None:
                continue
            resource_id = _shared_resource_id(routine_entry.location_path)
            if resource_id is None:
                continue
            grouped.setdefault((routine_entry.location_path, resource_id), []).append(agent)

        conflicts: dict[str, RoutineConflict] = {}
        for (_, resource_id), contenders in grouped.items():
            if len(contenders) < 2:
                continue
            ordered = tuple(
                agent.agent_id
                for agent in sorted(
                    contenders,
                    key=lambda contender: (
                        -contender.personality.conscientiousness,
                        -contender.age,
                        contender.agent_id,
                    ),
                )
            )
            for position, agent_id in enumerate(ordered, start=1):
                conflicts[agent_id] = RoutineConflict(
                    resource_id=resource_id,
                    queue=ordered,
                    position=position,
                    queue_size=len(ordered),
                )
        return conflicts

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

    def _routine_context_with_conflict(
        self,
        context: EnvironmentContext,
        routine_entry: RoutineEntry,
        *,
        routine_conflict: RoutineConflict | None = None,
    ) -> EnvironmentContext:
        base_context = self._routine_context(context, routine_entry)
        if routine_conflict is None:
            return base_context
        conditions = dict(base_context.conditions)
        conditions["resource_queue"] = {
            "resource_id": routine_conflict.resource_id,
            "queue": list(routine_conflict.queue),
            "position": routine_conflict.position,
            "queue_size": routine_conflict.queue_size,
        }
        if self.language == "ko":
            if routine_conflict.position == 1:
                next_agent = routine_conflict.next_agent_id or "다음 대기자"
                routine_note = (
                    f"{base_context.routine_note} 공유 자원 {routine_conflict.resource_id}의 선두로 "
                    f"먼저 사용하고 {next_agent}에게 순서를 넘길 준비를 하세요."
                )
            else:
                routine_note = (
                    f"{base_context.routine_note} 공유 자원 {routine_conflict.resource_id}의 대기열 "
                    f"{routine_conflict.position}/{routine_conflict.queue_size}번입니다. "
                    f"앞사람과 사용 순서를 조율하세요."
                )
        else:
            if routine_conflict.position == 1:
                next_agent = routine_conflict.next_agent_id or "the next person in line"
                routine_note = (
                    f"{base_context.routine_note} You are first in the queue for the shared "
                    f"{routine_conflict.resource_id}; use it and coordinate a handoff to {next_agent}."
                )
            else:
                routine_note = (
                    f"{base_context.routine_note} You are position {routine_conflict.position}/"
                    f"{routine_conflict.queue_size} for the shared {routine_conflict.resource_id}; "
                    "negotiate the order instead of colliding."
                )
        return EnvironmentContext(
            agent_id=base_context.agent_id,
            timestamp=base_context.timestamp,
            location_path=base_context.location_path,
            conditions=conditions,
            recent_events=list(base_context.recent_events),
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

    def _routine_conflict_action(
        self,
        agent: Persona,
        context: EnvironmentContext,
        routine_entry: RoutineEntry,
        routine_conflict: RoutineConflict,
    ) -> Action:
        shared_resource = routine_conflict.resource_id.replace("_", " ")
        if routine_conflict.position == 1:
            base_action = self._routine_default_action(agent, context, routine_entry)
            metadata = dict(base_action.metadata)
            metadata.update(
                {
                    "queue_position": routine_conflict.position,
                    "queue_size": routine_conflict.queue_size,
                    "shared_resource": routine_conflict.resource_id,
                    "queue_role": "holder",
                    "queue_order": list(routine_conflict.queue),
                }
            )
            if self.language == "ko":
                content = (
                    f"{agent.name}이(가) 공유 {shared_resource}를 먼저 사용하고 "
                    f"{routine_conflict.next_agent_id or '다음 대기자'}에게 순서를 넘길 준비를 한다."
                )
            else:
                content = (
                    f"{agent.name} takes the shared {shared_resource} first and prepares a handoff "
                    f"to {routine_conflict.next_agent_id or 'the next person in line'}."
                )
            return Action(
                agent_id=base_action.agent_id,
                timestamp=base_action.timestamp,
                action_type=base_action.action_type,
                target=base_action.target,
                content=content,
                location=base_action.location,
                metadata=metadata,
            )

        counterpart = routine_conflict.previous_agent_id or routine_conflict.holder_agent_id
        if self.language == "ko":
            content = (
                f"{agent.name}이(가) {counterpart} 뒤에서 공유 {shared_resource} 대기열 "
                f"{routine_conflict.position}/{routine_conflict.queue_size}번을 지키며 사용 순서를 조율한다."
            )
        else:
            content = (
                f"{agent.name} waits behind {counterpart} in the shared {shared_resource} queue "
                f"({routine_conflict.position}/{routine_conflict.queue_size}) and negotiates the handoff."
            )
        return Action(
            agent_id=agent.agent_id,
            timestamp=context.timestamp,
            action_type="speak",
            target=counterpart,
            content=content,
            location=context.location,
            metadata={
                "routine": True,
                "queue_position": routine_conflict.position,
                "queue_size": routine_conflict.queue_size,
                "shared_resource": routine_conflict.resource_id,
                "queue_role": "waiting",
                "queue_order": list(routine_conflict.queue),
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
