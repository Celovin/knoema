from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from knoema.api.server import create_app
from knoema.billing.gateway import LLMGateway, UsageMeter
from knoema.cli import main


class MockLiteLLM:
    def __call__(self, **kwargs: object) -> dict[str, object]:
        return {
            "choices": [{"message": {"content": "mock completion"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8},
            "cost_usd": "0.0100",
        }


def _extract_token(output: str) -> str:
    match = re.search(r"Bearer (knoema_[^ ]+)", output)
    assert match is not None
    return match.group(1)


def _extract_key_id(output: str) -> str:
    match = re.search(r"API key id: (ak[0-9a-f]+)", output)
    assert match is not None
    return match.group(1)


def _simulation_payload() -> dict[str, object]:
    return {
        "runtime": {
            "duration_days": 1,
            "tick_duration_minutes": 1440,
            "prompt_language": "en",
        },
        "environment": {
            "start_time": "2026-04-19T09:00:00",
            "location_path": ["Korea", "Seoul", "Campus"],
            "conditions": {"weather": "clear"},
        },
        "agents": [
            {
                "agent_id": "agent-0",
                "name": "Agent 0",
                "age": 24,
                "background": "Synthetic participant.",
                "personality": {
                    "openness": 0.5,
                    "conscientiousness": 0.6,
                    "extraversion": 0.4,
                    "agreeableness": 0.7,
                    "neuroticism": 0.3,
                },
                "values": ["clarity"],
                "goals": ["cooperate"],
            }
        ],
        "local_response": '{"action_type": "wait", "target": null, "content": "waits."}',
    }


def test_customer_cli_create_rejects_duplicate_and_invalid_tier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    ok = main(
        [
            "customer",
            "create",
            "--tenant-id",
            "tenant-cli",
            "--tier",
            "pro",
            "--display-name",
            "CLI Tenant",
        ]
    )
    first_output = capsys.readouterr().out
    duplicate = main(
        [
            "customer",
            "create",
            "--tenant-id",
            "tenant-cli",
            "--tier",
            "pro",
            "--display-name",
            "CLI Tenant",
        ]
    )
    invalid = main(
        [
            "customer",
            "create",
            "--tenant-id",
            "bad-tier",
            "--tier",
            "invalid",
            "--display-name",
            "Bad Tier",
        ]
    )

    assert ok == 0
    assert duplicate == 3
    assert invalid == 2
    token = _extract_token(first_output)
    assert first_output.count(token) == 1
    registry_text = Path("var/billing/tenants.json").read_text(encoding="utf-8")
    audit_text = Path("var/audit/commercial.jsonl").read_text(encoding="utf-8")
    assert token not in registry_text
    assert token.split("_", 2)[2] not in registry_text
    assert token not in audit_text
    assert token.split("_", 2)[2] not in audit_text


def test_customer_cli_lifecycle_and_usage_table(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    assert (
        main(
            [
                "customer",
                "create",
                "--tenant-id",
                "tenant-cli",
                "--tier",
                "pro",
                "--display-name",
                "CLI Tenant",
            ]
        )
        == 0
    )
    create_output = capsys.readouterr().out
    first_key_id = _extract_key_id(create_output)
    first_token = _extract_token(create_output)
    with TestClient(create_app()) as client:
        api_response = client.post(
            "/simulations/run?model=gpt-4o",
            json=_simulation_payload(),
            headers={"Authorization": f"Bearer {first_token}"},
        )

    assert api_response.status_code == 200
    assert api_response.headers["X-Knoema-Tenant-Tier"] == "pro"
    assert (
        main(
            [
                "customer",
                "issue-key",
                "--tenant-id",
                "tenant-cli",
            ]
        )
        == 0
    )
    issue_output = capsys.readouterr().out
    issued_token = _extract_token(issue_output)
    gateway = LLMGateway(UsageMeter(Path("var/billing")), completion_client=MockLiteLLM())
    response = gateway.complete(
        tenant_id="tenant-cli",
        tier="pro",
        api_key_source="pass_through",
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "hello"}],
    )
    month = datetime.now(UTC).strftime("%Y-%m")

    assert response.ok is True
    assert main(["customer", "show-usage", "--tenant-id", "tenant-cli", "--month", month]) == 0
    usage_output = capsys.readouterr().out
    assert "gpt-5.4-mini\t12\t8\t0.013000" in usage_output
    assert "TOTAL\t\t\t0.013000" in usage_output
    assert main(["customer", "rotate-key", "--tenant-id", "tenant-cli", "--api-key-id", first_key_id]) == 0
    rotate_output = capsys.readouterr().out
    rotated_key_id = _extract_key_id(rotate_output)
    rotated_token = _extract_token(rotate_output)
    assert main(
        [
            "customer",
            "revoke-key",
            "--tenant-id",
            "tenant-cli",
            "--api-key-id",
            rotated_key_id,
            "--reason",
            "test-cleanup",
        ]
    ) == 0
    _ = capsys.readouterr()
    assert main(["customer", "list"]) == 0
    list_output = capsys.readouterr().out

    assert "tenant-cli\tpro\t3\tCLI Tenant" in list_output
    registry = json.loads(Path("var/billing/tenants.json").read_text(encoding="utf-8"))
    registry_text = json.dumps(registry, sort_keys=True)
    for token in (first_token, issued_token, rotated_token):
        assert token not in registry_text
        assert token.split("_", 2)[2] not in registry_text
        assert token not in list_output
