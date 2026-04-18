from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

OWNER = "Celovin"
REPO = "knoema"
FULL_REPO = f"{OWNER}/{REPO}"
TARGET_SPACE = f"{OWNER}/knoema-playground"


@dataclass(frozen=True, slots=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def __call__(self, command: list[str], *, cwd: Path | None = None) -> CommandResult: ...


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_command(command: list[str], *, cwd: Path | None = None) -> CommandResult:
    env = os.environ.copy()
    if command and command[0] == "gh":
        env.pop("GITHUB_TOKEN", None)
        env.pop("GH_TOKEN", None)
        env.pop("GIT_ASKPASS", None)
    if command[:3] == ["hf", "auth", "whoami"]:
        env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
    except FileNotFoundError as exc:
        return CommandResult(exit_code=127, stdout="", stderr=str(exc))
    return CommandResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _parse_hf_user(output: str) -> str | None:
    cleaned = _strip_ansi(output)
    match = re.search(r"user:\s*([^\s]+)", cleaned)
    if match is not None:
        return match.group(1)
    stripped = cleaned.strip()
    return stripped or None


def _parse_latest_release(output: str) -> dict[str, str] | None:
    stripped = output.strip()
    if not stripped:
        return None
    columns = [column for column in stripped.split("\t") if column]
    if len(columns) < 4:
        return {"raw": stripped}
    return {
        "title": columns[0],
        "status": columns[1],
        "tag": columns[2],
        "published_at": columns[3],
    }


def _parse_variable_names(output: str) -> list[str]:
    names: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        names.append(stripped.split()[0])
    return names


def _load_json(result: CommandResult) -> dict[str, Any] | None:
    if result.exit_code != 0:
        return None
    payload = result.stdout.strip()
    if not payload:
        return None
    return json.loads(payload)


def collect_external_activation_status(
    *,
    run_command: CommandRunner = _run_command,
    repo_root: Path | None = None,
) -> dict[str, object]:
    root = repo_root or _repo_root()
    website_project_link = root / "website" / ".vercel" / "project.json"

    repo_view = _load_json(
        run_command(
            [
                "gh",
                "repo",
                "view",
                FULL_REPO,
                "--json",
                "name,visibility,isPrivate,defaultBranchRef,url",
            ]
        )
    )
    workflow_permissions = _load_json(
        run_command(["gh", "api", f"repos/{FULL_REPO}/actions/permissions/workflow"])
    )
    variables_result = run_command(["gh", "variable", "list", "--repo", FULL_REPO])
    release_result = run_command(["gh", "release", "list", "--repo", FULL_REPO, "--limit", "1"])
    hf_result = run_command(["hf", "auth", "whoami"], cwd=root)
    vercel_result = run_command(["vercel", "whoami"], cwd=root / "website")

    repo_status = {
        "name": repo_view.get("name") if repo_view is not None else None,
        "url": repo_view.get("url") if repo_view is not None else None,
        "visibility": repo_view.get("visibility") if repo_view is not None else None,
        "is_public": repo_view is not None and repo_view.get("isPrivate") is False,
        "default_branch": (
            repo_view.get("defaultBranchRef", {}).get("name") if repo_view is not None else None
        ),
        "latest_release": _parse_latest_release(release_result.stdout),
    }

    hf_user = _parse_hf_user(hf_result.stdout) if hf_result.exit_code == 0 else None
    vercel_identity = vercel_result.stdout.strip() or None
    variable_names = _parse_variable_names(variables_result.stdout)

    github_actions_status = {
        "default_workflow_permissions": (
            workflow_permissions.get("default_workflow_permissions")
            if workflow_permissions is not None
            else None
        ),
        "can_approve_pull_request_reviews": (
            workflow_permissions.get("can_approve_pull_request_reviews")
            if workflow_permissions is not None
            else None
        ),
        "release_please_enabled": "ENABLE_RELEASE_PLEASE" in variable_names,
        "repository_variables": variable_names,
    }

    deployment_status = {
        "hugging_face": {
            "authenticated_user": hf_user,
            "matches_target_namespace": hf_user == OWNER,
            "target_space": TARGET_SPACE,
        },
        "vercel": {
            "whoami": vercel_identity,
            "website_project_link_exists": website_project_link.exists(),
        },
    }

    blockers: list[str] = []
    if not repo_status["is_public"]:
        blockers.append("GitHub repository is not public.")
    if hf_user != OWNER:
        blockers.append("Hugging Face local auth is not using the Celovin namespace.")
    if not website_project_link.exists():
        blockers.append("website/.vercel/project.json is missing, so production deploy is not linked.")
    if github_actions_status["default_workflow_permissions"] != "write":
        blockers.append("GitHub Actions default workflow permissions are not set to write.")
    if not github_actions_status["release_please_enabled"]:
        blockers.append("Repository variable ENABLE_RELEASE_PLEASE is not set.")
    if repo_status["latest_release"] is None:
        blockers.append("No GitHub release is visible yet.")

    return {
        "repo": repo_status,
        "deployment": deployment_status,
        "github_actions": github_actions_status,
        "ready_for_external_activation": blockers == [],
        "blockers": blockers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report current external activation readiness for Knoema."
    )
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="Exit with status 1 when any external activation blocker is present.",
    )
    args = parser.parse_args()

    report = collect_external_activation_status()
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    if args.fail_on_blockers and not report["ready_for_external_activation"]:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        raise SystemExit(str(exc)) from exc
