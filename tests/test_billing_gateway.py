from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from luvoire.billing.gateway import LLMGateway, UsageMeter


class MockLiteLLM:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(kwargs)
        return {
            "choices": [{"message": {"content": "mock completion"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 8},
            "cost_usd": "0.0100",
        }


def test_byo_key_records_zero_luvoire_side_cost(tmp_path: Path) -> None:
    client = MockLiteLLM()
    gateway = LLMGateway(UsageMeter(tmp_path), completion_client=client)

    response = gateway.complete(
        tenant_id="tenant-a",
        tier="free",
        api_key_source="byo_key",
        byo_api_key="display-once-user-key",
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.ok is True
    assert response.usage is not None
    assert response.usage.provider_cost_usd == Decimal("0.0100")
    assert response.usage.billed_cost_usd == Decimal("0")
    assert gateway.usage_meter.records[0].cost_usd == Decimal("0")
    assert client.calls[0]["api_key"] == "display-once-user-key"


def test_pass_through_applies_thirty_percent_markup(tmp_path: Path) -> None:
    gateway = LLMGateway(UsageMeter(tmp_path), completion_client=MockLiteLLM())

    response = gateway.complete(
        tenant_id="tenant-b",
        tier="pro",
        api_key_source="pass_through",
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.usage is not None
    assert response.usage.billed_cost_usd == Decimal("0.013000")
    assert gateway.usage_meter.records[0].cost_usd == Decimal("0.013000")


def test_enterprise_records_analytics_with_zero_variable_cost(tmp_path: Path) -> None:
    gateway = LLMGateway(UsageMeter(tmp_path), completion_client=MockLiteLLM())

    response = gateway.complete(
        tenant_id="tenant-c",
        tier="enterprise",
        api_key_source="dedicated",
        model="private-model",
        dedicated_endpoint="https://enterprise.example.invalid/v1",
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.usage is not None
    assert response.usage.output_tokens == 8
    assert response.usage.billed_cost_usd == Decimal("0")
    assert gateway.usage_meter.records[0].tier == "enterprise"


def test_prompt_hash_is_deterministic_across_repeated_calls(tmp_path: Path) -> None:
    gateway = LLMGateway(UsageMeter(tmp_path), completion_client=MockLiteLLM())
    messages = [{"role": "user", "content": "hash me"}]

    gateway.complete(
        tenant_id="tenant-d",
        tier="free",
        api_key_source="byo_key",
        byo_api_key="user-key",
        model="gpt-5.4-mini",
        messages=messages,
    )
    gateway.complete(
        tenant_id="tenant-d",
        tier="free",
        api_key_source="byo_key",
        byo_api_key="user-key",
        model="gpt-5.4-mini",
        messages=messages,
    )

    assert gateway.records[0].prompt_hash == gateway.records[1].prompt_hash
    assert gateway.records[0].completion_hash == gateway.records[1].completion_hash
