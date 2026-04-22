from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import requests
from huggingface_hub import HfApi

DEFAULT_REPO_ID = "celovin/knoema-playground"
DEFAULT_TIMEOUT_SECONDS = 600
DEFAULT_POLL_INTERVAL_SECONDS = 10
ERROR_STAGES = {"RUNTIME_ERROR", "BUILD_ERROR"}
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


class ResponseLike(Protocol):
    status_code: int
    text: str


class RequestGet(Protocol):
    def __call__(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: int,
    ) -> ResponseLike: ...


@dataclass(frozen=True, slots=True)
class WarmSpaceResult:
    repo_id: str
    stage: str
    http_status: int
    transition_history: tuple[str, ...]


class WarmSpaceError(RuntimeError):
    pass


def _space_url(repo_id: str) -> str:
    return f"https://huggingface.co/spaces/{repo_id}"


def _run_logs_url(repo_id: str) -> str:
    return f"https://huggingface.co/api/spaces/{repo_id}/logs/run"


def _runtime_stage(space_info: object) -> str:
    runtime = getattr(space_info, "runtime", None)
    stage = runtime.get("stage") if isinstance(runtime, dict) else getattr(runtime, "stage", None)
    return str(stage or "UNKNOWN")


def _auth_headers() -> dict[str, str] | None:
    token = os.environ.get("HF_TOKEN")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def fetch_run_log_tail(
    repo_id: str,
    *,
    request_get: RequestGet = requests.get,
    line_count: int = 50,
) -> str:
    response = request_get(_run_logs_url(repo_id), headers=_auth_headers(), timeout=30)
    if response.status_code != 200:
        return f"Could not fetch run logs: HTTP {response.status_code}"
    lines = response.text.splitlines()
    return "\n".join(lines[-line_count:])


def warm_space(
    repo_id: str = DEFAULT_REPO_ID,
    *,
    api: HfApi | None = None,
    request_get: RequestGet = requests.get,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS,
) -> WarmSpaceResult:
    hf_api = api or HfApi()
    deadline = monotonic() + timeout_seconds
    transition_history: list[str] = []
    last_stage = "UNKNOWN"

    while monotonic() <= deadline:
        last_stage = _runtime_stage(hf_api.space_info(repo_id))
        if not transition_history or transition_history[-1] != last_stage:
            transition_history.append(last_stage)

        if last_stage == "RUNNING":
            response = request_get(_space_url(repo_id), headers=None, timeout=30)
            if response.status_code != 200:
                raise WarmSpaceError(
                    f"{repo_id} reached RUNNING but root URL returned HTTP {response.status_code}"
                )
            return WarmSpaceResult(
                repo_id=repo_id,
                stage=last_stage,
                http_status=response.status_code,
                transition_history=tuple(transition_history),
            )

        if last_stage in ERROR_STAGES:
            logs = fetch_run_log_tail(repo_id, request_get=request_get)
            raise WarmSpaceError(f"{repo_id} reached {last_stage}.\nLast run log lines:\n{logs}")

        sleep(poll_interval_seconds)

    history = " -> ".join(transition_history) if transition_history else "none"
    raise WarmSpaceError(
        f"{repo_id} did not reach RUNNING within {timeout_seconds}s; "
        f"last stage={last_stage}; transitions={history}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Wait for a Hugging Face Space to become RUNNING.")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID, help=f"Space repo id. Default: {DEFAULT_REPO_ID}.")
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Hard timeout. Default: {DEFAULT_TIMEOUT_SECONDS}.",
    )
    args = parser.parse_args()

    try:
        result = warm_space(repo_id=args.repo_id, timeout_seconds=args.timeout_seconds)
    except WarmSpaceError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(EXIT_FAILURE) from exc

    print(
        f"{result.repo_id} warmed: stage={result.stage}, "
        f"http={result.http_status}, transitions={' -> '.join(result.transition_history)}"
    )
    raise SystemExit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
