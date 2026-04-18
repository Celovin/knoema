from __future__ import annotations

import pytest

from scripts.deploy_playground_space import DEFAULT_COMMIT_MESSAGE, run_playground_space_deploy


def test_playground_space_deploy_requires_celovin_namespace(tmp_path) -> None:
    (tmp_path / "playground").mkdir()

    def fake_runner(command: list[str], *, cwd=None):
        del cwd
        if command == ["hf", "auth", "whoami"]:
            from scripts.deploy_playground_space import CommandResult

            return CommandResult(
                exit_code=0,
                stdout="\x1b[1muser: \x1b[0m iruhana25\n",
                stderr="",
            )
        raise AssertionError(f"Unexpected command: {command}")

    with pytest.raises(SystemExit, match="Hugging Face auth must resolve to Celovin"):
        run_playground_space_deploy(run_command=fake_runner, repo_root=tmp_path)


def test_playground_space_deploy_runs_create_and_upload_commands(tmp_path) -> None:
    playground_dir = tmp_path / "playground"
    playground_dir.mkdir()
    calls: list[tuple[list[str], object]] = []

    def fake_runner(command: list[str], *, cwd=None):
        from scripts.deploy_playground_space import CommandResult

        calls.append((command, cwd))
        if command == ["hf", "auth", "whoami"]:
            return CommandResult(exit_code=0, stdout="user: Celovin\n", stderr="")
        return CommandResult(exit_code=0, stdout="ok\n", stderr="")

    result = run_playground_space_deploy(run_command=fake_runner, repo_root=tmp_path)

    assert result["status"] == "ok"
    assert result["authenticated_user"] == "Celovin"
    assert result["commit_message"] == DEFAULT_COMMIT_MESSAGE
    assert result["repo_id"] == "Celovin/knoema-playground"
    assert result["space_url"] == "https://huggingface.co/spaces/Celovin/knoema-playground"
    assert calls == [
        (["hf", "auth", "whoami"], tmp_path),
        (
            [
                "hf",
                "repo",
                "create",
                "Celovin/knoema-playground",
                "--repo-type",
                "space",
                "--space_sdk",
                "gradio",
                "--exist-ok",
            ],
            playground_dir,
        ),
        (
            [
                "hf",
                "upload",
                "Celovin/knoema-playground",
                ".",
                ".",
                "--repo-type",
                "space",
                "--commit-message",
                DEFAULT_COMMIT_MESSAGE,
            ],
            playground_dir,
        ),
    ]


def test_playground_space_deploy_dry_run_skips_repo_mutation(tmp_path) -> None:
    (tmp_path / "playground").mkdir()
    calls: list[list[str]] = []

    def fake_runner(command: list[str], *, cwd=None):
        from scripts.deploy_playground_space import CommandResult

        del cwd
        calls.append(command)
        if command == ["hf", "auth", "whoami"]:
            return CommandResult(exit_code=0, stdout="user: Celovin\n", stderr="")
        raise AssertionError(f"Unexpected command in dry run: {command}")

    result = run_playground_space_deploy(
        run_command=fake_runner,
        repo_root=tmp_path,
        dry_run=True,
    )

    assert result["status"] == "dry-run"
    assert calls == [["hf", "auth", "whoami"]]
    assert "hf repo create Celovin/knoema-playground" in result["commands"][0]
