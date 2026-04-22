from __future__ import annotations

from dataclasses import dataclass

import pytest

from scripts.warm_space import WarmSpaceError, warm_space


@dataclass(slots=True)
class Runtime:
    stage: str


@dataclass(slots=True)
class SpaceInfo:
    runtime: Runtime


@dataclass(slots=True)
class Response:
    status_code: int
    text: str = ""


class FakeApi:
    def __init__(self, stages: list[str]) -> None:
        self.stages = stages
        self.calls = 0

    def space_info(self, repo_id: str) -> SpaceInfo:
        assert repo_id == "celovin/luvoire-playground"
        index = min(self.calls, len(self.stages) - 1)
        self.calls += 1
        return SpaceInfo(runtime=Runtime(stage=self.stages[index]))


def test_warm_space_polls_until_running_and_hits_root_url() -> None:
    requested_urls: list[str] = []

    def fake_get(url: str, *, headers=None, timeout: int) -> Response:
        del headers
        assert timeout == 30
        requested_urls.append(url)
        return Response(status_code=200)

    result = warm_space(
        api=FakeApi(["BUILDING", "APP_STARTING", "RUNNING"]),
        request_get=fake_get,
        sleep=lambda _: None,
    )

    assert result.stage == "RUNNING"
    assert result.http_status == 200
    assert result.transition_history == ("BUILDING", "APP_STARTING", "RUNNING")
    assert requested_urls == ["https://huggingface.co/spaces/celovin/luvoire-playground"]


@pytest.mark.parametrize("terminal_stage", ["RUNTIME_ERROR", "BUILD_ERROR"])
def test_warm_space_prints_last_logs_for_error_terminal_states(terminal_stage: str) -> None:
    requested_urls: list[str] = []
    log_lines = "\n".join(f"line {index}" for index in range(60))

    def fake_get(url: str, *, headers=None, timeout: int) -> Response:
        del headers
        assert timeout == 30
        requested_urls.append(url)
        return Response(status_code=200, text=log_lines)

    with pytest.raises(WarmSpaceError) as exc_info:
        warm_space(
            api=FakeApi(["BUILDING", terminal_stage]),
            request_get=fake_get,
            sleep=lambda _: None,
        )

    message = str(exc_info.value)
    assert terminal_stage in message
    assert "line 10" in message
    assert "line 9" not in message
    assert requested_urls == ["https://huggingface.co/api/spaces/celovin/luvoire-playground/logs/run"]


def test_warm_space_timeout_reports_last_stage_and_transition_history() -> None:
    ticks = iter([0.0, 0.0, 0.2])

    with pytest.raises(WarmSpaceError) as exc_info:
        warm_space(
            api=FakeApi(["BUILDING", "APP_STARTING", "APP_STARTING"]),
            request_get=lambda url, *, headers=None, timeout=30: Response(status_code=200),
            sleep=lambda _: None,
            monotonic=lambda: next(ticks),
            timeout_seconds=0,
        )

    message = str(exc_info.value)
    assert "did not reach RUNNING" in message
    assert "last stage=BUILDING" in message
    assert "transitions=BUILDING" in message
