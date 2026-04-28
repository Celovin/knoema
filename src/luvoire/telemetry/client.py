from __future__ import annotations

import json
import os
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib import request

from luvoire.config import get_env
from luvoire.telemetry.schema import TelemetryEvent, TelemetryProperties

_TRUTHY_VALUES = {"1", "true", "yes", "on"}
_DEFAULT_ID_PATH = Path.home() / ".luvoire" / "telemetry_id"


class TelemetryTransport(Protocol):
    def post(self, endpoint: str, payload: dict[str, object], *, timeout_seconds: float) -> None: ...


class UrlLibTelemetryTransport:
    def post(self, endpoint: str, payload: dict[str, object], *, timeout_seconds: float) -> None:
        from luvoire.safety.url_scheme import require_http_url

        # Defense-in-depth: a misconfigured ``LUVOIRE_TELEMETRY_ENDPOINT``
        # could otherwise let urllib follow ``file://`` for a local-file
        # leak or ``gopher://`` for protocol smuggling.
        safe_endpoint = require_http_url(endpoint)
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            safe_endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=timeout_seconds) as response:  # nosec B310 - scheme validated by require_http_url above
            response.read()


@dataclass(frozen=True, slots=True)
class TelemetrySettings:
    enabled: bool = False
    endpoint: str | None = None
    api_key: str | None = None
    distinct_id: str | None = None
    timeout_seconds: float = 2.0


class NullTelemetryClient:
    def capture(
        self,
        event_name: str,
        *,
        properties: TelemetryProperties | None = None,
    ) -> bool:
        del event_name, properties
        return False


class TelemetryClient:
    def __init__(
        self,
        settings: TelemetrySettings,
        *,
        transport: TelemetryTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport or UrlLibTelemetryTransport()

    def capture(
        self,
        event_name: str,
        *,
        properties: TelemetryProperties | None = None,
    ) -> bool:
        if not self._settings.enabled:
            return False
        if self._settings.endpoint is None or self._settings.distinct_id is None:
            return False
        event = TelemetryEvent(
            event=event_name,
            distinct_id=self._settings.distinct_id,
            properties=dict(properties or {}),
        )
        try:
            self._transport.post(
                self._settings.endpoint,
                event.to_payload(api_key=self._settings.api_key),
                timeout_seconds=self._settings.timeout_seconds,
            )
        except (OSError, ValueError):
            return False
        return True


def telemetry_opt_in_from_env(env: Mapping[str, str] | None = None) -> bool:
    env_map = os.environ if env is None else env
    value = get_env("LUVOIRE_TELEMETRY", "KNOEMA_TELEMETRY", "", environ=env_map)
    return (value or "").strip().lower() in _TRUTHY_VALUES


def load_or_create_anonymous_id(path: Path | None = None) -> str:
    target = path or _DEFAULT_ID_PATH
    if target.exists():
        existing = target.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    target.parent.mkdir(parents=True, exist_ok=True)
    distinct_id = str(uuid.uuid4())
    target.write_text(distinct_id, encoding="utf-8")
    return distinct_id


def build_env_telemetry_client(
    *,
    force_enable: bool = False,
    env: Mapping[str, str] | None = None,
    transport: TelemetryTransport | None = None,
    id_path: Path | None = None,
) -> TelemetryClient | NullTelemetryClient:
    env_map = os.environ if env is None else env
    enabled = force_enable or telemetry_opt_in_from_env(env_map)
    endpoint = get_env(
        "LUVOIRE_TELEMETRY_ENDPOINT",
        "KNOEMA_TELEMETRY_ENDPOINT",
        environ=env_map,
    )
    if not enabled or endpoint is None or not endpoint.strip():
        return NullTelemetryClient()
    distinct_id = get_env("LUVOIRE_TELEMETRY_ID", "KNOEMA_TELEMETRY_ID", environ=env_map)
    if distinct_id is None:
        distinct_id = load_or_create_anonymous_id(id_path)
    settings = TelemetrySettings(
        enabled=True,
        endpoint=endpoint,
        api_key=get_env(
            "LUVOIRE_TELEMETRY_API_KEY",
            "KNOEMA_TELEMETRY_API_KEY",
            environ=env_map,
        ),
        distinct_id=distinct_id,
    )
    return TelemetryClient(settings, transport=transport)
