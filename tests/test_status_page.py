from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from scripts.build_status_page import build_status_page
from scripts.compute_uptime import write_uptime
from scripts.fetch_status import CommandResult, collect_status, write_status


class FakeHfApi:
    def space_info(self, repo_id: str) -> object:
        assert repo_id == "celovin/knoema-playground"
        return SimpleNamespace(runtime=SimpleNamespace(stage="RUNNING"))


def _fake_gh_api(command: list[str], *, environment: object | None = None) -> CommandResult:
    assert command[:2] == ["gh", "api"]
    if "repos/Celovin/knoema/actions/workflows/deploy-hf-space.yml/runs" in command:
        payload: dict[str, Any] = {
            "workflow_runs": [
                {
                    "database_id": 2,
                    "name": "Deploy Hugging Face Space",
                    "path": ".github/workflows/deploy-hf-space.yml",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "head_branch": "main",
                    "created_at": "2026-04-22T08:00:00Z",
                    "updated_at": "2026-04-22T08:03:00Z",
                    "html_url": "https://github.com/Celovin/knoema/actions/runs/2",
                }
            ]
        }
        return CommandResult(0, json.dumps(payload), "")
    assert "repos/Celovin/knoema/actions/runs" in command
    payload = {
        "workflow_runs": [
            {
                "database_id": 2,
                "name": "Deploy Hugging Face Space",
                "path": ".github/workflows/deploy-hf-space.yml",
                "status": "completed",
                "conclusion": "success",
                "event": "push",
                "head_branch": "main",
                "created_at": "2026-04-22T08:00:00Z",
                "updated_at": "2026-04-22T08:03:00Z",
                "html_url": "https://github.com/Celovin/knoema/actions/runs/2",
            },
            {
                "database_id": 1,
                "name": "CI",
                "path": ".github/workflows/ci.yml",
                "status": "completed",
                "conclusion": "success",
                "event": "push",
                "head_branch": "main",
                "created_at": "2026-04-22T07:00:00Z",
                "updated_at": "2026-04-22T07:02:00Z",
                "html_url": "https://github.com/Celovin/knoema/actions/runs/1",
            },
        ]
    }
    return CommandResult(0, json.dumps(payload), "")


def test_fetch_status_schema_with_mocked_hf_and_gh_api() -> None:
    status = collect_status(
        api=FakeHfApi(),  # type: ignore[arg-type]
        run_command=_fake_gh_api,
        now="2026-04-22T09:00:00Z",
    )

    assert status["schema_version"] == 1
    assert status["space"] == {
        "repo_id": "celovin/knoema-playground",
        "stage": "RUNNING",
    }
    assert status["github_actions"]["last_deploy_time"] == "2026-04-22T08:03:00Z"
    assert len(status["github_actions"]["runs"]) == 2
    assert status["github_actions"]["runs"][0]["name"] == "Deploy Hugging Face Space"
    assert status["replay_artifacts"]["verified"] is True
    assert status["replay_artifacts"]["count"] == 5


def test_status_page_builds_badges_and_history(tmp_path: Path) -> None:
    status = collect_status(
        api=FakeHfApi(),  # type: ignore[arg-type]
        run_command=_fake_gh_api,
        now="2026-04-22T09:00:00Z",
    )
    status_path = tmp_path / "status.json"
    history_path = tmp_path / "status-history.jsonl"
    uptime_path = tmp_path / "uptime.json"
    output_path = tmp_path / "status.html"

    write_status(status, status_path)
    build_status_page(
        status_path=status_path,
        history_path=history_path,
        uptime_path=uptime_path,
        output_path=output_path,
    )
    write_uptime(history_path, uptime_path)
    build_status_page(
        status_path=status_path,
        history_path=history_path,
        uptime_path=uptime_path,
        output_path=output_path,
        append=False,
    )

    html = output_path.read_text(encoding="utf-8")
    history = history_path.read_text(encoding="utf-8")

    assert "HF Space" in html
    assert "RUNNING" in html
    assert "CI" in html
    assert "Replay artifacts" in html
    assert "Rolling uptime" in html
    assert "insufficient data" in html
    assert "30-day history" in html
    assert "Last updated 2026-04-22T09:00:00Z" in html
    assert '"space_stage": "RUNNING"' in history
    assert len(history.splitlines()) == 1
