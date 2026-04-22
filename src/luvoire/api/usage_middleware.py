"""Usage metering middleware for authenticated commercial API calls."""

from __future__ import annotations

from decimal import Decimal

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from knoema.api.auth import AuthenticatedTenant
from knoema.billing.gateway import UsageMeter


class UsageMeteringMiddleware(BaseHTTPMiddleware):
    """Append one UsageRecord for authenticated POST/PUT calls that declare usage."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if request.method not in {"POST", "PUT"}:
            return response
        tenant = getattr(request.state, "authenticated_tenant", None)
        usage_payload = getattr(request.state, "knoema_usage_payload", None)
        if not isinstance(tenant, AuthenticatedTenant) or not isinstance(usage_payload, dict):
            return response
        meter = getattr(request.app.state, "usage_meter", None)
        if meter is None:
            meter = UsageMeter()
            request.app.state.usage_meter = meter
        meter.record(
            tenant_id=tenant.tenant_id,
            model=str(usage_payload["model"]),
            input_tokens=int(usage_payload["input_tokens"]),
            output_tokens=int(usage_payload["output_tokens"]),
            cost_usd=Decimal(str(usage_payload["cost_usd"])),
            tier=tenant.tier,
        )
        return response


def record_request_usage(
    request: Request,
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: Decimal | str | int,
) -> None:
    request.state.knoema_usage_payload = {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }


__all__ = ["UsageMeteringMiddleware", "record_request_usage"]
