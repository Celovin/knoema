"""Tenant authentication helpers for the Luvoire API server."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, Response, WebSocket, WebSocketException, status

from luvoire.billing import api_keys
from luvoire.billing.tiers import ApiKeySource, TierName
from luvoire.config import get_env


def _tokens_equal(presented: str | None, expected: str | None) -> bool:
    """Constant-time equality for the legacy server-wide API key path.

    ``secrets.compare_digest`` rejects None / mixed-type inputs, so we
    coerce both sides to bytes (with an empty-string fallback) before
    comparing. The empty-empty case is forced to ``False`` so a missing
    expected key cannot be silently equal to a missing presented token.
    """

    if not expected:
        return False
    if presented is None:
        # Still run compare_digest against a same-length pad to keep
        # response time independent of the length of ``expected``.
        return secrets.compare_digest(b"\0" * len(expected.encode("utf-8")), expected.encode("utf-8"))
    return secrets.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))


@dataclass(frozen=True, slots=True)
class AuthenticatedTenant:
    tenant_id: str
    tier: TierName
    api_key_id: str
    api_key_source: ApiKeySource


def _expected_api_key() -> str | None:
    value = get_env("LUVOIRE_API_KEY", "KNOEMA_API_KEY")
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _extract_bearer_token(header_value: str | None) -> str | None:
    if header_value is None:
        return None
    prefix = "Bearer "
    if not header_value.startswith(prefix):
        return None
    token = header_value[len(prefix) :].strip()
    return token or None


def _tenant_from_token(app: Any, token: str) -> AuthenticatedTenant | None:
    manager = getattr(app.state, "api_key_manager", api_keys.default_manager())
    verified = manager.verify_key(token)
    if verified is None:
        return None
    return AuthenticatedTenant(
        tenant_id=verified.tenant_id,
        tier=verified.tier,
        api_key_id=verified.key_id,
        api_key_source=verified.api_key_source,
    )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing tenant API key.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_tenant(request: Request, response: Response) -> AuthenticatedTenant:
    token = _extract_bearer_token(request.headers.get("Authorization"))
    if token is None:
        raise _unauthorized()
    tenant = _tenant_from_token(request.app, token)
    if tenant is None:
        raise _unauthorized()
    request.state.authenticated_tenant = tenant
    response.headers["X-Luvoire-Tenant-Tier"] = tenant.tier
    return tenant


def optional_tenant(request: Request, response: Response) -> AuthenticatedTenant | None:
    token = _extract_bearer_token(request.headers.get("Authorization"))
    if token is None:
        return None
    tenant = _tenant_from_token(request.app, token)
    if tenant is None:
        raise _unauthorized()
    request.state.authenticated_tenant = tenant
    response.headers["X-Luvoire-Tenant-Tier"] = tenant.tier
    return tenant


def optional_websocket_tenant(websocket: WebSocket) -> AuthenticatedTenant | None:
    token = _extract_bearer_token(websocket.headers.get("Authorization"))
    if token is None:
        return None
    tenant = _tenant_from_token(websocket.app, token)
    if tenant is None:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid tenant API key.",
        )
    return tenant


def require_api_key(request: Request) -> None:
    """Legacy server-wide API key guard used by compatibility routes."""

    expected = _expected_api_key()
    if expected is None:
        return
    token = _extract_bearer_token(request.headers.get("Authorization"))
    if not _tokens_equal(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


def require_websocket_api_key(websocket: WebSocket) -> None:
    """Legacy WebSocket API key guard used when LUVOIRE_API_KEY is configured."""

    expected = _expected_api_key()
    if expected is None:
        return
    token = _extract_bearer_token(websocket.headers.get("Authorization"))
    if not _tokens_equal(token, expected):
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or missing API key.",
        )


__all__ = [
    "AuthenticatedTenant",
    "optional_tenant",
    "optional_websocket_tenant",
    "require_api_key",
    "require_tenant",
    "require_websocket_api_key",
]
