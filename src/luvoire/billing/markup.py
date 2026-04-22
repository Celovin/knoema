"""Currency-safe commercial markup calculations."""

from __future__ import annotations

from decimal import Decimal

from luvoire.billing.tiers import TierName

TIER_MARKUPS: dict[TierName, Decimal] = {
    "free": Decimal("0"),
    "pro": Decimal("0.30"),
    "team": Decimal("0.30"),
    "enterprise": Decimal("0"),
}


def compute_markup_price(base_cost_usd: Decimal, tier: TierName) -> Decimal:
    """Return the customer-billed variable price for a base provider cost."""

    if not isinstance(base_cost_usd, Decimal):
        raise TypeError("base_cost_usd must be a decimal.Decimal")
    return base_cost_usd * (Decimal("1") + TIER_MARKUPS[tier])


__all__ = ["TIER_MARKUPS", "compute_markup_price"]
