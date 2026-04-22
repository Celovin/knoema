from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from knoema.api.auth import AuthenticatedTenant
from knoema.api.server import create_app
from knoema.api.tier_rate_limit import TierRateLimiter, enforce_tier_rate_limit
from knoema.billing import api_keys
from knoema.billing.api_keys import APIKeyManager, InMemoryAPIKeyStore
from knoema.billing.gateway import UsageMeter
from knoema.billing.tiers import TierName


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


def _manager_and_headers(tier: TierName) -> tuple[APIKeyManager, str, dict[str, str]]:
    manager = APIKeyManager(InMemoryAPIKeyStore())
    key_id, token = manager.issue("tenant-commercial-test", "llm:invoke", tier=tier)
    return manager, key_id, {"Authorization": f"Bearer {token}"}


def test_api_commercial_auth_missing_returns_401() -> None:
    manager, _key_id, _headers = _manager_and_headers("pro")
    with TestClient(create_app(api_key_manager=manager)) as client:
        response = client.post("/simulations/run", json=_simulation_payload())

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_api_commercial_valid_pro_tier_sets_response_header() -> None:
    manager, _key_id, headers = _manager_and_headers("pro")
    with TestClient(create_app(api_key_manager=manager)) as client:
        response = client.post("/simulations/run", json=_simulation_payload(), headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Knoema-Tenant-Tier"] == "pro"
    assert response.json()["simulation_id"]


def test_api_commercial_free_tier_cannot_use_pro_model() -> None:
    manager, _key_id, headers = _manager_and_headers("free")
    with TestClient(create_app(api_key_manager=manager)) as client:
        response = client.post(
            "/simulations/run?model=gpt-4o",
            json=_simulation_payload(),
            headers=headers,
        )

    assert response.status_code == 402
    assert "Upgrade tier" in response.json()["detail"]


def test_api_commercial_rate_limit_returns_retry_headers() -> None:
    manager, _key_id, headers = _manager_and_headers("pro")
    app = FastAPI()
    app.state.api_key_manager = manager
    app.state.tier_rate_limiter = TierRateLimiter(time_fn=lambda: 100.0)

    @app.get("/limited")
    def limited_route(
        tenant: Annotated[AuthenticatedTenant, Depends(enforce_tier_rate_limit)],
    ) -> dict[str, str]:
        return {"tenant_id": tenant.tenant_id}

    with TestClient(app) as client:
        responses = [client.get("/limited", headers=headers) for _ in range(241)]

    assert [response.status_code for response in responses[:240]] == [200] * 240
    assert responses[240].status_code == 429
    assert responses[240].headers["Retry-After"]
    assert responses[240].headers["X-Knoema-RateLimit-Tier"] == "pro"
    assert responses[240].headers["X-Knoema-RateLimit-Remaining"] == "0"


def test_api_commercial_usage_middleware_writes_one_jsonl_line(tmp_path: Path) -> None:
    manager, _key_id, headers = _manager_and_headers("pro")
    meter = UsageMeter(tmp_path)
    with TestClient(create_app(api_key_manager=manager, usage_meter=meter)) as client:
        response = client.post("/simulations/run", json=_simulation_payload(), headers=headers)

    assert response.status_code == 200
    usage_files = sorted(tmp_path.glob("usage_*.jsonl"))
    assert len(usage_files) == 1
    lines = usage_files[0].read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert sorted(payload) == [
        "cost_usd",
        "input_tokens",
        "model",
        "output_tokens",
        "recorded_at",
        "tenant_id",
        "tier",
    ]
    assert payload["tenant_id"] == "tenant-commercial-test"
    assert payload["tier"] == "pro"


def test_api_commercial_revoked_key_returns_401() -> None:
    manager, key_id, headers = _manager_and_headers("pro")
    assert manager.revoke(key_id) is True

    with TestClient(create_app(api_key_manager=manager)) as client:
        response = client.post("/simulations/run", json=_simulation_payload(), headers=headers)

    assert response.status_code == 401


def test_api_commercial_invalid_token_still_uses_constant_time_compare(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []
    original = api_keys.constant_time_equals

    def compare(left: str, right: str) -> bool:
        calls.append((left, right))
        return original(left, right)

    monkeypatch.setattr(api_keys, "constant_time_equals", compare)
    manager, _key_id, _headers = _manager_and_headers("pro")

    with TestClient(create_app(api_key_manager=manager)) as client:
        response = client.post(
            "/simulations/run",
            json=_simulation_payload(),
            headers={"Authorization": "Bearer knoema_missing_bad-secret"},
        )

    assert response.status_code == 401
    assert calls
