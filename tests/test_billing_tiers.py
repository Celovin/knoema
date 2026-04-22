from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from luvoire.billing.gateway import LLMGateway, UsageMeter
from luvoire.billing.tiers import TIER_LIMITS


class CountingClient:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, **kwargs: object) -> dict[str, object]:
        self.calls += 1
        return {
            "choices": [{"message": {"content": "unused"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "cost_usd": "0.001",
        }


def test_tier_limits_shape_and_types() -> None:
    assert set(TIER_LIMITS) == {"free", "pro", "team", "enterprise"}
    for tier, limits in TIER_LIMITS.items():
        assert isinstance(limits["monthly_output_token_cap"], int | type(None))
        assert isinstance(limits["concurrent_request_cap"], int)
        assert limits["concurrent_request_cap"] >= 1
        assert isinstance(limits["allowed_models"], tuple)
        assert limits["allowed_models"]
        assert isinstance(limits["api_key_sources"], tuple)
        assert limits["api_key_sources"]
        assert isinstance(limits["metering_model"], str)
        assert tier in {"free", "pro", "team", "enterprise"}


def test_tier_exceeded_blocks_upstream_call(tmp_path: Path) -> None:
    meter = UsageMeter(tmp_path)
    meter.record(
        tenant_id="tenant-over-cap",
        model="gpt-5.4-mini",
        input_tokens=1,
        output_tokens=2_000_000,
        cost_usd=Decimal("0"),
        tier="pro",
    )
    client = CountingClient()
    gateway = LLMGateway(meter, completion_client=client)

    response = gateway.complete(
        tenant_id="tenant-over-cap",
        tier="pro",
        api_key_source="pass_through",
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "blocked"}],
        max_tokens=1,
    )

    assert response.ok is False
    assert response.error_code == "tier_exceeded"
    assert client.calls == 0
