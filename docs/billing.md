# Billing and Metering

Luvoire uses a tiered LLM cost model:

| Tier | Credential source | Monthly output-token cap | Concurrent requests | Billing model |
| --- | --- | ---: | ---: | --- |
| Free | Customer BYO key | 100,000 | 1 | Usage counts only; no Luvoire-side variable charge |
| Pro | Luvoire pass-through key | 2,000,000 | 4 | Provider cost plus 30% markup |
| Team | Luvoire pass-through key | 10,000,000 | 16 | Provider cost plus 30% markup with workspace sharing |
| Enterprise | Dedicated endpoint | Contract-specific | 64 default | Flat contract; token counts kept for analytics |

The gateway records prompt and completion hashes, token counts, provider cost, billed cost, and latency for every call. It never writes raw prompts, completions, or customer API keys to the usage spool.

## LLM Cost Flow

```text
Client request
  |
  v
Tenant API key verification
  |
  v
Tier check: credential source, model allow-list, monthly output cap
  |
  v
LLMGateway -> LiteLLM completion()
  |
  v
UsageMeter -> var/billing/usage_YYYYMMDD.jsonl
  |
  v
StripeUsageAdapter -> Stripe usage record when STRIPE_TEST_SECRET_KEY and STRIPE_SUBSCRIPTION_ITEM_ID are set
```

Free calls require a customer-supplied provider key. The raw key is accepted for that one request, passed to the provider client, and discarded. Luvoire records token counts and hashes only.

Pro and Team calls use Luvoire's provider key from the runtime environment. The base provider cost is calculated as a `decimal.Decimal`, then billed with a 30% markup. Currency math does not use floats.

Enterprise calls route to a customer-assigned endpoint. The variable usage record is zero-cost because enterprise billing is handled by contract, but analytics still record token counts and hashes.

## Stripe Meter Export

`UsageMeter.flush_to_stripe()` is safe to call in local and CI environments. If `STRIPE_TEST_SECRET_KEY` is unset, it prints a skip message and returns an empty list. If the key is set but `STRIPE_SUBSCRIPTION_ITEM_ID` is missing, it also skips. Live billing requires both values and should only be enabled after the Stripe seller account is configured.

## Secret Handling

Customer BYO keys:

- are provided per request;
- are never stored in `UsageMeter`;
- do not appear in JSONL spool rows;
- do not appear in webhook payloads.

Luvoire provider keys:

- are read from environment variables at runtime;
- are not committed to the repository;
- are not printed by diagnostics or tests.

Tenant API keys:

- `issue(tenant_id, scope)` returns the raw secret once;
- the store keeps only the SHA256 hash;
- `verify(raw_secret)` uses constant-time comparison;
- `revoke(key_id)` soft-deletes the key with a timestamp;
- `rotate(key_id)` creates a new key while the old key remains valid for 24 hours.

## Webhook Events

Customer webhooks are signed with `X-Luvoire-Signature: sha256=<hex>`. The signature is an HMAC-SHA256 digest over the canonical JSON payload.

Supported events:

| Event | When it fires | Required payload fields |
| --- | --- | --- |
| `usage.recorded` | A metered call is recorded | `tenant_id`, `model`, `input_tokens`, `output_tokens`, `tier` |
| `tier.exceeded` | A request would exceed the monthly output-token cap | `tenant_id`, `tier`, `cap`, `current_usage` |
| `subscription.updated` | A tenant's subscription state changes | `tenant_id`, `old_tier`, `new_tier`, `effective_at` |

Example:

```json
{
  "event": "usage.recorded",
  "payload": {
    "tenant_id": "tenant_123",
    "model": "gpt-5.4-mini",
    "input_tokens": 1200,
    "output_tokens": 420,
    "tier": "pro"
  }
}
```

The dispatcher uses a background queue so webhook retries do not block an upstream LLM call. Retry delays are 1, 4, 16, and 64 seconds, with a 5-second timeout per attempt.
