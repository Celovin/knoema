"""Hierarchical task planning for opt-in goal pursuit."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal

from luvoire.types import AgentID

TaskStatus = Literal["pending", "active", "completed", "failed"]


@dataclass(frozen=True, slots=True)
class WorldState:
    """Minimal inspectable state used by the planner."""

    tick: int = 0
    facts: dict[str, bool] = field(default_factory=dict)
    completed_tasks: frozenset[str] = field(default_factory=frozenset)

    def with_completed(self, task_id: str) -> WorldState:
        return replace(self, completed_tasks=self.completed_tasks | {task_id})


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Goal and local state supplied when decomposing a plan."""

    agent_id: AgentID
    location: str
    active_goals: tuple[str, ...] = ()
    plan_depth: int = 3


def _always_available(_: WorldState) -> bool:
    return True


def _identity_effect(state: WorldState) -> WorldState:
    return state


@dataclass(slots=True)
class Task:
    task_id: str
    description: str
    parent_id: str | None
    children: list[str]
    precondition: Callable[[WorldState], bool] = _always_available
    effect: Callable[[WorldState], WorldState] = _identity_effect
    status: TaskStatus = "pending"
    priority: float = 0.5

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be blank")
        if not self.description.strip():
            raise ValueError("description must not be blank")
        if self.parent_id is not None and not self.parent_id.strip():
            raise ValueError("parent_id must not be blank when provided")
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError("priority must be between 0.0 and 1.0")

    def ready(self, world_state: WorldState, completed_task_ids: set[str]) -> bool:
        parent_ready = self.parent_id is None or self.parent_id in completed_task_ids
        return self.status == "pending" and parent_ready and self.precondition(world_state)


class HierarchicalPlanner:
    """Small HTN-style planner for deterministic agent goals."""

    def __init__(self, *, default_depth: int = 3) -> None:
        if default_depth < 1:
            raise ValueError("default_depth must be positive")
        self.default_depth = default_depth
        self._plans: dict[AgentID, list[Task]] = {}
        self._active_tasks: dict[AgentID, str] = {}

    def decompose(self, goal: str, context: AgentContext) -> list[Task]:
        """Create a linear hierarchy from an agent goal.

        The initial implementation intentionally favors reproducibility over
        generative creativity. Applications can replace these tasks with a
        provider-authored hierarchy while preserving the same planner API.
        """

        if not goal.strip():
            raise ValueError("goal must not be blank")
        depth = max(1, context.plan_depth or self.default_depth)
        labels = _task_labels(goal, depth)
        tasks: list[Task] = []
        for index, description in enumerate(labels):
            task_id = f"{context.agent_id}:goal:{_slug(goal)}:{index + 1}"
            parent_id = tasks[index - 1].task_id if index else None
            task = Task(
                task_id=task_id,
                description=description,
                parent_id=parent_id,
                children=[],
                priority=max(0.1, 1.0 - index * 0.12),
            )
            if tasks:
                tasks[-1].children.append(task.task_id)
            tasks.append(task)
        self._plans[context.agent_id] = tasks
        self._active_tasks.pop(context.agent_id, None)
        return [replace(task, children=list(task.children)) for task in tasks]

    def select_next_task(self, agent_id: str, world_state: WorldState) -> Task | None:
        tasks = self._plans.get(agent_id, [])
        completed = {task.task_id for task in tasks if task.status == "completed"}
        candidates = [task for task in tasks if task.ready(world_state, completed)]
        if not candidates:
            return None
        selected = max(candidates, key=lambda task: task.priority)
        selected.status = "active"
        self._active_tasks[agent_id] = selected.task_id
        return replace(selected, children=list(selected.children))

    def replan_on_failure(self, agent_id: str, failed_task: Task) -> list[Task]:
        tasks = self._plans.setdefault(agent_id, [])
        for task in tasks:
            if task.task_id == failed_task.task_id:
                task.status = "failed"
        recovery = Task(
            task_id=f"{failed_task.task_id}:replan",
            description=f"Recover and retry: {failed_task.description}",
            parent_id=failed_task.parent_id,
            children=[failed_task.task_id],
            priority=min(1.0, failed_task.priority + 0.1),
        )
        tasks.append(recovery)
        self._active_tasks[agent_id] = recovery.task_id
        return [replace(task, children=list(task.children)) for task in tasks]

    def update_progress(self, agent_id: str, completed_task: Task) -> None:
        tasks = self._plans.get(agent_id, [])
        for task in tasks:
            if task.task_id == completed_task.task_id:
                task.status = "completed"
                self._active_tasks.pop(agent_id, None)
                return

    def complete_active_task(self, agent_id: AgentID) -> Task | None:
        active_id = self._active_tasks.get(agent_id)
        if active_id is None:
            return None
        for task in self._plans.get(agent_id, []):
            if task.task_id == active_id:
                task.status = "completed"
                self._active_tasks.pop(agent_id, None)
                return replace(task, children=list(task.children))
        return None

    def plan_for(self, agent_id: AgentID) -> tuple[Task, ...]:
        return tuple(replace(task, children=list(task.children)) for task in self._plans.get(agent_id, []))

    def achievement_rate(self, agent_ids: Sequence[AgentID]) -> float:
        if not agent_ids:
            return 0.0
        completed = 0
        for agent_id in agent_ids:
            tasks = self._plans.get(agent_id, [])
            if tasks and all(task.status == "completed" for task in tasks):
                completed += 1
        return completed / len(agent_ids)


def _task_labels(goal: str, depth: int) -> list[str]:
    templates = [
        "Clarify the success criteria for {goal}",
        "Gather the information and resources needed for {goal}",
        "Execute the next concrete step toward {goal}",
        "Review evidence and close the loop for {goal}",
    ]
    return [templates[index % len(templates)].format(goal=goal) for index in range(depth)]


def _slug(value: str) -> str:
    normalized = "".join(character.lower() if character.isalnum() else "-" for character in value)
    parts = [part for part in normalized.split("-") if part]
    return "-".join(parts[:8]) or "goal"
