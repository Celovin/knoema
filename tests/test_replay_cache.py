from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from luvoire.core.replay_cache import (
    RecordedResponse,
    ReplayCache,
    ReplayCacheLockError,
    ReplayCacheMiss,
    inspect_replay_cache,
)
from luvoire.llm.gateway import LLMGateway
from luvoire.protocols import Message

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class StaticClient:
    model = "fake-model"
    model_fingerprint = "fake-fp-001"

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        self.calls += 1
        return self.response


class ExplodingClient:
    model = "fake-model"

    def complete(self, messages: Sequence[Message], **kwargs: object) -> str:
        raise AssertionError("live provider must not be called in replay mode")


def test_replay_cache_key_canonicalization_golden() -> None:
    cases = json.loads((FIXTURE_DIR / "replay_cache_keys.json").read_text(encoding="utf-8"))
    cache = ReplayCache(Path("unused.ndmp"), mode="off")

    digests = [
        cache.key(
            model=str(case["model"]),
            prompt=str(case["prompt"]),
            sampling=case["sampling"],
            seed=int(case["seed"]),
        )
        for case in cases
    ]

    assert digests == [case["expected"] for case in cases]
    assert digests[0] == digests[1]


def test_replay_cache_round_trip_preserves_records_and_bytes(tmp_path: Path) -> None:
    cache_path = tmp_path / "responses.ndmp"
    responses: dict[str, RecordedResponse] = {}
    with ReplayCache(cache_path, mode="record") as cache:
        for index in range(3):
            key = cache.key(
                model=f"fake-model-{index}",
                prompt=f"prompt {index}",
                sampling={"temperature": 0.1 * index, "max_tokens": 32},
                seed=index,
            )
            response = _response(index)
            responses[key] = response
            cache.put(key, response)

    original_bytes = cache_path.read_bytes()
    with ReplayCache(cache_path, mode="replay") as cache:
        for key, response in responses.items():
            assert cache.get(key) == response
    assert cache_path.read_bytes() == original_bytes


def test_replay_cache_miss_raises_in_replay_mode(tmp_path: Path) -> None:
    cache_path = tmp_path / "responses.ndmp"
    with ReplayCache(cache_path, mode="record") as cache:
        for index in range(2):
            key = cache.key(
                model="fake-model",
                prompt=f"prompt {index}",
                sampling={"temperature": 0.0},
                seed=index,
            )
            cache.put(key, _response(index))

    with ReplayCache(cache_path, mode="replay") as cache:
        missing_key = cache.key(
            model="fake-model",
            prompt="unrecorded prompt",
            sampling={"temperature": 0.0},
            seed=999,
        )
        with pytest.raises(ReplayCacheMiss):
            cache.get(missing_key)


def test_replay_cache_concurrent_writer_fails_fast(tmp_path: Path) -> None:
    cache_path = tmp_path / "responses.ndmp"
    first = ReplayCache(cache_path, mode="record")
    try:
        with pytest.raises(ReplayCacheLockError, match="already open for recording"):
            ReplayCache(cache_path, mode="record")
    finally:
        first.close()

    ReplayCache(cache_path, mode="record").close()


def test_llm_gateway_records_and_replays_without_live_call(tmp_path: Path) -> None:
    cache_path = tmp_path / "gateway.ndmp"
    messages: list[Message] = [{"role": "user", "content": "same prompt"}]
    client = StaticClient("recorded response")
    with ReplayCache(cache_path, mode="record") as cache:
        gateway = LLMGateway([("fake", client)], replay_cache=cache)
        assert gateway.complete(messages, temperature=0.2, max_tokens=64, seed=7) == "recorded response"
        assert gateway.complete(messages, temperature=0.2, max_tokens=64, seed=7) == "recorded response"

    assert client.calls == 1

    with ReplayCache(cache_path, mode="replay") as cache:
        replay_gateway = LLMGateway([("fake", ExplodingClient())], replay_cache=cache)
        assert (
            replay_gateway.complete(messages, temperature=0.2, max_tokens=64, seed=7)
            == "recorded response"
        )


def test_replay_cache_inspect_summary(tmp_path: Path) -> None:
    cache_path = tmp_path / "summary.ndmp"
    with ReplayCache(cache_path, mode="record") as cache:
        for index in range(3):
            key = cache.key(
                model="fake-model",
                prompt=f"prompt {index}",
                sampling={"temperature": 0.0},
                seed=index,
            )
            cache.put(key, _response(index))

    summary = inspect_replay_cache(cache_path)

    assert summary.record_count == 3
    assert summary.unique_models == ("fake-model",)
    assert summary.first_capture == "2026-04-23T00:00:00Z"
    assert summary.last_capture == "2026-04-23T00:02:00Z"
    assert summary.total_bytes == cache_path.stat().st_size


def _response(index: int) -> RecordedResponse:
    return RecordedResponse(
        text=f"response {index}",
        finish_reason="stop",
        prompt_tokens=10 + index,
        completion_tokens=3 + index,
        model_fingerprint=f"fingerprint-{index}",
        captured_at=datetime(2026, 4, 23, 0, index, tzinfo=UTC),
    )
