from __future__ import annotations

import importlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

from luvoire import CachedLLMClient, Environment, Persona, Personality, Simulator
from luvoire.protocols import Message

playground_simulation = importlib.import_module("playground.simulation")


class CountingClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0
        self.lock = threading.Lock()

    def complete(self, messages: list[Message], **kwargs: object) -> str:
        with self.lock:
            self.calls += 1
        time.sleep(0.05)
        return self.response


class ConcurrencyTrackingClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0
        self.active = 0
        self.max_active = 0
        self.lock = threading.Lock()

    def complete(self, messages: list[Message], **kwargs: object) -> str:
        with self.lock:
            self.calls += 1
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(0.05)
            return self.response
        finally:
            with self.lock:
                self.active -= 1


def _personas(count: int = 3) -> list[Persona]:
    return [
        Persona(
            agent_id=f"agent_{index + 1}",
            name=f"Agent {index + 1}",
            age=24 + index,
            background="Synthetic participant",
            personality=Personality(0.5, 0.5, 0.5, 0.5, 0.5),
            values=["stability"],
            goals=["finish the shift"],
        )
        for index in range(count)
    ]


def _environment() -> Environment:
    return Environment(
        start_time=datetime(2026, 4, 18, 9, 0),
        location_path=("City", "Office", "Break Room"),
        conditions={"weather": "rain"},
    )


def test_subtask30_cached_llm_client_deduplicates_concurrent_identical_prompts() -> None:
    underlying = CountingClient("cached-response")
    client = CachedLLMClient(underlying)
    messages: list[Message] = [{"role": "user", "content": "same prompt"}]

    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda _: client.complete(messages, temperature=0.2), range(4)))

    assert responses == ["cached-response"] * 4
    assert underlying.calls == 1
    stats = client.cache_stats()
    assert stats.hits == 3
    assert stats.misses == 1
    assert stats.entries == 1


def test_subtask30_parallel_simulator_overlaps_llm_calls_within_tick() -> None:
    tracking = ConcurrencyTrackingClient(
        '{"action_type":"observe","target":null,"content":"notes the room."}'
    )
    simulator = Simulator(
        agents=_personas(),
        environment=_environment(),
        llm=CachedLLMClient(tracking),
        parallel_decisions=True,
    )

    simulator.run_ticks(1)

    assert tracking.max_active >= 2
    assert len(simulator.logs) == 3
    assert all(entry.action.action_type == "observe" for entry in simulator.logs)


def test_subtask30_playground_result_exposes_parallel_llm_runtime(monkeypatch) -> None:
    class FakeOpenAIClient:
        def __init__(self, *, model: str, api_key: str | None = None) -> None:
            self.model = model
            self.api_key = api_key

        def complete(self, messages: list[Message], **kwargs: object) -> str:
            return '{"action_type":"observe","target":null,"content":"tracks the room."}'

    monkeypatch.setattr(playground_simulation, "OpenAIClient", FakeOpenAIClient)

    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        provider="OpenAI",
        api_key="demo-key",
        model="fake-model",
        primary_name="Mina",
        primary_age=24,
        openness=0.5,
        conscientiousness=0.5,
        extraversion=0.5,
        agreeableness=0.5,
        neuroticism=0.5,
        ticks=1,
        language="en",
    )

    assert result.parallel_llm_enabled is True
    assert result.llm_cache_stats is not None
    assert result.llm_cache_stats.misses > 0
