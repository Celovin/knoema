from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from huggingface_hub import HfApi, hf_hub_download

HF_NAMESPACE = "celovin"
SPACE_NAME = "knoema-playground"
SPACE_REPO_ID = f"{HF_NAMESPACE}/{SPACE_NAME}"
SPACE_URL = f"https://huggingface.co/spaces/{SPACE_REPO_ID}"
DEFAULT_COMMIT_MESSAGE = "Deploy Knoema Playground"
KNOEMA_REQUIREMENT_PATTERN = re.compile(
    r"^knoema-engine\s*@\s*git\+https://github\.com/Celovin/knoema\.git@[0-9a-fA-F]{7,40}\s*$",
    re.MULTILINE,
)
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


class CommandRunner(Protocol):
    def __call__(self, command: list[str], *, cwd: Path | None = None) -> CommandResult: ...


class SpaceFileReader(Protocol):
    def __call__(self, repo_id: str, filename: str, revision: str | None = None) -> str | None: ...


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


def _current_verified_head_sha(run_command: CommandRunner, root: Path) -> str:
    result = run_command(["git", "rev-parse", "HEAD"], cwd=root)
    if result.exit_code != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise SystemExit(f"Could not read git HEAD SHA with git rev-parse HEAD: {detail}")
    sha = result.stdout.strip()
    if not GIT_SHA_PATTERN.fullmatch(sha):
        raise SystemExit(f"git rev-parse HEAD returned an invalid SHA: {sha!r}")
    verify = run_command(["git", "cat-file", "-e", sha], cwd=root)
    if verify.exit_code != 0:
        detail = verify.stderr.strip() or verify.stdout.strip() or "unknown error"
        raise SystemExit(f"Could not verify git HEAD SHA with git cat-file -e: {detail}")
    return sha


def _rewrite_requirements_pin(root: Path, sha: str) -> bool:
    requirements_path = root / "playground" / "requirements.txt"
    text = requirements_path.read_text(encoding="utf-8")
    pinned_line = f"knoema-engine @ git+https://github.com/Celovin/knoema.git@{sha}"
    updated, replacements = KNOEMA_REQUIREMENT_PATTERN.subn(pinned_line, text, count=1)
    if replacements != 1:
        raise SystemExit(
            "Could not rewrite playground/requirements.txt: missing knoema-engine git pin."
        )
    if text.endswith("\n") and not updated.endswith("\n"):
        updated += "\n"
    if updated == text:
        return False
    requirements_path.write_text(updated, encoding="utf-8", newline="")
    return True


def _read_space_file(repo_id: str, filename: str, revision: str | None = None) -> str | None:
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="space",
            revision=revision,
        )
    except Exception:
        return None
    return Path(path).read_text(encoding="utf-8")


def _space_revision(api: HfApi, repo_id: str) -> str | None:
    try:
        info = api.repo_info(repo_id=repo_id, repo_type="space")
    except Exception:
        return None
    sha = getattr(info, "sha", None)
    return str(sha) if sha else None


def _pinned_source_sha(requirements_text: str | None) -> str | None:
    if requirements_text is None:
        return None
    match = KNOEMA_REQUIREMENT_PATTERN.search(requirements_text)
    if match is None:
        return None
    return match.group(0).rsplit("@", 1)[-1]


def _git_show_text(
    run_command: CommandRunner,
    root: Path,
    *,
    revision: str,
    path: str,
) -> str | None:
    if not GIT_SHA_PATTERN.fullmatch(revision):
        return None
    verify = run_command(["git", "cat-file", "-e", revision], cwd=root)
    if verify.exit_code != 0:
        return None
    result = run_command(["git", "show", f"{revision}:{path}"], cwd=root)
    if result.exit_code != 0:
        return None
    return result.stdout


def _factory_reboot_needed(
    *,
    root: Path,
    repo_id: str,
    previous_space_revision: str | None,
    run_command: CommandRunner,
    read_space_file: SpaceFileReader,
) -> bool:
    remote_requirements = read_space_file(repo_id, "requirements.txt", previous_space_revision)
    local_requirements = (root / "playground" / "requirements.txt").read_text(encoding="utf-8")
    if remote_requirements != local_requirements:
        return True

    previous_source_sha = _pinned_source_sha(remote_requirements)
    previous_pyproject = (
        _git_show_text(run_command, root, revision=previous_source_sha, path="pyproject.toml")
        if previous_source_sha
        else None
    )
    local_pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    return previous_pyproject != local_pyproject


def run_playground_space_deploy(
    *,
    run_command: CommandRunner = _run_command,
    repo_root: Path | None = None,
    repo_id: str = SPACE_REPO_ID,
    commit_message: str = DEFAULT_COMMIT_MESSAGE,
    dry_run: bool = False,
    ensure_fresh_install: bool = False,
    factory_reboot_on_pyproject_change: bool = False,
    api_factory: Callable[[], HfApi] = HfApi,
    read_space_file: SpaceFileReader = _read_space_file,
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

    head_sha: str | None = None
    requirements_rewritten = False
    if ensure_fresh_install:
        head_sha = _current_verified_head_sha(run_command, root)
        requirements_rewritten = _rewrite_requirements_pin(root, head_sha)

    warm_command = [sys.executable, str(root / "scripts" / "warm_space.py"), "--repo-id", repo_id]
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
        warm_command,
    ]

    factory_rebooted = False
    if not dry_run:
        api = api_factory() if factory_reboot_on_pyproject_change else None
        previous_space_revision = _space_revision(api, repo_id) if api is not None else None
        upload_commands = commands[:-1]
        for command in upload_commands:
            result = run_command(command, cwd=playground_dir)
            if result.exit_code != 0:
                detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
                raise SystemExit(f"Command failed: {' '.join(command)}\n{detail}")
        if api is not None and _factory_reboot_needed(
            root=root,
            repo_id=repo_id,
            previous_space_revision=previous_space_revision,
            run_command=run_command,
            read_space_file=read_space_file,
        ):
            api.restart_space(repo_id=repo_id, factory_reboot=True)
            factory_rebooted = True
        warm_result = run_command(warm_command, cwd=root)
        if warm_result.exit_code != 0:
            detail = warm_result.stderr.strip() or warm_result.stdout.strip() or "unknown error"
            raise SystemExit(f"Space warmup failed: {' '.join(warm_command)}\n{detail}")

    return {
        "status": "dry-run" if dry_run else "ok",
        "authenticated_user": authenticated_user,
        "repo_id": repo_id,
        "space_url": f"https://huggingface.co/spaces/{repo_id}",
        "playground_dir": str(playground_dir),
        "commit_message": commit_message,
        "ensure_fresh_install": ensure_fresh_install,
        "factory_reboot_on_pyproject_change": factory_reboot_on_pyproject_change,
        "factory_rebooted": factory_rebooted,
        "head_sha": head_sha,
        "requirements_rewritten": requirements_rewritten,
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
    parser.add_argument(
        "--ensure-fresh-install",
        action="store_true",
        help="Pin playground/requirements.txt to the verified current git HEAD before uploading.",
    )
    parser.add_argument(
        "--factory-reboot-on-pyproject-change",
        action="store_true",
        help="Factory reboot the Space when dependency metadata changed since the previous Space snapshot.",
    )
    args = parser.parse_args()

    result = run_playground_space_deploy(
        repo_id=args.repo_id,
        commit_message=args.commit_message,
        dry_run=args.dry_run,
        ensure_fresh_install=args.ensure_fresh_install,
        factory_reboot_on_pyproject_change=args.factory_reboot_on_pyproject_change,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        raise SystemExit(str(exc)) from exc
