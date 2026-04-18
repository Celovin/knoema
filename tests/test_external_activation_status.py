from __future__ import annotations

from pathlib import Path

from scripts.external_activation_status import CommandResult, collect_external_activation_status


def _command_key(command: list[str]) -> tuple[str, ...]:
    return tuple(command)


def test_external_activation_status_reports_current_blockers(tmp_path: Path) -> None:
    website_dir = tmp_path / "website"
    website_dir.mkdir()

    responses = {
        _command_key(
            [
                "gh",
                "repo",
                "view",
                "Celovin/knoema",
                "--json",
                "name,visibility,isPrivate,defaultBranchRef,url",
            ]
        ): CommandResult(
            exit_code=0,
            stdout=(
                '{"name":"knoema","visibility":"PUBLIC","isPrivate":false,'
                '"defaultBranchRef":{"name":"main"},"url":"https://github.com/Celovin/knoema"}'
            ),
            stderr="",
        ),
        _command_key(
            ["gh", "api", "repos/Celovin/knoema/actions/permissions/workflow"]
        ): CommandResult(
            exit_code=0,
            stdout='{"default_workflow_permissions":"read","can_approve_pull_request_reviews":false}',
            stderr="",
        ),
        _command_key(["gh", "variable", "list", "--repo", "Celovin/knoema"]): CommandResult(
            exit_code=0,
            stdout="",
            stderr="",
        ),
        _command_key(
            ["gh", "release", "list", "--repo", "Celovin/knoema", "--limit", "1"]
        ): CommandResult(
            exit_code=0,
            stdout="Knoema Engine v0.1.0\tLatest\tv0.1.0\t2026-04-18T00:14:14Z\n",
            stderr="",
        ),
        _command_key(["hf", "auth", "whoami"]): CommandResult(
            exit_code=0,
            stdout="\x1b[1muser: \x1b[0m iruhana25\n",
            stderr="",
        ),
        _command_key(["vercel", "whoami"]): CommandResult(exit_code=0, stdout="celovin-team\n", stderr=""),
    }

    def fake_runner(command: list[str], *, cwd: Path | None = None) -> CommandResult:
        del cwd
        return responses[_command_key(command)]

    report = collect_external_activation_status(run_command=fake_runner, repo_root=tmp_path)

    assert report["ready_for_external_activation"] is False
    assert report["repo"]["is_public"] is True
    assert report["deployment"]["hugging_face"]["authenticated_user"] == "iruhana25"
    assert report["deployment"]["vercel"]["website_project_link_exists"] is False
    assert report["github_actions"]["release_please_enabled"] is False
    assert "Repository variable ENABLE_RELEASE_PLEASE is not set." in report["blockers"]


def test_external_activation_status_reports_ready_state_when_all_checks_pass(tmp_path: Path) -> None:
    website_link = tmp_path / "website" / ".vercel"
    website_link.mkdir(parents=True)
    (website_link / "project.json").write_text('{"projectId":"p123"}', encoding="utf-8")

    responses = {
        _command_key(
            [
                "gh",
                "repo",
                "view",
                "Celovin/knoema",
                "--json",
                "name,visibility,isPrivate,defaultBranchRef,url",
            ]
        ): CommandResult(
            exit_code=0,
            stdout=(
                '{"name":"knoema","visibility":"PUBLIC","isPrivate":false,'
                '"defaultBranchRef":{"name":"main"},"url":"https://github.com/Celovin/knoema"}'
            ),
            stderr="",
        ),
        _command_key(
            ["gh", "api", "repos/Celovin/knoema/actions/permissions/workflow"]
        ): CommandResult(
            exit_code=0,
            stdout='{"default_workflow_permissions":"write","can_approve_pull_request_reviews":true}',
            stderr="",
        ),
        _command_key(["gh", "variable", "list", "--repo", "Celovin/knoema"]): CommandResult(
            exit_code=0,
            stdout="ENABLE_RELEASE_PLEASE\t1\t2026-04-18T12:00:00Z\n",
            stderr="",
        ),
        _command_key(
            ["gh", "release", "list", "--repo", "Celovin/knoema", "--limit", "1"]
        ): CommandResult(
            exit_code=0,
            stdout="Knoema Engine v0.1.0\tLatest\tv0.1.0\t2026-04-18T00:14:14Z\n",
            stderr="",
        ),
        _command_key(["hf", "auth", "whoami"]): CommandResult(
            exit_code=0,
            stdout="user: Celovin\n",
            stderr="",
        ),
        _command_key(["vercel", "whoami"]): CommandResult(
            exit_code=0,
            stdout="celovin-production\n",
            stderr="",
        ),
    }

    def fake_runner(command: list[str], *, cwd: Path | None = None) -> CommandResult:
        del cwd
        return responses[_command_key(command)]

    report = collect_external_activation_status(run_command=fake_runner, repo_root=tmp_path)

    assert report["ready_for_external_activation"] is True
    assert report["blockers"] == []
    assert report["deployment"]["hugging_face"]["matches_target_namespace"] is True
    assert report["github_actions"]["default_workflow_permissions"] == "write"
    assert report["github_actions"]["release_please_enabled"] is True
