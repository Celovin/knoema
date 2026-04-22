from __future__ import annotations

import os
import time

import pytest

from luvoire.billing.stripe_adapter import StripeUsageAdapter


@pytest.mark.slow
def test_stripe_usage_record_round_trip_when_enabled() -> None:
    if os.environ.get("LUVOIRE_ENABLE_STRIPE_TEST") != "1":
        pytest.skip("set LUVOIRE_ENABLE_STRIPE_TEST=1 for live Stripe test-mode verification")
    secret_key = os.environ.get("STRIPE_TEST_SECRET_KEY")
    subscription_item_id = os.environ.get("STRIPE_TEST_SUBSCRIPTION_ITEM_ID")
    if not secret_key or not subscription_item_id:
        pytest.skip("Stripe test secret and subscription item id are required")

    result = StripeUsageAdapter(secret_key).submit_usage_record(
        subscription_item_id=subscription_item_id,
        quantity=1,
        timestamp=int(time.time()),
    )

    assert result.skipped is False
    assert result.id
