from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from huggingface_hub import HfApi

DEFAULT_SPACE_ID = "celovin/luvoire-playground"
DEFAULT_GITHUB_REPO = "Celovin/luvoire"
DEFAULT_BRANCH = "main"
DEFAULT_OUTPUT_PATH = Path("site-snapshot/status.json")
REPLAY_SHA256 = {
    "demo/replay/replay_100agents_gangnam_7pm.msgpack": "8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab",
    "demo/replay/replay_1000agents_gangnam_7pm.msgpack": "0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b",
    "demo/replay/replay_5000agents_gangnam_7pm.msgpack": "d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01",
    "demo/replay/replay_10000agents_gangnam_7pm.msgpack": "af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2",
    "demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack": "9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9",
}


@dataclass(frozen=True, slots=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def __call__(
        self,
        command: list[str],
        *,
        environment: Mapping[str, str] | None = None,
    ) -> CommandResult: ...


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _runtime_stage(space_info: object) -> str:
    runtime = getattr(space_info, "runtime", None)
    stage = runtime.get("stage") if isinstance(runtime, dict) else getattr(runtime, "stage", None)
    return str(stage or "UNKNOWN")


def _run_command(
    command: list[str],
    *,
    environment: Mapping[str, str] | None = None,
) -> CommandResult:
    env = os.environ.copy()
    if environment is not None:
        env.update(environment)
    if "GITHUB_TOKEN" in env and "GH_TOKEN" not in env:
        env["GH_TOKEN"] = env["GITHUB_TOKEN"]

    resolved = list(command)
    if resolved:
        executable = shutil.which(resolved[0])
        if executable is not None:
            resolved[0] = executable

    try:
        completed = subprocess.run(
            resolved,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        return CommandResult(exit_code=127, stdout="", stderr=str(exc))
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _github_api_url(repo: str, branch: str) -> str:
    return f"https://api.github.com/repos/{repo}/actions/runs?branch={branch}&per_page=10"


def _github_deploy_api_url(repo: str, branch: str) -> str:
    return (
        f"https://api.github.com/repos/{repo}/actions/workflows/"
        f"deploy-hf-space.yml/runs?branch={branch}&per_page=1"
    )


def _load_public_json(url: str, environment: Mapping[str, str]) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "luvoire-status-page",
    }
    token = environment.get("GITHUB_TOKEN") or environment.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        return {"workflow_runs": [], "error": "GitHub API response was not an object"}
    return payload


def _load_actions_with_public_fallback(
    *,
    repo: str,
    branch: str,
    run_command: CommandRunner,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    result = run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/actions/runs",
            "-F",
            f"branch={branch}",
            "-F",
            "per_page=10",
        ],
        environment=environment,
    )
    if result.exit_code == 0 and result.stdout.strip():
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            return payload

    try:
        payload = _load_public_json(_github_api_url(repo, branch), environment)
    except urllib.error.URLError as exc:
        return {
            "workflow_runs": [],
            "error": f"Could not fetch GitHub Actions runs: {exc}",
        }
    return payload


def _load_latest_deploy_with_public_fallback(
    *,
    repo: str,
    branch: str,
    run_command: CommandRunner,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    result = run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/actions/workflows/deploy-hf-space.yml/runs",
            "-F",
            f"branch={branch}",
            "-F",
            "per_page=1",
        ],
        environment=environment,
    )
    if result.exit_code == 0 and result.stdout.strip():
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            return payload

    try:
        payload = _load_public_json(_github_deploy_api_url(repo, branch), environment)
    except urllib.error.URLError as exc:
        return {
            "workflow_runs": [],
            "error": f"Could not fetch deploy workflow runs: {exc}",
        }
    return payload


def _normalize_run(run: Mapping[str, Any]) -> dict[str, Any]:
    run_id = run.get("database_id") or run.get("id")
    return {
        "id": run_id,
        "name": str(run.get("name") or run.get("display_title") or "unknown"),
        "path": str(run.get("path") or ""),
        "status": str(run.get("status") or "unknown"),
        "conclusion": run.get("conclusion"),
        "event": str(run.get("event") or ""),
        "head_branch": str(run.get("head_branch") or ""),
        "created_at": str(run.get("created_at") or ""),
        "updated_at": str(run.get("updated_at") or ""),
        "html_url": str(run.get("html_url") or ""),
    }


def _sort_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(run: dict[str, Any]) -> tuple[str, int]:
        run_id = run["id"] if isinstance(run["id"], int) else 0
        return str(run["created_at"]), run_id

    return sorted(runs, key=key, reverse=True)[:10]


def _last_deploy_time(runs: list[dict[str, Any]]) -> str | None:
    for run in runs:
        deploy_surface = f"{run['name']} {run['path']}".lower()
        if "deploy" in deploy_surface:
            return str(run["updated_at"] or run["created_at"] or "") or None
    return None


def _last_deploy_time_from_payload(payload: Mapping[str, Any]) -> str | None:
    raw_runs = payload.get("workflow_runs", [])
    if not isinstance(raw_runs, list) or not raw_runs:
        return None
    first = raw_runs[0]
    if not isinstance(first, dict):
        return None
    updated = first.get("updated_at") or first.get("created_at")
    return str(updated) if updated else None


def _replay_artifact_status(root: Path) -> dict[str, Any]:
    artifacts: list[dict[str, Any]] = []
    verified = True
    for relative_path, expected_sha in sorted(REPLAY_SHA256.items()):
        path = root / relative_path
        if path.exists():
            import hashlib

            actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            matches = actual_sha == expected_sha
        else:
            actual_sha = None
            matches = False
        verified = verified and matches
        artifacts.append(
            {
                "path": relative_path,
                "sha256": expected_sha,
                "current_sha256": actual_sha,
                "matches": matches,
            }
        )
    return {
        "verified": verified,
        "count": len(artifacts),
        "artifacts": artifacts,
    }


def collect_status(
    *,
    space_id: str = DEFAULT_SPACE_ID,
    github_repo: str = DEFAULT_GITHUB_REPO,
    branch: str = DEFAULT_BRANCH,
    api: HfApi | None = None,
    run_command: CommandRunner = _run_command,
    environment: Mapping[str, str] | None = None,
    now: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    env = os.environ if environment is None else environment
    repo_root = root or Path(__file__).resolve().parents[1]
    hf_api = api or HfApi()
    actions_payload = _load_actions_with_public_fallback(
        repo=github_repo,
        branch=branch,
        run_command=run_command,
        environment=env,
    )
    deploy_payload = _load_latest_deploy_with_public_fallback(
        repo=github_repo,
        branch=branch,
        run_command=run_command,
        environment=env,
    )
    raw_runs = actions_payload.get("workflow_runs", [])
    if not isinstance(raw_runs, list):
        raw_runs = []
    runs = _sort_runs([_normalize_run(run) for run in raw_runs if isinstance(run, dict)])

    return {
        "schema_version": 1,
        "generated_at": now or _utc_now(),
        "space": {
            "repo_id": space_id,
            "stage": _runtime_stage(hf_api.space_info(space_id)),
        },
        "github_actions": {
            "repo": github_repo,
            "branch": branch,
            "last_deploy_time": _last_deploy_time_from_payload(deploy_payload)
            or _last_deploy_time(runs),
            "runs": runs,
            "source": "gh api" if "error" not in actions_payload else "public fallback",
            "error": actions_payload.get("error"),
        },
        "replay_artifacts": _replay_artifact_status(repo_root),
    }


def write_status(status: Mapping[str, Any], output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public Luvoire status signals.")
    parser.add_argument("--space-id", default=DEFAULT_SPACE_ID)
    parser.add_argument("--github-repo", default=DEFAULT_GITHUB_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    status = collect_status(
        space_id=args.space_id,
        github_repo=args.github_repo,
        branch=args.branch,
    )
    write_status(status, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
