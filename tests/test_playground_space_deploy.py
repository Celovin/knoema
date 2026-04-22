from __future__ import annotations

import sys

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
                stdout="\x1b[1muser: \x1b[0m celovin-ci-bot\n",
                stderr="",
            )
        raise AssertionError(f"Unexpected command: {command}")

    result = run_playground_space_deploy(run_command=fake_runner, repo_root=tmp_path, dry_run=True)

    assert result["authenticated_user"] == "celovin-ci-bot"


def test_playground_space_deploy_rejects_non_celovin_target_namespace(tmp_path) -> None:
    (tmp_path / "playground").mkdir()

    def fake_runner(command: list[str], *, cwd=None):
        del cwd
        if command == ["hf", "auth", "whoami"]:
            from scripts.deploy_playground_space import CommandResult

            return CommandResult(exit_code=0, stdout="user: celovin\n", stderr="")
        raise AssertionError(f"Unexpected command: {command}")

    with pytest.raises(SystemExit, match="must target the celovin namespace"):
        run_playground_space_deploy(
            run_command=fake_runner,
            repo_root=tmp_path,
            repo_id="someone-else/knoema-playground",
            dry_run=True,
        )


def test_playground_space_deploy_runs_create_and_upload_commands(tmp_path) -> None:
    playground_dir = tmp_path / "playground"
    playground_dir.mkdir()
    calls: list[tuple[list[str], object]] = []

    def fake_runner(command: list[str], *, cwd=None):
        from scripts.deploy_playground_space import CommandResult

        calls.append((command, cwd))
        if command == ["hf", "auth", "whoami"]:
            return CommandResult(exit_code=0, stdout="user: celovin\n", stderr="")
        return CommandResult(exit_code=0, stdout="ok\n", stderr="")

    result = run_playground_space_deploy(run_command=fake_runner, repo_root=tmp_path)

    assert result["status"] == "ok"
    assert result["authenticated_user"] == "celovin"
    assert result["commit_message"] == DEFAULT_COMMIT_MESSAGE
    assert result["repo_id"] == "celovin/knoema-playground"
    assert result["space_url"] == "https://huggingface.co/spaces/celovin/knoema-playground"
    assert calls == [
        (["hf", "auth", "whoami"], tmp_path),
        (
            [
                "hf",
                "repo",
                "create",
                "celovin/knoema-playground",
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
                "celovin/knoema-playground",
                ".",
                ".",
                "--repo-type",
                "space",
                "--commit-message",
                DEFAULT_COMMIT_MESSAGE,
            ],
            playground_dir,
        ),
        (
            [
                sys.executable,
                str(tmp_path / "scripts" / "warm_space.py"),
                "--repo-id",
                "celovin/knoema-playground",
            ],
            tmp_path,
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
            return CommandResult(exit_code=0, stdout="user: celovin\n", stderr="")
        raise AssertionError(f"Unexpected command in dry run: {command}")

    result = run_playground_space_deploy(
        run_command=fake_runner,
        repo_root=tmp_path,
        dry_run=True,
    )

    assert result["status"] == "dry-run"
    assert calls == [["hf", "auth", "whoami"]]
    assert "hf repo create celovin/knoema-playground" in result["commands"][0]


def test_playground_space_deploy_ensure_fresh_install_uses_verified_head(tmp_path) -> None:
    playground_dir = tmp_path / "playground"
    playground_dir.mkdir()
    old_sha = "a" * 40
    head_sha = "b" * 40
    requirements = playground_dir / "requirements.txt"
    requirements.write_text(
        f"gradio==5.31.0\n"
        f"knoema-engine @ git+https://github.com/Celovin/knoema.git@{old_sha}\n",
        encoding="utf-8",
    )

    def fake_runner(command: list[str], *, cwd=None):
        from scripts.deploy_playground_space import CommandResult

        assert cwd in {tmp_path, playground_dir}
        if command == ["hf", "auth", "whoami"]:
            return CommandResult(exit_code=0, stdout="user: celovin\n", stderr="")
        if command == ["git", "rev-parse", "HEAD"]:
            return CommandResult(exit_code=0, stdout=f"{head_sha}\n", stderr="")
        if command == ["git", "cat-file", "-e", head_sha]:
            return CommandResult(exit_code=0, stdout="", stderr="")
        raise AssertionError(f"Unexpected command: {command}")

    result = run_playground_space_deploy(
        run_command=fake_runner,
        repo_root=tmp_path,
        dry_run=True,
        ensure_fresh_install=True,
    )

    assert result["head_sha"] == head_sha
    assert result["requirements_rewritten"] is True
    assert requirements.read_text(encoding="utf-8").endswith(f"@{head_sha}\n")


def test_playground_space_deploy_factory_reboots_when_pyproject_changed(tmp_path) -> None:
    playground_dir = tmp_path / "playground"
    playground_dir.mkdir()
    previous_source_sha = "c" * 40
    requirements_text = (
        "gradio==5.31.0\n"
        f"knoema-engine @ git+https://github.com/Celovin/knoema.git@{previous_source_sha}\n"
    )
    (playground_dir / "requirements.txt").write_text(requirements_text, encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = \"new\"\n", encoding="utf-8")
    calls: list[list[str]] = []

    class FakeRepoInfo:
        sha = "space-revision"

    class FakeApi:
        def __init__(self) -> None:
            self.restarted = False

        def repo_info(self, *, repo_id: str, repo_type: str):
            assert repo_id == "celovin/knoema-playground"
            assert repo_type == "space"
            return FakeRepoInfo()

        def restart_space(self, *, repo_id: str, factory_reboot: bool) -> None:
            assert repo_id == "celovin/knoema-playground"
            assert factory_reboot is True
            self.restarted = True

    fake_api = FakeApi()

    def fake_runner(command: list[str], *, cwd=None):
        from scripts.deploy_playground_space import CommandResult

        del cwd
        calls.append(command)
        if command == ["hf", "auth", "whoami"]:
            return CommandResult(exit_code=0, stdout="user: celovin\n", stderr="")
        if command == ["git", "cat-file", "-e", previous_source_sha]:
            return CommandResult(exit_code=0, stdout="", stderr="")
        if command == ["git", "show", f"{previous_source_sha}:pyproject.toml"]:
            return CommandResult(exit_code=0, stdout="[project]\nname = \"old\"\n", stderr="")
        return CommandResult(exit_code=0, stdout="ok\n", stderr="")

    result = run_playground_space_deploy(
        run_command=fake_runner,
        repo_root=tmp_path,
        factory_reboot_on_pyproject_change=True,
        api_factory=lambda: fake_api,
        read_space_file=lambda repo_id, filename, revision=None: requirements_text,
    )

    assert result["factory_rebooted"] is True
    assert fake_api.restarted is True
    assert calls[-1][2:] == ["--repo-id", "celovin/knoema-playground"]
