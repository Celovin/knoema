"""Metered commercial LLM gateway primitives."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, cast

from knoema.billing.markup import compute_markup_price
from knoema.billing.stripe_adapter import StripeUsageAdapter, StripeUsageRecordResult
from knoema.billing.tiers import (
    ApiKeySource,
    TierName,
    is_api_key_source_allowed,
    is_model_allowed,
    monthly_output_token_cap,
)
from knoema.llm.gateway import estimate_tokens
from knoema.protocols import Message

CompletionCallable = Callable[..., object]


@dataclass(frozen=True, slots=True)
class UsageRecord:
    tenant_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    tier: TierName
    recorded_at: datetime

    def to_json(self) -> str:
        payload = {
            "tenant_id": self.tenant_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": str(self.cost_usd),
            "tier": self.tier,
            "recorded_at": self.recorded_at.isoformat(),
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


@dataclass(frozen=True, slots=True)
class GatewayUsage:
    input_tokens: int
    output_tokens: int
    provider_cost_usd: Decimal
    billed_cost_usd: Decimal


@dataclass(frozen=True, slots=True)
class GatewayResponse:
    ok: bool
    content: str
    usage: GatewayUsage | None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class GatewayCallLog:
    tenant_id: str
    tier: TierName
    api_key_source: ApiKeySource
    model: str
    prompt_hash: str
    completion_hash: str | None
    input_tokens: int
    output_tokens: int
    provider_cost_usd: Decimal
    billed_cost_usd: Decimal
    latency_ms: Decimal
    ok: bool
    error_code: str | None


class UsageMeter:
    """In-memory usage meter with a JSONL spool for later billing export."""

    def __init__(self, spool_dir: Path | str = Path("var/billing")) -> None:
        self.spool_dir = Path(spool_dir)
        self.records: list[UsageRecord] = []

    def record(
        self,
        tenant_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Decimal,
        tier: TierName,
    ) -> UsageRecord:
        """Record one tenant usage row and append it to the daily JSONL spool."""

        if not isinstance(cost_usd, Decimal):
            raise TypeError("cost_usd must be a decimal.Decimal")
        record = UsageRecord(
            tenant_id=tenant_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            tier=tier,
            recorded_at=datetime.now(UTC),
        )
        self.records.append(record)
        self._append_spool(record)
        return record

    def monthly_output_tokens(
        self,
        tenant_id: str,
        tier: TierName,
        month: date | None = None,
    ) -> int:
        """Return output tokens recorded for a tenant/tier in the given UTC month."""

        resolved_month = month or datetime.now(UTC).date()
        return sum(
            record.output_tokens
            for record in self.records
            if record.tenant_id == tenant_id
            and record.tier == tier
            and record.recorded_at.year == resolved_month.year
            and record.recorded_at.month == resolved_month.month
        )

    def flush_to_stripe(self, stripe_secret_key: str | None = None) -> list[StripeUsageRecordResult]:
        """Flush billable usage to Stripe, or no-op when Stripe is not configured."""

        resolved_key = stripe_secret_key or os.environ.get("STRIPE_TEST_SECRET_KEY")
        if not resolved_key:
            print("Stripe flush skipped: STRIPE_TEST_SECRET_KEY is unset.")
            return []

        subscription_item_id = os.environ.get("STRIPE_SUBSCRIPTION_ITEM_ID")
        if not subscription_item_id:
            print("Stripe flush skipped: STRIPE_SUBSCRIPTION_ITEM_ID is unset.")
            return []

        adapter = StripeUsageAdapter(resolved_key)
        billable_quantity = sum(record.output_tokens for record in self.records if record.cost_usd > 0)
        if billable_quantity == 0:
            return []
        return [
            adapter.submit_usage_record(
                subscription_item_id,
                billable_quantity,
                int(datetime.now(UTC).timestamp()),
            )
        ]

    def _append_spool(self, record: UsageRecord) -> None:
        self.spool_dir.mkdir(parents=True, exist_ok=True)
        filename = f"usage_{record.recorded_at:%Y%m%d}.jsonl"
        with (self.spool_dir / filename).open("a", encoding="utf-8") as handle:
            handle.write(record.to_json())
            handle.write("\n")


class LLMGateway:
    """Route LLM calls by tenant tier and record deterministic metering logs."""

    def __init__(
        self,
        usage_meter: UsageMeter | None = None,
        completion_client: CompletionCallable | None = None,
    ) -> None:
        self.usage_meter = usage_meter or UsageMeter()
        self._completion_client = completion_client or _litellm_completion
        self.records: list[GatewayCallLog] = []

    def complete(
        self,
        *,
        tenant_id: str,
        api_key_source: ApiKeySource,
        model: str,
        messages: Sequence[Message],
        tier: TierName,
        byo_api_key: str | None = None,
        dedicated_endpoint: str | None = None,
        **kwargs: object,
    ) -> GatewayResponse:
        """Complete a chat request through the configured source while enforcing tier limits."""

        prompt_hash = prompt_messages_hash(messages)
        input_tokens = estimate_tokens(_messages_to_text(messages))
        quota_error = self._quota_error(tenant_id, tier, kwargs)
        source_error = self._source_error(tier, api_key_source, model, byo_api_key)
        error_code = quota_error or source_error
        if error_code is not None:
            self._record_blocked(
                tenant_id=tenant_id,
                tier=tier,
                api_key_source=api_key_source,
                model=model,
                prompt_hash=prompt_hash,
                input_tokens=input_tokens,
                error_code=error_code,
            )
            return GatewayResponse(
                ok=False,
                content="",
                usage=None,
                error_code=error_code,
                error_message=error_code.replace("_", " "),
            )

        request_kwargs = dict(kwargs)
        if api_key_source == "byo_key":
            request_kwargs["api_key"] = byo_api_key
        elif api_key_source == "pass_through":
            master_key = os.environ.get("OPENAI_API_KEY")
            if master_key:
                request_kwargs["api_key"] = master_key
        elif dedicated_endpoint:
            request_kwargs["api_base"] = dedicated_endpoint

        started_at = perf_counter()
        response = self._completion_client(model=model, messages=list(messages), **request_kwargs)
        latency_ms = Decimal(str((perf_counter() - started_at) * 1000))
        content = _completion_to_text(response)
        output_tokens = _extract_output_tokens(response, content)
        input_tokens = _extract_input_tokens(response, input_tokens)
        provider_cost = _extract_cost_decimal(response, input_tokens, output_tokens)
        billed_cost = _billed_cost(provider_cost, tier, api_key_source)
        usage = GatewayUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider_cost_usd=provider_cost,
            billed_cost_usd=billed_cost,
        )
        self.usage_meter.record(tenant_id, model, input_tokens, output_tokens, billed_cost, tier)
        self.records.append(
            GatewayCallLog(
                tenant_id=tenant_id,
                tier=tier,
                api_key_source=api_key_source,
                model=model,
                prompt_hash=prompt_hash,
                completion_hash=completion_text_hash(content),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider_cost_usd=provider_cost,
                billed_cost_usd=billed_cost,
                latency_ms=latency_ms,
                ok=True,
                error_code=None,
            )
        )
        return GatewayResponse(ok=True, content=content, usage=usage)

    def _quota_error(
        self,
        tenant_id: str,
        tier: TierName,
        kwargs: Mapping[str, object],
    ) -> str | None:
        cap = monthly_output_token_cap(tier)
        if cap is None:
            return None
        current = self.usage_meter.monthly_output_tokens(tenant_id, tier)
        requested = _requested_output_tokens(kwargs)
        if current >= cap or current + requested > cap:
            return "tier_exceeded"
        return None

    @staticmethod
    def _source_error(
        tier: TierName,
        api_key_source: ApiKeySource,
        model: str,
        byo_api_key: str | None,
    ) -> str | None:
        if not is_api_key_source_allowed(tier, api_key_source):
            return "api_key_source_not_allowed"
        if not is_model_allowed(tier, model):
            return "model_not_allowed"
        if api_key_source == "byo_key" and not byo_api_key:
            return "byo_key_required"
        return None

    def _record_blocked(
        self,
        *,
        tenant_id: str,
        tier: TierName,
        api_key_source: ApiKeySource,
        model: str,
        prompt_hash: str,
        input_tokens: int,
        error_code: str,
    ) -> None:
        self.records.append(
            GatewayCallLog(
                tenant_id=tenant_id,
                tier=tier,
                api_key_source=api_key_source,
                model=model,
                prompt_hash=prompt_hash,
                completion_hash=None,
                input_tokens=input_tokens,
                output_tokens=0,
                provider_cost_usd=Decimal("0"),
                billed_cost_usd=Decimal("0"),
                latency_ms=Decimal("0"),
                ok=False,
                error_code=error_code,
            )
        )


def prompt_messages_hash(messages: Sequence[Message]) -> str:
    payload = [
        {"role": message.get("role", ""), "content": message.get("content", "")}
        for message in messages
    ]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def completion_text_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


def _litellm_completion(**kwargs: object) -> object:
    from litellm import completion

    return completion(**kwargs)


def _messages_to_text(messages: Sequence[Message]) -> str:
    return "\n".join(message.get("content", "") for message in messages)


def _requested_output_tokens(kwargs: Mapping[str, object]) -> int:
    value = kwargs.get("max_tokens") or kwargs.get("expected_output_tokens") or 1
    if isinstance(value, int):
        return max(1, value)
    return 1


def _billed_cost(provider_cost: Decimal, tier: TierName, api_key_source: ApiKeySource) -> Decimal:
    if api_key_source in {"byo_key", "dedicated"}:
        return Decimal("0")
    return compute_markup_price(provider_cost, tier)


def _completion_to_text(response: object) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, Mapping):
        choices = response.get("choices")
        return _choices_to_text(choices)
    choices_obj = getattr(response, "choices", None)
    if choices_obj is not None:
        return _choices_to_text(choices_obj)
    return str(response)


def _choices_to_text(choices: object) -> str:
    if not isinstance(choices, Sequence) or isinstance(choices, (str, bytes)) or not choices:
        return ""
    first = choices[0]
    if isinstance(first, Mapping):
        message = first.get("message")
        if isinstance(message, Mapping):
            content = message.get("content", "")
            return str(content)
        text = first.get("text", "")
        return str(text)
    message_obj = getattr(first, "message", None)
    if message_obj is not None:
        content_obj = getattr(message_obj, "content", "")
        return str(content_obj)
    text_obj = getattr(first, "text", "")
    return str(text_obj)


def _extract_usage_mapping(response: object) -> Mapping[str, object]:
    if isinstance(response, Mapping):
        usage = response.get("usage", {})
        if isinstance(usage, Mapping):
            return usage
    usage_obj = getattr(response, "usage", None)
    if isinstance(usage_obj, Mapping):
        return usage_obj
    return {}


def _extract_input_tokens(response: object, fallback: int) -> int:
    usage = _extract_usage_mapping(response)
    value = usage.get("prompt_tokens", usage.get("input_tokens", fallback))
    return _safe_int(value, fallback)


def _extract_output_tokens(response: object, content: str) -> int:
    usage = _extract_usage_mapping(response)
    value = usage.get("completion_tokens", usage.get("output_tokens", estimate_tokens(content)))
    return _safe_int(value, estimate_tokens(content))


def _extract_cost_decimal(response: object, input_tokens: int, output_tokens: int) -> Decimal:
    if isinstance(response, Mapping):
        for key in ("cost_usd", "provider_cost_usd"):
            value = response.get(key)
            if value is not None:
                return _safe_decimal(value)
        hidden = response.get("_hidden_params")
        if isinstance(hidden, Mapping):
            value = hidden.get("response_cost")
            if value is not None:
                return _safe_decimal(value)
    return ((Decimal(input_tokens) * Decimal("0.003")) + (Decimal(output_tokens) * Decimal("0.015"))) / Decimal(
        "1000"
    )


def _safe_int(value: object, fallback: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    return fallback


def _safe_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | str):
        return Decimal(value)
    return Decimal(str(cast(Any, value)))


__all__ = [
    "GatewayCallLog",
    "GatewayResponse",
    "GatewayUsage",
    "LLMGateway",
    "UsageMeter",
    "UsageRecord",
    "completion_text_hash",
    "prompt_messages_hash",
]
