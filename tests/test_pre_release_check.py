from __future__ import annotations

from scripts.pre_release_check import run_pre_release_check


def test_pre_release_check_combines_external_status_and_dry_run_results() -> None:
    def fake_status() -> dict[str, object]:
        return {
            "ready_for_external_activation": True,
            "blockers": [],
            "repo": {"is_public": True},
        }

    def fake_dry_run(version: str, keep: bool) -> dict[str, object]:
        assert version == "0.3.0"
        assert keep is False
        return {"status": "ok", "dry_run_version": version}

    result = run_pre_release_check(
        "0.3.0",
        collect_status=fake_status,
        dry_run=fake_dry_run,
    )

    assert result["version"] == "0.3.0"
    assert result["external_activation"]["ready_for_external_activation"] is True
    assert result["release_dry_run"]["status"] == "ok"
    assert result["ready_for_release_tag"] is True


def test_pre_release_check_stays_not_ready_when_external_blockers_exist() -> None:
    def fake_status() -> dict[str, object]:
        return {
            "ready_for_external_activation": False,
            "blockers": ["Repository variable ENABLE_RELEASE_PLEASE is not set."],
            "repo": {"is_public": True},
        }

    def fake_dry_run(version: str, keep: bool) -> dict[str, object]:
        del keep
        return {"status": "ok", "dry_run_version": version}

    result = run_pre_release_check(
        "0.3.0",
        collect_status=fake_status,
        dry_run=fake_dry_run,
    )

    assert result["release_dry_run"]["status"] == "ok"
    assert result["ready_for_release_tag"] is False
    assert result["external_activation"]["blockers"] == [
        "Repository variable ENABLE_RELEASE_PLEASE is not set."
    ]
