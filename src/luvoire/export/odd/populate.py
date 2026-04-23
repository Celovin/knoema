"""Populate ODD protocol sections from Luvoire simulation state."""

from __future__ import annotations

from luvoire.dsl import Scenario
from luvoire.export.odd.odd_schema import TODO_STUB, OddReport
from luvoire.simulator import Simulator
from luvoire.types import PERSONALITY_FIELDS


def populate_from_simulation(sim: Simulator, scenario: Scenario) -> OddReport:
    """Fill machine-derivable ODD fields from a Luvoire `Simulator` and `Scenario`."""

    run_ticks = sim.ticks_for_days(scenario.duration_days)
    llm = sim.decision_engine.llm
    llm_model = getattr(llm, "model", type(llm).__name__)
    llm_fingerprint = getattr(llm, "model_fingerprint", None) or "not recorded"
    agent_lines = [
        f"- {agent.name} (`{agent.agent_id}`), age {agent.age}, synthetic={spec.synthetic}"
        for agent, spec in zip(sim.agents, scenario.agents, strict=True)
    ]
    event_lines = [
        f"- {event.timestamp.isoformat()}: {event.event_type} at {event.location}"
        for event in scenario.events
    ]
    metric_lines = [
        f"- {metric.name} ({metric.kind}): {metric.description}"
        for metric in scenario.metrics
    ]

    return OddReport(
        purpose_and_patterns=TODO_STUB,
        entities_state_variables_scales="\n".join(
            [
                f"- Model: {scenario.title} (`{scenario.scenario_id}`)",
                f"- Domain: {scenario.domain}",
                f"- Agents: {len(scenario.agents)}",
                *agent_lines,
                f"- Environment scale: {' > '.join(scenario.environment.location_path)}",
                f"- Tick duration: {scenario.tick_duration_minutes} minutes",
                f"- State variables: {', '.join(PERSONALITY_FIELDS)}, location, emotion, short-term memory, long-term memory, relationship weights, inventory, faction scores",
            ]
        ),
        process_overview_and_scheduling="\n".join(
            [
                "- Scheduler: Luvoire sequential tick loop; Mesa wrapper uses `AgentSet.shuffle_do(\"step\")` for adapter stepping.",
                f"- RNG seed: {scenario.seed}",
                f"- Run duration: {scenario.duration_days} day(s), {run_ticks} tick(s)",
                f"- LLM model: {llm_model}",
                f"- LLM fingerprint: {llm_fingerprint}",
                "- LLM calls, when configured, flow through `luvoire.llm.gateway`; the ODD exporter itself makes no LLM calls.",
            ]
        ),
        design_concepts=TODO_STUB,
        initialization="\n".join(
            [
                f"- Start time: {scenario.environment.start_time.isoformat()}",
                f"- Initial location path: {' > '.join(scenario.environment.location_path)}",
                f"- Conditions: {dict(scenario.environment.conditions)}",
                f"- Initial scheduled events: {len(scenario.events)}",
            ]
        ),
        input_data="\n".join(
            [
                f"- Scenario ID: {scenario.scenario_id}",
                f"- Scenario title: {scenario.title}",
                f"- Scenario description: {scenario.description}",
                f"- Events: {len(scenario.events)}",
                *(event_lines or ["- Events: none"]),
                f"- Metrics: {len(scenario.metrics)}",
                *(metric_lines or ["- Metrics: none"]),
            ]
        ),
        submodels="\n".join(
            [
                "- Decision parsing: strict JSON action schema via `DecisionEngine`.",
                "- Environment update: scheduled events and agent actions append world events.",
                "- Memory update: each action writes episodic short-term and long-term memories.",
                "- Relationship update: targeted interactions update trust and familiarity weights.",
                "- Optional cognition: theory-of-mind, hierarchical planning, routines, and social learning run only when enabled on personas.",
            ]
        ),
    )


__all__ = ["populate_from_simulation"]
