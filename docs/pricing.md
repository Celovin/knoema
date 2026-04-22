# Pricing

Luvoire pricing separates bring-your-own-key evaluation from metered hosted usage. Prices are pre-tax and are listed in USD unless the checkout provider shows a local currency during checkout.

| Tier | Price | Monthly token cap | Concurrent requests | Support | SLA target | LLM cost model |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Free | $0/mo | 100,000 output tokens | 1 | Community docs and GitHub issues | No uptime SLA | Customer BYO OpenAI key; usage is counted only, with no Luvoire-side variable charge |
| Pro | $49/mo | 2,000,000 output tokens | 4 | Email support, next-business-day target | Best-effort, no contractual SLA | Luvoire pass-through key; provider cost plus 30% markup |
| Team | $199/mo | 10,000,000 output tokens | 16 | Priority email for workspace admins | 99.5% target after commercial terms are countersigned | Shared pass-through key; provider cost plus 30% markup |
| Enterprise | Contact sales | Contract-specific | 64 default | Named support path and launch review | Contract-specific SLA target | Dedicated endpoint or approved customer provider; flat contract with usage analytics |

## How do I get a key?

Use the customer onboarding CLI to create a PoC tenant and issue a hashed tenant API key. See [Customer Onboarding](customer-onboarding.md) for the command sequence and `/simulations/run` curl example.

## Start or Subscribe

### Free

**Start with your own OpenAI key**

Use Free when you want to run local or hosted evaluation with your own provider credentials. Luvoire records usage counts and safety hashes, but it does not store raw customer API keys.

### Pro

**Subscribe with card (Toss KR / Paddle global)**

Checkout placeholders, not live checkout links:

- Paddle global: `https://checkout.paddle.com/<product-id-placeholder>`
- Toss KR: `https://pay.tosspayments.com/<payment-link-placeholder>`

### Team

**Subscribe with card**

Checkout placeholders, not live checkout links:

- Paddle global: `https://checkout.paddle.com/<team-product-id-placeholder>`
- Toss KR: `https://pay.tosspayments.com/<team-payment-link-placeholder>`

### Enterprise

**Contact sales@celovin.com**

Use Enterprise for dedicated endpoint review, custom SLA terms, procurement paperwork, data-processing terms, or higher concurrency.

## Taxes and Provider Roles

Prices above are pre-tax. Paddle global checkout calculates and remits applicable taxes where Paddle is the merchant of record. Toss KR checkout should show Korean tax handling and invoice/receipt behavior during seller onboarding before any paid launch.

Billing behavior is documented in [docs/billing.md](billing.md). Legal drafts are collected in [docs/legal.md](legal.md), including the current [legal terms](legal/commercial_terms_v1_en.md). Review those documents before enabling live checkout.
