from __future__ import annotations

from collections.abc import Mapping

from luvoire.billing.webhooks import (
    WebhookDispatcher,
    canonical_payload,
    sign_payload,
    verify_signature,
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
