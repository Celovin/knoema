from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

HF_NAMESPACE = "celovin"
SPACE_NAME = "knoema-playground"
SPACE_REPO_ID = f"{HF_NAMESPACE}/{SPACE_NAME}"
SPACE_URL = f"https://huggingface.co/spaces/{SPACE_REPO_ID}"
DEFAULT_COMMIT_MESSAGE = "Deploy Knoema Playground"


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


def _repo_namespace(repo_id: str) -> str:
    parts = repo_id.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise SystemExit(f"Invalid Hugging Face Space repository id: {repo_id}")
    return parts[0]


def run_playground_space_deploy(
    *,
    run_command: CommandRunner = _run_command,
    repo_root: Path | None = None,
    repo_id: str = SPACE_REPO_ID,
    commit_message: str = DEFAULT_COMMIT_MESSAGE,
    dry_run: bool = False,
) -> dict[str, object]:
    root = repo_root or _repo_root()
    playground_dir = root / "playground"
    if not playground_dir.exists():
        raise SystemExit(f"Playground directory is missing: {playground_dir}")

    auth_result = run_command(["hf", "auth", "whoami"], cwd=root)
    if auth_result.exit_code != 0:
        detail = auth_result.stderr.strip() or auth_result.stdout.strip() or "unknown error"
        raise SystemExit(f"Hugging Face CLI authentication is unavailable: {detail}")

    authenticated_user = _parse_hf_user(auth_result.stdout)
    if authenticated_user is None:
        raise SystemExit("Hugging Face auth is active but `hf auth whoami` did not report a user.")

    target_namespace = _repo_namespace(repo_id)
    if target_namespace != HF_NAMESPACE:
        raise SystemExit(
            f"Playground deploys must target the {HF_NAMESPACE} namespace; got {repo_id}."
        )

    commands = [
        ["hf", "repo", "create", repo_id, "--repo-type", "space", "--space_sdk", "gradio", "--exist-ok"],
        [
            "hf",
            "upload",
            repo_id,
            ".",
            ".",
            "--repo-type",
            "space",
            "--commit-message",
            commit_message,
        ],
    ]

    if not dry_run:
        for command in commands:
            result = run_command(command, cwd=playground_dir)
            if result.exit_code != 0:
                detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
                raise SystemExit(f"Command failed: {' '.join(command)}\n{detail}")

    return {
        "status": "dry-run" if dry_run else "ok",
        "authenticated_user": authenticated_user,
        "repo_id": repo_id,
        "space_url": f"https://huggingface.co/spaces/{repo_id}",
        "playground_dir": str(playground_dir),
        "commit_message": commit_message,
        "commands": [" ".join(command) for command in commands],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or update the Knoema Hugging Face Space from the playground directory."
    )
    parser.add_argument(
        "--repo-id",
        default=SPACE_REPO_ID,
        help=f"Target Hugging Face Space repository. Default: {SPACE_REPO_ID}.",
    )
    parser.add_argument(
        "--commit-message",
        default=DEFAULT_COMMIT_MESSAGE,
        help=f"Commit message for the upload step. Default: {DEFAULT_COMMIT_MESSAGE!r}.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate authentication and print the planned commands without uploading.",
    )
    args = parser.parse_args()

    result = run_playground_space_deploy(
        repo_id=args.repo_id,
        commit_message=args.commit_message,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        raise SystemExit(str(exc)) from exc
