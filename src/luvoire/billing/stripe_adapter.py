"""Thin Stripe usage-record adapter with safe no-op behavior."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, slots=True)
class StripeUsageRecordResult:
    id: str
    skipped: bool
    quantity: int
    timestamp: int


class StripeUsageAdapter:
    """Submit metered usage to Stripe when a test or live key is explicitly supplied."""

    def __init__(self, stripe_secret_key: str | None = None) -> None:
        self._stripe_secret_key = stripe_secret_key or os.environ.get("STRIPE_TEST_SECRET_KEY")

    def submit_usage_record(
        self,
        subscription_item_id: str,
        quantity: int,
        timestamp: int,
    ) -> StripeUsageRecordResult:
        """Submit one Stripe usage record, or return a deterministic mock id when disabled."""

        if not self._stripe_secret_key:
            print("Stripe usage submission skipped: STRIPE_TEST_SECRET_KEY is unset.")
            return StripeUsageRecordResult(
                id=f"stripe_mock_{subscription_item_id}_{timestamp}_{quantity}",
                skipped=True,
                quantity=quantity,
                timestamp=timestamp,
            )

        import stripe  # type: ignore[import-not-found,unused-ignore]

        stripe.api_key = self._stripe_secret_key
        response = stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=quantity,
            timestamp=timestamp,
            action="increment",
        )
        response_id = cast(str, response["id"])
        return StripeUsageRecordResult(
            id=response_id,
            skipped=False,
            quantity=quantity,
            timestamp=timestamp,
        )


def submit_usage_record(
    subscription_item_id: str,
    quantity: int,
    timestamp: int,
    stripe_secret_key: str | None = None,
) -> StripeUsageRecordResult:
    """Compatibility helper for callers that do not need an adapter instance."""

    return StripeUsageAdapter(stripe_secret_key).submit_usage_record(
        subscription_item_id,
        quantity,
        timestamp,
    )


__all__ = ["StripeUsageAdapter", "StripeUsageRecordResult", "submit_usage_record"]
