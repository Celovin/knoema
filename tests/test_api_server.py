from __future__ import annotations

import time

from fastapi.testclient import TestClient

from knoema.api.rate_limit import RateLimiter
from knoema.api.server import create_app
from knoema.billing.api_keys import APIKeyManager, InMemoryAPIKeyStore
from knoema.billing.tiers import TierName


def _simulation_payload(*, stream_delay_seconds: float = 0.0) -> dict[str, object]:
    return {
        "runtime": {
            "duration_days": 1,
            "tick_duration_minutes": 120,
            "prompt_language": "en",
            "stream_delay_seconds": stream_delay_seconds,
        },
        "environment": {
            "start_time": "2026-04-19T09:00:00",
            "location_path": ["Korea", "Seoul", "Campus", "Commons"],
            "conditions": {"weather": "clear"},
        },
        "agents": [
            {
                "agent_id": f"agent-{index}",
                "name": f"Agent {index}",
                "age": 20 + index,
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
                "theory_of_mind": {"enabled": index == 0},
            }
            for index in range(5)
        ],
        "local_response": '{"action_type": "speak", "target": null, "content": "shares a brief status update."}',
    }


def _app_and_headers(tier: TierName = "pro") -> tuple[object, dict[str, str]]:
    manager = APIKeyManager(InMemoryAPIKeyStore())
    _key_id, token = manager.issue("tenant-api-test", "llm:invoke", tier=tier)
    return create_app(api_key_manager=manager), {"Authorization": f"Bearer {token}"}


def _wait_for_completion(client: TestClient, simulation_id: str) -> dict[str, object]:
    for _ in range(200):
        response = client.get(f"/simulations/{simulation_id}")
        payload = response.json()
        if payload["status"] == "completed":
            return payload
        time.sleep(0.01)
    raise AssertionError("simulation did not complete in time")


def test_api_healthz_reports_ok() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_openapi_lists_simulation_routes() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/simulations" in paths
    assert "/simulations/{simulation_id}" in paths
    assert "/simulations/{simulation_id}/agents" in paths


def test_api_create_simulation_returns_status_payload() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        response = client.post("/simulations", json=_simulation_payload(), headers=headers)
    assert response.status_code == 201
    payload = response.json()
    assert payload["simulation_id"]
    assert payload["agent_count"] == 5
    assert payload["total_ticks"] == 12


def test_api_simulation_status_reaches_completed_state() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        created = client.post("/simulations", json=_simulation_payload(), headers=headers).json()
        payload = _wait_for_completion(client, created["simulation_id"])
    assert payload["status"] == "completed"
    assert payload["completed_ticks"] == payload["total_ticks"]


def test_api_websocket_stream_emits_logs_and_terminal_status() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        created = client.post(
            "/simulations",
            json=_simulation_payload(stream_delay_seconds=0.005),
            headers=headers,
        ).json()
        simulation_id = created["simulation_id"]
        log_messages = 0
        with client.websocket_connect(f"/simulations/{simulation_id}/stream") as websocket:
            while True:
                message = websocket.receive_json()
                if message["type"] == "simulation.log":
                    log_messages += 1
                    continue
                assert message["type"] == "simulation.status"
                assert message["status"] == "completed"
                break
    assert log_messages > 0


def test_api_agents_endpoint_lists_agent_snapshots() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        created = client.post("/simulations", json=_simulation_payload(), headers=headers).json()
        _wait_for_completion(client, created["simulation_id"])
        response = client.get(f"/simulations/{created['simulation_id']}/agents")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["agents"]) == 5
    assert payload["agents"][0]["theory_of_mind_enabled"] is True


def test_api_agent_memory_endpoint_returns_recent_memories() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        created = client.post("/simulations", json=_simulation_payload(), headers=headers).json()
        _wait_for_completion(client, created["simulation_id"])
        response = client.get(f"/simulations/{created['simulation_id']}/agents/agent-0/memory")
    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_id"] == "agent-0"
    assert payload["memories"]


def test_api_event_injection_schedules_new_event() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        created = client.post(
            "/simulations",
            json=_simulation_payload(stream_delay_seconds=0.01),
            headers=headers,
        ).json()
        response = client.post(
            f"/simulations/{created['simulation_id']}/events",
            json={
                "event_type": "world.announcement",
                "participants": ["agent-0"],
                "description": "A moderator posts a short notice.",
            },
            headers=headers,
        )
    assert response.status_code == 200
    assert response.json()["scheduled_events"] >= 1


def test_api_delete_removes_simulation() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        created = client.post(
            "/simulations",
            json=_simulation_payload(stream_delay_seconds=0.01),
            headers=headers,
        ).json()
        deleted = client.delete(f"/simulations/{created['simulation_id']}")
        missing = client.get(f"/simulations/{created['simulation_id']}")
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_api_requires_tenant_bearer_token_for_writes() -> None:
    app, headers = _app_and_headers()
    with TestClient(app) as client:
        missing = client.post("/simulations", json=_simulation_payload())
        ok = client.post(
            "/simulations",
            json=_simulation_payload(),
            headers=headers,
        )
    assert missing.status_code == 401
    assert ok.status_code == 201


def test_api_rate_limit_returns_429_when_bucket_is_exhausted() -> None:
    limiter = RateLimiter(tokens_per_second=0.0, burst=1.0)
    with TestClient(create_app(rate_limiter=limiter)) as client:
        first = client.get("/simulations/missing")
        second = client.get("/simulations/missing")
    assert first.status_code == 404
    assert second.status_code == 429
