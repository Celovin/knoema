"""Round-6: inbound Stripe webhook receiver.

We test the ``StripeWebhookHandler`` directly with a stubbed Stripe
SDK because pip-installing ``stripe`` in CI is out of scope for this
audit pass. The route is exercised end-to-end via FastAPI's
``TestClient`` with a handler whose secret + tolerance behaviour is
overridden.
"""

from __future__ import annotations

import json
import sys
import types
from collections.abc import Mapping
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from luvoire.api.routes.stripe_webhook import StripeWebhookHandler, router

# ---------------------------------------------------------------------------
# Stub the stripe SDK so ``construct_event`` is testable without the real
# package. The stub is installed via monkeypatch on ``sys.modules`` so it
# only applies for the duration of each test.
# ---------------------------------------------------------------------------


def _install_stripe_stub(
    monkeypatch: pytest.MonkeyPatch,
    *,
    accept_signature: str = "valid-sig",
) -> None:
    """Install a deterministic ``stripe`` stub that:
    - constructs a Mapping event when ``sig_header == accept_signature``
    - raises ``SignatureVerificationError`` otherwise
    """

    error_module = types.ModuleType("stripe.error")

    class _SigError(Exception):
        pass

    error_module.SignatureVerificationError = _SigError  # type: ignore[attr-defined]

    webhook_module = types.SimpleNamespace()

    def construct_event(
        payload: bytes,
        sig_header: str,
        secret: str,
        *,
        tolerance: int,
    ) -> Mapping[str, Any]:
        if sig_header != accept_signature:
            raise _SigError("bad signature")
        try:
            event = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("bad payload") from exc
        if not isinstance(event, dict):
            raise ValueError("not an object")
        return event

    webhook_module.construct_event = construct_event

    stripe_module = types.ModuleType("stripe")
    stripe_module.error = error_module  # type: ignore[attr-defined]
    stripe_module.Webhook = webhook_module  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "stripe", stripe_module)
    monkeypatch.setitem(sys.modules, "stripe.error", error_module)


# ---- Direct StripeWebhookHandler tests -------------------------------


def test_handler_unconfigured_when_no_secret() -> None:
    handler = StripeWebhookHandler(secret=None)
    assert handler.configured is False


def test_handler_configured_when_secret_provided() -> None:
    handler = StripeWebhookHandler(secret="whsec_x")
    assert handler.configured is True


def test_handler_construct_event_rejects_bad_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_stripe_stub(monkeypatch)
    handler = StripeWebhookHandler(secret="whsec_x")
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        handler.construct_event(b'{"id":"evt_1","type":"x"}', "wrong-sig")
    assert exc.value.status_code == 400


def test_handler_dedup_returns_false_on_replay() -> None:
    handler = StripeWebhookHandler(secret="whsec_x")
    assert handler.remember("evt_1") is True
    assert handler.remember("evt_1") is False
    assert handler.remember("evt_2") is True


def test_handler_dedup_evicts_oldest_at_cap() -> None:
    handler = StripeWebhookHandler(
        secret="whsec_x",
        dedup_max_entries=3,
    )
    for i in range(5):
        assert handler.remember(f"evt_{i}") is True
    # evt_0 and evt_1 should have been evicted; readding evt_0 returns True.
    assert handler.remember("evt_0") is True


def test_handler_dispatch_swallows_handler_exceptions() -> None:
    """A misbehaving handler MUST NOT propagate exceptions out — that
    would force Stripe to retry indefinitely on the same broken event.
    """

    handler = StripeWebhookHandler(secret="whsec_x")

    def boom(_event: Mapping[str, Any]) -> None:
        raise RuntimeError("handler crashed")

    handler.register("customer.created", boom)
    # Must not raise.
    handler.dispatch({"id": "evt_1", "type": "customer.created"})


def test_handler_dispatch_invokes_registered_handler() -> None:
    handler = StripeWebhookHandler(secret="whsec_x")
    seen: list[Mapping[str, Any]] = []
    handler.register("customer.created", seen.append)
    event = {"id": "evt_1", "type": "customer.created", "data": {}}
    handler.dispatch(event)
    assert seen == [event]


def test_handler_dispatch_no_handler_is_a_noop() -> None:
    handler = StripeWebhookHandler(secret="whsec_x")
    handler.dispatch({"id": "evt_1", "type": "subscription.deleted"})  # no raise


def test_handler_invalid_tolerance_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        StripeWebhookHandler(secret="whsec_x", tolerance_seconds=0)


def test_handler_invalid_dedup_cap_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        StripeWebhookHandler(secret="whsec_x", dedup_max_entries=0)


# ---- End-to-end route tests ------------------------------------------


def _make_app(handler: StripeWebhookHandler) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.state.stripe_webhook_handler = handler
    return app


def test_route_returns_400_when_signature_header_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_stripe_stub(monkeypatch)
    handler = StripeWebhookHandler(secret="whsec_x")
    client = TestClient(_make_app(handler))
    response = client.post("/webhooks/stripe", content=b'{"id":"evt_1"}')
    assert response.status_code == 400
    assert "Stripe-Signature" in response.json()["detail"]


def test_route_returns_503_when_handler_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_stripe_stub(monkeypatch)
    handler = StripeWebhookHandler(secret=None)
    client = TestClient(_make_app(handler))
    response = client.post(
        "/webhooks/stripe",
        content=b'{"id":"evt_1","type":"x"}',
        headers={"Stripe-Signature": "valid-sig"},
    )
    assert response.status_code == 503


def test_route_processes_fresh_event(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_stripe_stub(monkeypatch)
    handler = StripeWebhookHandler(secret="whsec_x")
    seen: list[Mapping[str, Any]] = []
    handler.register("customer.created", seen.append)
    client = TestClient(_make_app(handler))
    payload = json.dumps(
        {"id": "evt_xyz", "type": "customer.created", "data": {"x": 1}}
    ).encode("utf-8")
    response = client.post(
        "/webhooks/stripe",
        content=payload,
        headers={"Stripe-Signature": "valid-sig"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["received"] is True
    assert body["deduplicated"] is False
    assert body["event_id"] == "evt_xyz"
    assert seen == [
        {"id": "evt_xyz", "type": "customer.created", "data": {"x": 1}}
    ]


def test_route_dedup_does_not_double_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_stripe_stub(monkeypatch)
    handler = StripeWebhookHandler(secret="whsec_x")
    seen: list[Mapping[str, Any]] = []
    handler.register("customer.created", seen.append)
    client = TestClient(_make_app(handler))
    payload = json.dumps(
        {"id": "evt_dup", "type": "customer.created"}
    ).encode("utf-8")
    headers = {"Stripe-Signature": "valid-sig"}

    first = client.post("/webhooks/stripe", content=payload, headers=headers)
    second = client.post("/webhooks/stripe", content=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["deduplicated"] is False
    assert second.json()["deduplicated"] is True
    # Handler invoked exactly once despite two deliveries.
    assert len(seen) == 1


def test_route_rejects_bad_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_stripe_stub(monkeypatch)
    handler = StripeWebhookHandler(secret="whsec_x")
    client = TestClient(_make_app(handler))
    response = client.post(
        "/webhooks/stripe",
        content=b'{"id":"evt_1","type":"customer.created"}',
        headers={"Stripe-Signature": "WRONG"},
    )
    assert response.status_code == 400
    assert "signature verification failed" in response.json()["detail"].lower()
