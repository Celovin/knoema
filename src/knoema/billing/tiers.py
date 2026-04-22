"""Commercial tier limits for metered LLM usage."""

from __future__ import annotations

from typing import Literal, TypedDict

ApiKeySource = Literal["byo_key", "pass_through", "dedicated"]
TierName = Literal["free", "pro", "team", "enterprise"]


class TierLimit(TypedDict):
    monthly_output_token_cap: int | None
    concurrent_request_cap: int
    allowed_models: tuple[str, ...]
    api_key_sources: tuple[ApiKeySource, ...]
    metering_model: str


TIER_LIMITS: dict[TierName, TierLimit] = {
    "free": {
        "monthly_output_token_cap": 100_000,
        "concurrent_request_cap": 1,
        "allowed_models": ("gpt-5.4-mini", "gpt-4.1-mini", "claude-3-7-sonnet-latest"),
        "api_key_sources": ("byo_key",),
        "metering_model": "usage-counts-only",
    },
    "pro": {
        "monthly_output_token_cap": 2_000_000,
        "concurrent_request_cap": 4,
        "allowed_models": ("gpt-5.4-mini", "gpt-4.1-mini", "claude-3-7-sonnet-latest"),
        "api_key_sources": ("pass_through",),
        "metering_model": "metered-pass-through-with-markup",
    },
    "team": {
        "monthly_output_token_cap": 10_000_000,
        "concurrent_request_cap": 16,
        "allowed_models": ("gpt-5.4-mini", "gpt-5.4", "gpt-4.1-mini", "claude-3-7-sonnet-latest"),
        "api_key_sources": ("pass_through",),
        "metering_model": "workspace-metered-pass-through-with-markup",
    },
    "enterprise": {
        "monthly_output_token_cap": None,
        "concurrent_request_cap": 64,
        "allowed_models": ("*",),
        "api_key_sources": ("dedicated",),
        "metering_model": "dedicated-flat-contract",
    },
}


def get_tier_limit(tier: TierName) -> TierLimit:
    """Return the immutable limit record for a tier."""

    return TIER_LIMITS[tier]


def is_model_allowed(tier: TierName, model: str) -> bool:
    """Return whether a model is available to the given tier."""

    allowed = TIER_LIMITS[tier]["allowed_models"]
    return "*" in allowed or model in allowed


def is_api_key_source_allowed(tier: TierName, api_key_source: ApiKeySource) -> bool:
    """Return whether a tier may use the requested credential source."""

    return api_key_source in TIER_LIMITS[tier]["api_key_sources"]


def monthly_output_token_cap(tier: TierName) -> int | None:
    """Return the configured monthly output-token cap for a tier."""

    return TIER_LIMITS[tier]["monthly_output_token_cap"]


__all__ = [
    "TIER_LIMITS",
    "ApiKeySource",
    "TierLimit",
    "TierName",
    "get_tier_limit",
    "is_api_key_source_allowed",
    "is_model_allowed",
    "monthly_output_token_cap",
]
