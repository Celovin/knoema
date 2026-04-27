"""Round-4 audit: usage-middleware payload validation defense-in-depth.

If a route handler bug or a crafted payload writes negative / oversized
counters into ``request.state.luvoire_usage_payload``, the metering
middleware previously coerced and recorded them blindly. This test set
verifies the new ceiling + non-negative + malformed-payload guards.
"""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from luvoire.api.auth import AuthenticatedTenant
from luvoire.api.usage_middleware import (
    UsageMeteringMiddleware,
    record_request_usage,
)
from luvoire.billing.gateway import UsageMeter


class _FakeRequest:
    def __init__(self, payload: Any, *, method: str = "POST", tenant: AuthenticatedTenant | None = None) -> None:
        self.method = method
        self.state = SimpleNamespace(
            luvoire_usage_payload=payload,
            authenticated_tenant=tenant,
        )
        self.app = SimpleNamespace(state=SimpleNamespace(usage_meter=UsageMeter()))


class _FakeResponse:
    pass


def _make_tenant() -> AuthenticatedTenant:
    return AuthenticatedTenant(
        tenant_id="tenant-a",
        tier="pro",
        api_key_id="kid-1",
        api_key_source="luvoire",
    )


def _run_dispatch(request: _FakeRequest) -> int:
    """Run the middleware once; return the post-call meter record count."""

    middleware = UsageMeteringMiddleware(app=lambda *_a, **_k: None)

    async def call_next(_req: Any) -> Any:
        return _FakeResponse()

    asyncio.run(middleware.dispatch(request, call_next))
    return len(request.app.state.usage_meter.records)


def test_negative_input_tokens_are_dropped(caplog: pytest.LogCaptureFixture) -> None:
    payload = {
        "model": "claude-opus-4-7",
        "input_tokens": -1,
        "output_tokens": 100,
        "cost_usd": "0.01",
    }
    req = _FakeRequest(payload, tenant=_make_tenant())
    with caplog.at_level(logging.WARNING, logger="luvoire.api.usage_middleware"):
        n = _run_dispatch(req)
    assert n == 0
    assert any("negative" in rec.getMessage() for rec in caplog.records)


def test_negative_cost_is_dropped(caplog: pytest.LogCaptureFixture) -> None:
    payload = {
        "model": "claude-opus-4-7",
        "input_tokens": 100,
        "output_tokens": 100,
        "cost_usd": "-0.50",
    }
    req = _FakeRequest(payload, tenant=_make_tenant())
    with caplog.at_level(logging.WARNING, logger="luvoire.api.usage_middleware"):
        n = _run_dispatch(req)
    assert n == 0


def test_token_count_above_cap_is_dropped(caplog: pytest.LogCaptureFixture) -> None:
    payload = {
        "model": "claude-opus-4-7",
        "input_tokens": 10**18,  # well above the 10M cap
        "output_tokens": 100,
        "cost_usd": "0.01",
    }
    req = _FakeRequest(payload, tenant=_make_tenant())
    with caplog.at_level(logging.WARNING, logger="luvoire.api.usage_middleware"):
        n = _run_dispatch(req)
    assert n == 0
    assert any("cap" in rec.getMessage() for rec in caplog.records)


def test_malformed_payload_is_dropped() -> None:
    """Missing required fields, non-coercible cost, etc. must not crash
    the request — middleware drops the record and continues.
    """

    payload: dict[str, Any] = {"model": "x", "input_tokens": "not-an-int"}
    req = _FakeRequest(payload, tenant=_make_tenant())
    n = _run_dispatch(req)
    assert n == 0


def test_valid_payload_is_recorded() -> None:
    payload = {
        "model": "claude-opus-4-7",
        "input_tokens": 100,
        "output_tokens": 50,
        "cost_usd": "0.001",
    }
    req = _FakeRequest(payload, tenant=_make_tenant())
    n = _run_dispatch(req)
    assert n == 1
    record = req.app.state.usage_meter.records[0]
    assert record.input_tokens == 100
    assert record.output_tokens == 50
    assert record.cost_usd == Decimal("0.001")


def test_record_request_usage_round_trip() -> None:
    """``record_request_usage`` is a thin shim — round-trip the payload
    through it and the middleware to ensure the contract is unchanged.
    """

    req = _FakeRequest(payload=None, tenant=_make_tenant())
    record_request_usage(
        req,  # type: ignore[arg-type]
        model="m",
        input_tokens=10,
        output_tokens=20,
        cost_usd="0.02",
    )
    assert req.state.luvoire_usage_payload == {
        "model": "m",
        "input_tokens": 10,
        "output_tokens": 20,
        "cost_usd": "0.02",
    }
