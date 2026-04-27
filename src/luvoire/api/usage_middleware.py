"""Usage metering middleware for authenticated commercial API calls."""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from luvoire.api.auth import AuthenticatedTenant
from luvoire.billing.gateway import UsageMeter

_LOGGER = logging.getLogger(__name__)

# Defense-in-depth ceiling for per-request token counts. Any single
# completion call producing more than this is almost certainly a route-
# handler bug (or a malicious crafted payload) and would corrupt the
# monthly tier-cap arithmetic. Real provider responses fit well under
# this bound — Claude Opus 4.7's 1 M context is ~10^6 tokens.
_MAX_TOKENS_PER_REQUEST: int = 10_000_000


class UsageMeteringMiddleware(BaseHTTPMiddleware):
    """Append one UsageRecord for authenticated POST/PUT calls that declare usage."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if request.method not in {"POST", "PUT"}:
            return response
        tenant = getattr(request.state, "authenticated_tenant", None)
        usage_payload = getattr(request.state, "luvoire_usage_payload", None)
        if not isinstance(tenant, AuthenticatedTenant) or not isinstance(usage_payload, dict):
            return response
        meter = getattr(request.app.state, "usage_meter", None)
        if meter is None:
            meter = UsageMeter()
            request.app.state.usage_meter = meter
        # Validate at the meter boundary: a route-handler bug or a
        # crafted payload could otherwise drive the monthly tier cap
        # negative or wrap a large positive into 32-bit territory.
        try:
            input_tokens = int(usage_payload["input_tokens"])
            output_tokens = int(usage_payload["output_tokens"])
            cost_usd = Decimal(str(usage_payload["cost_usd"]))
        except (KeyError, TypeError, ValueError, InvalidOperation):
            _LOGGER.warning(
                "usage_middleware: malformed usage payload, dropping "
                "(tenant=%s tier=%s)",
                tenant.tenant_id,
                tenant.tier,
            )
            return response
        if input_tokens < 0 or output_tokens < 0 or cost_usd < 0:
            _LOGGER.warning(
                "usage_middleware: negative usage counters, dropping "
                "(tenant=%s in=%d out=%d cost=%s)",
                tenant.tenant_id,
                input_tokens,
                output_tokens,
                cost_usd,
            )
            return response
        if (
            input_tokens > _MAX_TOKENS_PER_REQUEST
            or output_tokens > _MAX_TOKENS_PER_REQUEST
        ):
            _LOGGER.warning(
                "usage_middleware: token count exceeds cap %d, dropping "
                "(tenant=%s in=%d out=%d)",
                _MAX_TOKENS_PER_REQUEST,
                tenant.tenant_id,
                input_tokens,
                output_tokens,
            )
            return response
        meter.record(
            tenant_id=tenant.tenant_id,
            model=str(usage_payload["model"]),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
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
    request.state.luvoire_usage_payload = {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }


__all__ = ["UsageMeteringMiddleware", "record_request_usage"]
