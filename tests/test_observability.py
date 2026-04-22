from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from luvoire.api.server import create_app
from luvoire.billing.api_keys import APIKeyManager, InMemoryAPIKeyStore

ROOT = Path(__file__).resolve().parents[1]


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


def test_observability_default_has_no_metrics_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LUVOIRE_METRICS_ENABLED", raising=False)
    monkeypatch.delenv("LUVOIRE_OTEL_EXPORTER", raising=False)

    with TestClient(create_app()) as client:
        response = client.get("/metrics")

    assert response.status_code == 404


def test_default_server_path_does_not_import_opentelemetry() -> None:
    code = (
        "import sys;"
        "from luvoire.api.server import create_app;"
        "create_app();"
        "print(any(name.startswith('opentelemetry') for name in sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "False"


def test_metrics_enabled_exposes_prometheus_format(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("prometheus_client")
    monkeypatch.setenv("LUVOIRE_METRICS_ENABLED", "1")
    monkeypatch.delenv("LUVOIRE_OTEL_EXPORTER", raising=False)

    with TestClient(create_app()) as client:
        assert client.get("/healthz").status_code == 200
        response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "luvoire_requests_total" in response.text
    assert "luvoire_request_duration_seconds_bucket" in response.text


def test_metric_labels_hash_tenant_id(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("prometheus_client")
    monkeypatch.setenv("LUVOIRE_METRICS_ENABLED", "1")
    monkeypatch.delenv("LUVOIRE_OTEL_EXPORTER", raising=False)
    tenant_id = "tenant-visible-plaintext"
    manager = APIKeyManager(InMemoryAPIKeyStore())
    _key_id, token = manager.issue(tenant_id, "llm:invoke", tier="pro")

    with TestClient(create_app(api_key_manager=manager)) as client:
        response = client.post(
            "/simulations/run",
            json=_simulation_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        metrics = client.get("/metrics").text

    assert "luvoire_billing_tokens_total" in metrics
    assert "tenant_id_hash" in metrics
    assert tenant_id not in metrics


@pytest.mark.skipif(
    importlib.util.find_spec("opentelemetry") is None,
    reason="OpenTelemetry optional dependencies are not installed.",
)
def test_otel_exporter_can_capture_request_span(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

    from luvoire.observability import tracing

    class ListSpanExporter(SpanExporter):
        def __init__(self) -> None:
            self.spans: list[Any] = []

        def export(self, spans: Any) -> SpanExportResult:
            self.spans.extend(spans)
            return SpanExportResult.SUCCESS

        def shutdown(self) -> None:
            return None

    exporter = ListSpanExporter()
    monkeypatch.setenv("LUVOIRE_OTEL_EXPORTER", "otlp")
    monkeypatch.delenv("LUVOIRE_METRICS_ENABLED", raising=False)
    monkeypatch.setattr(tracing, "_build_span_exporter", lambda _exporter: exporter)

    with TestClient(create_app()) as client:
        assert client.get("/healthz").status_code == 200

    assert exporter.spans
