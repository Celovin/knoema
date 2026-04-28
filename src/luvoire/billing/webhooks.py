"""Outbound billing webhook dispatcher."""

from __future__ import annotations

import hmac
import json
import queue
import threading
import time as _time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from time import sleep
from typing import Protocol
from urllib import request

from luvoire.observability.metrics import record_webhook_dispatch
from luvoire.safety.audit_log import CommercialAuditLogger, NoOpAuditLog

DEFAULT_REPLAY_WINDOW_SECONDS: int = 5 * 60
"""Default replay window for ``verify_signature_with_window``. Stripe and
GitHub use 5 minutes; we follow the same convention so a captured
delivery cannot be replayed indefinitely. Receivers SHOULD validate the
``timestamp`` field of every envelope against this window.
"""

WebhookEvent = str
HttpPoster = Callable[[str, bytes, Mapping[str, str], float], int]
Sleeper = Callable[[float], None]

DEFAULT_EVENTS: tuple[WebhookEvent, ...] = (
    "usage.recorded",
    "tier.exceeded",
    "subscription.updated",
)
RETRY_DELAYS: tuple[float, ...] = (1.0, 4.0, 16.0, 64.0)


class QueueItem(Protocol):
    event_type: str
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class WebhookDelivery:
    event_type: str
    payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class WebhookResult:
    delivered: bool
    attempts: int
    last_status: int | None


class WebhookDispatcher:
    """Dispatch signed webhook events from a non-blocking queue."""

    def __init__(
        self,
        secret: str,
        endpoint_url: str,
        events: tuple[WebhookEvent, ...] = DEFAULT_EVENTS,
        *,
        http_post: HttpPoster | None = None,
        sleeper: Sleeper = sleep,
        auto_start: bool = True,
        audit_log: CommercialAuditLogger | None = None,
    ) -> None:
        self.secret = secret
        self.endpoint_url = endpoint_url
        self.events = set(events)
        self._http_post = http_post or _urllib_post
        self._sleeper = sleeper
        self.audit_log = audit_log or NoOpAuditLog()
        self._queue: queue.Queue[WebhookDelivery | None] = queue.Queue()
        self._worker: threading.Thread | None = None
        if auto_start:
            self.start()

    def start(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            return
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._queue.put(None)
        if self._worker is not None:
            self._worker.join(timeout=5)

    def dispatch(self, event_type: WebhookEvent, payload: dict[str, object]) -> bool:
        """Queue an event and return immediately."""

        if event_type not in self.events:
            return False
        self._queue.put(WebhookDelivery(event_type=event_type, payload=dict(payload)))
        return True

    def drain_once(self) -> WebhookResult | None:
        """Process one queued event synchronously, used by tests and maintenance scripts."""

        item = self._queue.get_nowait()
        if item is None:
            return None
        return self.deliver_now(item.event_type, item.payload)

    def deliver_now(self, event_type: WebhookEvent, payload: dict[str, object]) -> WebhookResult:
        """Deliver an event synchronously with retry/backoff."""

        # ``timestamp`` is a unix-epoch integer signed inside the body so
        # receivers can reject replays via :func:`verify_signature_with_window`.
        # See Stripe's webhook signing convention for prior art.
        envelope = {
            "event": event_type,
            "payload": payload,
            "timestamp": int(_time.time()),
        }
        body = canonical_payload(envelope)
        delivery_id = _delivery_id(event_type, body, self.endpoint_url)
        url_hash = _url_hash(self.endpoint_url)
        subject = _payload_subject(payload)
        self.audit_log.append(
            "commercial.webhook_dispatched",
            actor="webhook-dispatcher",
            subject=subject,
            metadata={"delivery_id": delivery_id, "event_type": event_type, "url_hash": url_hash},
        )
        headers = {
            "Content-Type": "application/json",
            "X-Luvoire-Signature": sign_payload(self.secret, body),
        }
        attempts = 0
        last_status: int | None = None
        for delay in RETRY_DELAYS:
            attempts += 1
            try:
                last_status = self._http_post(self.endpoint_url, body, headers, 5.0)
                if 200 <= last_status < 300:
                    record_webhook_dispatch("delivered")
                    return WebhookResult(delivered=True, attempts=attempts, last_status=last_status)
            except OSError:
                last_status = None
            record_webhook_dispatch("failed")
            self.audit_log.append(
                "commercial.webhook_failed",
                actor="webhook-dispatcher",
                subject=subject,
                metadata={
                    "attempt": attempts,
                    "delivery_id": delivery_id,
                    "event_type": event_type,
                    "last_status": last_status,
                    "url_hash": url_hash,
                },
            )
            self._sleeper(delay)
        self.audit_log.append(
            "commercial.webhook_exhausted",
            actor="webhook-dispatcher",
            subject=subject,
            metadata={
                "attempts": attempts,
                "delivery_id": delivery_id,
                "event_type": event_type,
                "last_status": last_status,
                "url_hash": url_hash,
            },
        )
        record_webhook_dispatch("exhausted")
        return WebhookResult(delivered=False, attempts=attempts, last_status=last_status)

    def _worker_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            self.deliver_now(item.event_type, item.payload)


def canonical_payload(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )


def sign_payload(secret: str, payload: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, payload: bytes, signature_header: str) -> bool:
    expected = sign_payload(secret, payload)
    return hmac.compare_digest(expected, signature_header)


def verify_signature_with_window(
    secret: str,
    payload: bytes,
    signature_header: str,
    *,
    window_seconds: int = DEFAULT_REPLAY_WINDOW_SECONDS,
    now_unix: int | None = None,
) -> bool:
    """Verify HMAC AND reject deliveries whose envelope ``timestamp``
    falls outside a rolling window. Returns ``False`` for any of:

    - HMAC mismatch
    - body is not a JSON object with an integer ``timestamp`` field
    - timestamp delta ``|now - timestamp| > window_seconds``

    Use this in receiver-side webhook handlers so a captured signed
    delivery cannot be replayed indefinitely. Defense matches the
    Stripe / GitHub convention: a 5-minute window with constant-time
    HMAC verification first.
    """

    if not verify_signature(secret, payload, signature_header):
        return False
    try:
        envelope = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(envelope, dict):
        return False
    timestamp = envelope.get("timestamp")
    if not isinstance(timestamp, int) or isinstance(timestamp, bool):
        return False
    if window_seconds <= 0:
        return False
    current = int(_time.time()) if now_unix is None else int(now_unix)
    return abs(current - timestamp) <= window_seconds


def _delivery_id(event_type: str, body: bytes, endpoint_url: str) -> str:
    seed = event_type.encode("utf-8") + b"\0" + body + b"\0" + endpoint_url.encode("utf-8")
    return sha256(seed).hexdigest()[:24]


def _url_hash(endpoint_url: str) -> str:
    return sha256(endpoint_url.encode("utf-8")).hexdigest()


def _payload_subject(payload: Mapping[str, object]) -> str:
    tenant_id = payload.get("tenant_id")
    if isinstance(tenant_id, str) and tenant_id:
        return tenant_id
    return "commercial-webhook"


def _urllib_post(endpoint_url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> int:
    # Defense-in-depth: validate the scheme before letting urlopen run.
    # Without this, an operator who mistypes the endpoint or a
    # compromised config substitution could redirect deliveries to
    # ``file://`` (local-file leak) or ``gopher://`` (protocol smuggle).
    from luvoire.safety.url_scheme import require_http_url

    safe_url = require_http_url(endpoint_url)
    req = request.Request(safe_url, data=body, headers=dict(headers), method="POST")
    with request.urlopen(req, timeout=timeout) as response:  # nosec B310 - scheme validated by require_http_url above
        return int(response.status)


__all__ = [
    "DEFAULT_EVENTS",
    "DEFAULT_REPLAY_WINDOW_SECONDS",
    "RETRY_DELAYS",
    "WebhookDelivery",
    "WebhookDispatcher",
    "WebhookResult",
    "canonical_payload",
    "sign_payload",
    "verify_signature",
    "verify_signature_with_window",
]
