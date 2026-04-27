from __future__ import annotations

import time
from collections.abc import Mapping

from luvoire.billing.webhooks import (
    DEFAULT_REPLAY_WINDOW_SECONDS,
    WebhookDispatcher,
    canonical_payload,
    sign_payload,
    verify_signature,
    verify_signature_with_window,
)


def test_webhook_hmac_signature_matches_fixture_vector() -> None:
    payload = canonical_payload(
        {"event": "usage.recorded", "payload": {"tenant_id": "tenant_a", "tokens": 12}}
    )

    signature = sign_payload("webhook-secret", payload)

    assert signature == "sha256=c55af2ff06bc89869c4ae2f52b803dabd01600670dda1bcb4a05f4d63541d922"
    assert verify_signature("webhook-secret", payload, signature) is True
    assert verify_signature("wrong-secret", payload, signature) is False


def test_webhook_retry_behavior_with_mocked_http() -> None:
    statuses = [500, 502, 200]
    calls: list[tuple[str, bytes, Mapping[str, str], float]] = []
    sleeps: list[float] = []

    def post(url: str, body: bytes, headers: Mapping[str, str], timeout: float) -> int:
        calls.append((url, body, headers, timeout))
        return statuses.pop(0)

    dispatcher = WebhookDispatcher(
        secret="secret",
        endpoint_url="https://example.invalid/webhook",
        http_post=post,
        sleeper=sleeps.append,
        auto_start=False,
    )

    result = dispatcher.deliver_now("usage.recorded", {"tenant_id": "tenant-a"})

    assert result.delivered is True
    assert result.attempts == 3
    assert sleeps == [1.0, 4.0]
    assert all(call[3] == 5.0 for call in calls)
    assert calls[0][2]["X-Luvoire-Signature"].startswith("sha256=")


def test_dispatch_is_queue_based_and_non_blocking() -> None:
    dispatcher = WebhookDispatcher(
        secret="secret",
        endpoint_url="https://example.invalid/webhook",
        http_post=lambda _url, _body, _headers, _timeout: 200,
        sleeper=lambda _delay: None,
        auto_start=False,
    )

    assert dispatcher.dispatch("usage.recorded", {"tenant_id": "tenant-a"}) is True
    assert dispatcher.dispatch("ignored.event", {"tenant_id": "tenant-a"}) is False
    result = dispatcher.drain_once()

    assert result is not None
    assert result.delivered is True


# --- Round-4 audit: replay-window defense -----------------------------


def test_dispatched_envelope_includes_unix_timestamp() -> None:
    """``WebhookDispatcher.deliver_now`` must include an integer ``timestamp``
    field in the signed envelope so receivers can reject replayed deliveries.
    """

    captured: list[bytes] = []

    def post(_url: str, body: bytes, _headers: Mapping[str, str], _timeout: float) -> int:
        captured.append(body)
        return 200

    dispatcher = WebhookDispatcher(
        secret="secret",
        endpoint_url="https://example.invalid/webhook",
        http_post=post,
        sleeper=lambda _delay: None,
        auto_start=False,
    )
    before = int(time.time())
    dispatcher.deliver_now("usage.recorded", {"tenant_id": "t"})
    after = int(time.time())

    assert captured, "expected at least one delivered body"
    import json

    envelope = json.loads(captured[-1].decode("utf-8"))
    assert envelope["event"] == "usage.recorded"
    assert envelope["payload"] == {"tenant_id": "t"}
    assert isinstance(envelope["timestamp"], int)
    assert before <= envelope["timestamp"] <= after


def test_verify_signature_with_window_rejects_replayed_delivery() -> None:
    """A captured delivery older than the window must fail verification
    even though the HMAC is still valid."""

    fresh_envelope = {"event": "x", "payload": {}, "timestamp": 1_000_000}
    body = canonical_payload(fresh_envelope)
    signature = sign_payload("s", body)

    # Within window
    assert verify_signature_with_window(
        "s", body, signature, window_seconds=300, now_unix=1_000_010
    ) is True
    # Outside window
    assert verify_signature_with_window(
        "s", body, signature, window_seconds=300, now_unix=1_001_000
    ) is False


def test_verify_signature_with_window_rejects_wrong_secret() -> None:
    body = canonical_payload({"event": "x", "payload": {}, "timestamp": 1_000_000})
    signature = sign_payload("right-secret", body)
    assert verify_signature_with_window(
        "wrong-secret", body, signature, now_unix=1_000_000
    ) is False


def test_verify_signature_with_window_rejects_envelope_without_timestamp() -> None:
    body = canonical_payload({"event": "x", "payload": {}})
    signature = sign_payload("s", body)
    assert verify_signature_with_window("s", body, signature, now_unix=1_000_000) is False


def test_verify_signature_with_window_rejects_bool_timestamp() -> None:
    """``isinstance(True, int)`` is True in Python; the helper must
    explicitly reject bool to avoid accepting ``True`` as a timestamp."""

    body = canonical_payload({"event": "x", "payload": {}, "timestamp": True})
    signature = sign_payload("s", body)
    assert verify_signature_with_window("s", body, signature, now_unix=1) is False


def test_verify_signature_with_window_rejects_negative_window() -> None:
    body = canonical_payload({"event": "x", "payload": {}, "timestamp": 1_000_000})
    signature = sign_payload("s", body)
    assert verify_signature_with_window(
        "s", body, signature, window_seconds=0, now_unix=1_000_000
    ) is False


def test_default_replay_window_is_five_minutes() -> None:
    assert DEFAULT_REPLAY_WINDOW_SECONDS == 300
