"""Inbound Stripe webhook receiver.

Stripe webhooks deliver subscription / payment events that the Luvoire
billing layer needs to react to (e.g. ``customer.subscription.deleted``
should pause the tenant's tier; ``invoice.paid`` confirms billing
cycles closed). This route:

1. Reads the **raw** body bytes (Stripe signs the raw payload — JSON
   re-serialisation breaks the signature).
2. Verifies the ``Stripe-Signature`` header via the Stripe SDK against
   ``STRIPE_WEBHOOK_SECRET`` (per-environment endpoint secret).
3. Rejects deliveries whose ``timestamp`` is more than five minutes
   away from now (Stripe's ``construct_event`` does this internally,
   but we set the window explicitly for visibility).
4. Deduplicates on ``event.id`` so a Stripe retry on transient 5xx
   does not double-process the same event.
5. Hands the parsed event to a registered handler, or returns 200
   with ``{"received": true}`` when no handler is registered (Stripe
   treats non-2xx as a retry signal).

Civilian Use Policy alignment is unchanged here: this layer never
processes individual scenario data, only billing events.
"""

from __future__ import annotations

import logging
import os
import threading
from collections import OrderedDict
from collections.abc import Callable, Mapping
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/stripe", tags=["webhooks"])

# Stripe's documented tolerance window for replay rejection. Five
# minutes matches the upstream default — extending it would let an
# attacker replay an old delivery long after capture; tightening it
# triggers false negatives when clock drift exceeds a few seconds.
_DEFAULT_TOLERANCE_SECONDS: int = 5 * 60

# Maximum number of recent event IDs we keep for dedup. Stripe retries
# the same event up to ~3 days; keeping 4096 entries handles any
# realistic burst of retries while bounding memory.
_DEDUP_MAX_ENTRIES: int = 4096


class StripeWebhookHandler:
    """In-memory dedup + dispatch wrapper around a per-event handler.

    Construct one instance at app startup, register handlers for the
    event types you care about, and stash on ``app.state``. The route
    pulls it from there and routes the verified event.

    The dedup set is intentionally process-local — a multi-replica
    deploy MUST front this with Redis-backed dedup or accept that the
    same event may be processed once per replica during a retry burst.
    Add a Redis adapter the same way as ``RedisRateLimitBackend`` when
    that constraint binds.
    """

    def __init__(
        self,
        secret: str | None = None,
        *,
        tolerance_seconds: int = _DEFAULT_TOLERANCE_SECONDS,
        dedup_max_entries: int = _DEDUP_MAX_ENTRIES,
    ) -> None:
        if tolerance_seconds <= 0:
            raise ValueError("tolerance_seconds must be positive")
        if dedup_max_entries <= 0:
            raise ValueError("dedup_max_entries must be positive")
        self._secret = secret or os.environ.get("STRIPE_WEBHOOK_SECRET") or None
        self._tolerance_seconds = tolerance_seconds
        self._dedup_max_entries = dedup_max_entries
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.Lock()
        self._handlers: dict[str, Callable[[Mapping[str, Any]], None]] = {}

    @property
    def configured(self) -> bool:
        return self._secret is not None

    def register(
        self, event_type: str, handler: Callable[[Mapping[str, Any]], None]
    ) -> None:
        """Register ``handler`` to be invoked for events of ``event_type``."""

        if not event_type:
            raise ValueError("event_type must be non-empty")
        self._handlers[event_type] = handler

    def construct_event(self, payload: bytes, sig_header: str) -> Mapping[str, Any]:
        """Verify HMAC + tolerance and parse the event.

        Raises :class:`HTTPException` on signature failure / tolerance
        breach so the route can map to 400. Importing the Stripe SDK
        inside the method keeps the module importable in environments
        that have not pip-installed ``stripe`` (e.g. air-gapped CI).
        """

        if self._secret is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe webhook secret is not configured.",
            )
        try:
            import stripe  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - infra only
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Stripe SDK not installed on this host.",
            ) from exc
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self._secret,
                tolerance=self._tolerance_seconds,
            )
        except (stripe.error.SignatureVerificationError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe signature verification failed: {type(exc).__name__}",
            ) from exc
        if not isinstance(event, Mapping) or not event.get("id") or not event.get("type"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stripe event missing id / type",
            )
        return event

    def remember(self, event_id: str) -> bool:
        """Record ``event_id`` as seen; return ``False`` if it was already
        present (i.e. this is a duplicate Stripe retry).
        """

        with self._lock:
            if event_id in self._seen:
                return False
            self._seen[event_id] = None
            # Bound memory by evicting the oldest entries — Stripe
            # retries within ~3 days so a 4k window covers normal
            # operation. Anything older is unlikely to be a true
            # duplicate by the time it arrives.
            while len(self._seen) > self._dedup_max_entries:
                self._seen.popitem(last=False)
            return True

    def dispatch(self, event: Mapping[str, Any]) -> None:
        handler = self._handlers.get(str(event.get("type", "")))
        if handler is None:
            return
        try:
            handler(event)
        except Exception:
            # A failing handler MUST NOT propagate to Stripe as a 5xx,
            # because Stripe will retry indefinitely and the same fault
            # will reproduce. Log + swallow + continue. Operators see
            # the failure via the structured log + observability stack.
            LOGGER.exception(
                "stripe_webhook_handler_failed",
                extra={"luvoire_stripe_event_type": event.get("type", "")},
            )


def _handler_from_request(request: Request) -> StripeWebhookHandler:
    handler = getattr(request.app.state, "stripe_webhook_handler", None)
    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook handler is not configured.",
        )
    if not isinstance(handler, StripeWebhookHandler):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook handler is misconfigured.",
        )
    return handler


@router.post("", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
) -> dict[str, Any]:
    """Receive a Stripe webhook delivery."""

    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe-Signature header is required.",
        )
    handler = _handler_from_request(request)
    raw_body = await request.body()
    event = handler.construct_event(raw_body, stripe_signature)
    event_id = str(event["id"])
    if not handler.remember(event_id):
        # Duplicate — return 200 so Stripe stops retrying. The
        # ``deduplicated`` flag lets observability dashboards count
        # retry storms separately from fresh deliveries.
        return {"received": True, "deduplicated": True, "event_id": event_id}
    handler.dispatch(event)
    return {"received": True, "deduplicated": False, "event_id": event_id}


__all__ = ["StripeWebhookHandler", "router"]
