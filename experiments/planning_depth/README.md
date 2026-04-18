# Planning Depth Experiment

Phase 51 evaluates the opt-in hierarchical planner with deterministic goal-pursuit proxies.

```powershell
.venv\Scripts\python experiments\planning_depth\run.py
```

The experiment runs 20 seeds across 2-, 3-, and 4-level task hierarchies. It compares the planner-enabled proxy against a planning-off baseline and writes `results/summary.json`.
