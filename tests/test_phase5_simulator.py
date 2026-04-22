"""Phase 5 tests for event scheduling and simulation runs."""

from __future__ import annotations

import json
from datetime import datetime

from luvoire import Environment, Persona, Personality, Simulator
from luvoire.events import EventDispatcher, EventScheduler
from luvoire.types import WorldEvent


def _agent(agent_id: str) -> Persona:
    return Persona(
        agent_id=agent_id,
        name=agent_id.title(),
        age=17,
        background="Dormitory student",
        personality=Personality(0.6, 0.6, 0.5, 0.6, 0.4),
        values=["respect"],
        goals=["maintain routine"],
    )


def _environment() -> Environment:
    return Environment(
        start_time=datetime(2026, 3, 2, 9, 0),
        location_path=("Korea", "Seoul", "Dormitory"),
        conditions={"weather": "clear"},
    )


def test_event_dispatcher_calls_specific_and_wildcard_handlers() -> None:
    dispatcher = EventDispatcher()
    seen: list[str] = []
    dispatcher.subscribe("*", lambda event: seen.append(f"*:{event.event_type}"))
    dispatcher.subscribe("alarm", lambda event: seen.append(event.description))
    event = WorldEvent(
        timestamp=datetime(2026, 3, 2, 9, 0),
        event_type="alarm",
        participants=["alice"],
        location="Dorm",
        description="Wake up",
    )

    count = dispatcher.dispatch(event)

    assert count == 2
    assert seen == ["*:alarm", "Wake up"]


def test_event_scheduler_returns_due_events_in_time_order() -> None:
    scheduler = EventScheduler()
    first = WorldEvent(
        timestamp=datetime(2026, 3, 2, 9, 0),
        event_type="first",
        participants=["alice"],
        location="Dorm",
        description="First",
    )
    second = WorldEvent(
        timestamp=datetime(2026, 3, 2, 10, 0),
        event_type="second",
        participants=["alice"],
        location="Dorm",
        description="Second",
    )
    scheduler.schedule(second)
    scheduler.schedule(first)

    due = scheduler.due(datetime(2026, 3, 2, 9, 30))

    assert due == [first]
    assert len(scheduler) == 1


def test_simulator_runs_three_agents_for_seven_days_with_30_minute_ticks() -> None:
    simulator = Simulator(
        agents=[_agent("alice"), _agent("bob"), _agent("charlie")],
        environment=_environment(),
        tick_duration_minutes=30,
    )

    logs = simulator.run(duration_days=7)

    assert len(logs) == 1008
    assert simulator.environment.current_time == datetime(2026, 3, 9, 9, 0)
    assert all(log.action.action_type == "wait" for log in logs)


def test_simulator_export_logs_writes_jsonl(tmp_path) -> None:  # type: ignore[no-untyped-def]
    simulator = Simulator(
        agents=[_agent("alice")],
        environment=_environment(),
        tick_duration_minutes=60,
    )
    simulator.run(duration_days=1)
    output_path = tmp_path / "sim.jsonl"

    simulator.export_logs(output_path)

    lines = output_path.read_text(encoding="utf-8").splitlines()
    first_entry = json.loads(lines[0])
    assert len(lines) == 24
    assert first_entry["agent_id"] == "alice"
    assert first_entry["action"]["action_type"] == "wait"


def test_simulator_dispatches_scheduled_events_before_agent_decisions() -> None:
    simulator = Simulator(
        agents=[_agent("alice")],
        environment=_environment(),
        tick_duration_minutes=30,
    )
    seen: list[str] = []
    simulator.dispatcher.subscribe("announcement", lambda event: seen.append(event.description))
    simulator.scheduler.schedule(
        WorldEvent(
            timestamp=simulator.environment.current_time,
            event_type="announcement",
            participants=["alice"],
            location="Korea > Seoul > Dormitory",
            description="Breakfast starts now.",
        )
    )

    simulator.run(duration_days=1)

    assert seen == ["Breakfast starts now."]
    assert simulator.logs[0].timestamp == datetime(2026, 3, 2, 9, 0)


def test_simulator_rejects_invalid_duration() -> None:
    simulator = Simulator(
        agents=[_agent("alice")],
        environment=_environment(),
    )

    try:
        simulator.run(duration_days=0)
    except ValueError as exc:
        assert "duration_days must be positive" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_simulator_can_override_start_time() -> None:
    simulator = Simulator(
        agents=[_agent("alice")],
        environment=_environment(),
        start_time=datetime(2026, 4, 1, 12, 0),
        tick_duration_minutes=60,
    )

    simulator.run(duration_days=1)

    assert simulator.logs[0].timestamp == datetime(2026, 4, 1, 12, 0)
    assert simulator.environment.current_time == datetime(2026, 4, 2, 12, 0)
