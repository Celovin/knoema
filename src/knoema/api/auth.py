"""API key helpers for the Knoema API server."""

from __future__ import annotations

import os

from fastapi import HTTPException, Request, WebSocket, WebSocketException, status


def _expected_api_key() -> str | None:
    value = os.getenv("KNOEMA_API_KEY")
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


def require_api_key(request: Request) -> None:
    expected = _expected_api_key()
    if expected is None:
        return
    token = _extract_bearer_token(request.headers.get("Authorization"))
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


def require_websocket_api_key(websocket: WebSocket) -> None:
    expected = _expected_api_key()
    if expected is None:
        return
    token = _extract_bearer_token(websocket.headers.get("Authorization"))
    if token != expected:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or missing API key.",
        )


__all__ = ["require_api_key", "require_websocket_api_key"]
