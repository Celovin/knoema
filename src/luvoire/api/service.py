"""In-memory simulation management for the Knoema API server."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from knoema.api.schemas import ApiEventConfig, CreateSimulationRequest, SimulationStatus
from knoema.llm import LocalClient
from knoema.simulator import Simulator
from knoema.types import WorldEvent


class SimulationNotFoundError(KeyError):
    """Raised when a simulation ID is missing from the in-memory pool."""


class SimulationStateError(RuntimeError):
    """Raised when an operation is invalid for the simulation lifecycle state."""


@dataclass(slots=True)
class SimulationRecord:
    simulation_id: str
    simulator: Simulator
    duration_days: int
    total_ticks: int
    started_at: datetime
    updated_at: datetime
    status: SimulationStatus = "queued"
    completed_ticks: int = 0
    error: str | None = None
    stream_delay_seconds: float = 0.0
    worker: threading.Thread | None = field(default=None, repr=False, compare=False)
    cancel_requested: threading.Event = field(
        default_factory=threading.Event,
        repr=False,
        compare=False,
    )

    @property
    def agent_count(self) -> int:
        return len(self.simulator.agents)

    @property
    def scheduled_events(self) -> int:
        return len(self.simulator.scheduler)


class SimulationService:
    """Manage simulator instances for REST and WebSocket access."""

    def __init__(self) -> None:
        self._records: dict[str, SimulationRecord] = {}
        self._lock = threading.Lock()

    def create(self, request: CreateSimulationRequest) -> SimulationRecord:
        environment = request.environment.to_domain()
        agents = [agent.to_domain() for agent in request.agents]
        for agent_config in request.agents:
            if agent_config.location_path is not None:
                environment.set_agent_location(agent_config.agent_id, agent_config.location_path)
        simulator = Simulator(
            agents=agents,
            environment=environment,
            tick_duration_minutes=request.runtime.tick_duration_minutes,
            llm=LocalClient(lambda messages: request.local_response),
            language=request.runtime.prompt_language,
        )
        self._schedule_initial_events(simulator, request.events)
        simulation_id = uuid.uuid4().hex
        now = datetime.now(UTC)
        record = SimulationRecord(
            simulation_id=simulation_id,
            simulator=simulator,
            duration_days=request.runtime.duration_days,
            total_ticks=simulator.ticks_for_days(request.runtime.duration_days),
            started_at=now,
            updated_at=now,
            stream_delay_seconds=request.runtime.stream_delay_seconds,
        )
        worker = threading.Thread(
            target=self._run_record,
            args=(record, request.runtime.export_path),
            daemon=True,
            name=f"knoema-sim-{simulation_id}",
        )
        record.worker = worker
        with self._lock:
            self._records[simulation_id] = record
        worker.start()
        return record

    def get(self, simulation_id: str) -> SimulationRecord:
        with self._lock:
            record = self._records.get(simulation_id)
        if record is None:
            raise SimulationNotFoundError(simulation_id)
        return record

    def delete(self, simulation_id: str) -> None:
        with self._lock:
            record = self._records.pop(simulation_id, None)
        if record is None:
            raise SimulationNotFoundError(simulation_id)
        record.cancel_requested.set()
        if record.worker is not None and record.worker.is_alive():
            record.worker.join(timeout=1.0)

    def inject_event(self, simulation_id: str, event: WorldEvent) -> SimulationRecord:
        record = self.get(simulation_id)
        if record.status in {"completed", "failed", "cancelled"}:
            raise SimulationStateError("Simulation is no longer accepting events.")
        record.simulator.scheduler.schedule(event)
        record.updated_at = datetime.now(UTC)
        return record

    def total_simulations(self) -> int:
        with self._lock:
            return len(self._records)

    def active_simulations(self) -> int:
        with self._lock:
            return sum(
                1
                for record in self._records.values()
                if record.status in {"queued", "running"}
            )

    def shutdown(self) -> None:
        with self._lock:
            records = list(self._records.values())
            self._records.clear()
        for record in records:
            record.cancel_requested.set()
        for record in records:
            if record.worker is not None and record.worker.is_alive():
                record.worker.join(timeout=1.0)

    def _run_record(self, record: SimulationRecord, export_path: str | None) -> None:
        record.status = "running"
        record.updated_at = datetime.now(UTC)
        try:
            for tick in range(record.total_ticks):
                if record.cancel_requested.is_set():
                    record.status = "cancelled"
                    record.updated_at = datetime.now(UTC)
                    return
                record.simulator.step(tick)
                record.completed_ticks = tick + 1
                record.updated_at = datetime.now(UTC)
                if record.stream_delay_seconds > 0.0:
                    time.sleep(record.stream_delay_seconds)
            if export_path is not None:
                record.simulator.export_logs(export_path)
            record.status = "completed"
        except Exception as exc:  # pragma: no cover - defensive path
            record.status = "failed"
            record.error = str(exc)
        finally:
            record.updated_at = datetime.now(UTC)

    def _schedule_initial_events(
        self,
        simulator: Simulator,
        events: list[ApiEventConfig],
    ) -> None:
        default_timestamp = simulator.environment.current_time
        default_location = " > ".join(simulator.environment.location_path)
        for event in events:
            simulator.scheduler.schedule(
                event.to_domain(
                    default_timestamp=default_timestamp,
                    default_location=default_location,
                )
            )


__all__ = [
    "SimulationNotFoundError",
    "SimulationRecord",
    "SimulationService",
    "SimulationStateError",
]
