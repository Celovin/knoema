# Hierarchical Planning

Phase 51 adds an opt-in hierarchical task network surface for agents that need multi-step goal pursuit. The default remains `planning=False`, so existing simulations continue to run without planner state.

## Background

Hierarchical Task Network planning decomposes a high-level goal into smaller tasks that can be selected, completed, or replanned. Knoema follows the practical HTN shape associated with Erol, Hendler, and Nau's 1994 work, but keeps the first implementation deterministic and inspectable rather than provider-generated.

## API

```python
from knoema import AgentContext, HierarchicalPlanner, WorldState

planner = HierarchicalPlanner(default_depth=3)
tasks = planner.decompose(
    "complete a paper experiment",
    AgentContext(
        agent_id="researcher",
        location="Lab",
        active_goals=("complete a paper experiment",),
    ),
)
next_task = planner.select_next_task("researcher", WorldState(tick=0))
if next_task is not None:
    planner.update_progress("researcher", next_task)
```

## Persona Opt-in

```python
from knoema import Persona, Personality

persona = Persona(
    agent_id="researcher",
    name="Researcher",
    age=31,
    background="Synthetic researcher preparing an experiment.",
    personality=Personality(0.7, 0.8, 0.4, 0.6, 0.3),
    goals=["complete a paper experiment"],
    planning=True,
)
```

When `planning=True`, `Simulator` decomposes the first active goal and passes the selected task into the decision prompt. The task hint is visible as a `Current hierarchical task` block and does not change the JSON action schema.

## Experiment

`experiments/planning_depth` runs 20 seeds across 2-, 3-, and 4-level hierarchies. The committed summary reports a 0.900 goal achievement rate for the 3-level planner condition and a 0.525 planning-off baseline.

## Limits

The current planner is deterministic and linear by design. It is a runtime contract for explicit goal pursuit, not a complete automated-planning solver. Provider-authored or domain-specific decomposition can be layered behind the same `Task` and `HierarchicalPlanner` API.
