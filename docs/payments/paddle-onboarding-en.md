# Paddle Seller Onboarding Reference

This document is a reference for setting up Paddle as the global merchant-of-record option for Celovin. Codex does not create a Paddle account, complete KYC, submit documents, or generate live keys.

## 1. Official Sources Checked

- Paddle account verification: https://www.paddle.com/help/start/account-verification/what-is-account-verification
- Paddle business identification: https://www.paddle.com/help/start/account-verification/what-is-business-verification
- Paddle identity verification: https://www.paddle.com/help/start/account-verification/what-is-identity-verification
- Paddle supported checkout countries: https://developer.paddle.com/concepts/sell/supported-countries-locales
- Paddle Korean local cards: https://developer.paddle.com/concepts/payment-methods/korean/local-cobranded-cards
- Paddle API authentication: https://developer.paddle.com/api-reference/about/authentication
- Paddle webhook signature verification: https://developer.paddle.com/webhooks/signature-verification

## 2. Current Finding on Korean Sole Proprietor Support

Paddle's public verification docs confirm that Paddle supports account verification flows for individuals or sole traders, and that business verification is not required for individuals or sole traders. Paddle's public checkout docs also list South Korea as a supported buyer country and document Korean local cards.

However, the public docs checked on 2026-04-22 do not explicitly say that a Korean sole proprietor can be approved as the seller of record for a Paddle account. Treat VO-1 below as preferred but unconfirmed until Paddle support confirms it in writing.

Concrete question for Paddle support:

> Can a South Korean sole proprietor with a Korean business registration certificate, Korean government ID, Korean bank account proof, and a Korean software/SaaS website be approved as a Paddle seller? If yes, which exact registration, tax, payout, and domain-review documents are required?

## 3. Verification Options

| Option | Description | Use when |
| --- | --- | --- |
| VO-1 | Celovin registers as a KR sole proprietor seller | Preferred if Paddle confirms Korean sole proprietor support |
| VO-2 | Celovin forms a US LLC and uses that entity for Paddle | Fallback if Paddle cannot support the KR sole proprietor path |
| VO-3 | Use Wise Business plus direct invoicing without Paddle | Fallback for enterprise invoices while global card checkout is blocked |

Do not start live Paddle checkout until one option is confirmed and the legal entity details match the published website and bank payout profile.

## 4. Required Seller Materials

Prepare these before starting Paddle verification:

- Government-issued business registration document, if registering as a business.
- Government ID for the beneficial owner or sole trader.
- Ownership breakdown if using a company and any owner holds more than 25%.
- Bank account proof for payouts.
- Production website URL with product description, pricing, terms, privacy policy, refund policy, support email, and prohibited-use language.
- Demo or screenshots explaining the Knoema product if domain review asks for clarification.

Paddle's business identification docs say government business registration documents should preferably be PDF files. They also say utility bills, accounting documents, and tax identification documents alone are not acceptable as business registration proof.

## 5. API Keys, Client Tokens, and Webhooks

Knoema environment variable naming:

```text
PADDLE_API_KEY=
PADDLE_WEBHOOK_SECRET=
```

Operational notes:

- Paddle API keys are server-side credentials and must be kept secret.
- Paddle client-side tokens are separate from API keys. Do not store a client-side token in `PADDLE_API_KEY`.
- Webhook secrets are used to verify Paddle webhook signatures. Store them only in `.env.local` or the deployment secret store.
- Rotate Paddle keys if they are exposed or when personnel access changes.
- Keep sandbox and live credentials in separate environments.

## 6. Onboarding Flow

1. Create the Paddle account using the selected legal entity.
2. Submit the production domain for review.
3. Complete business identification if required.
4. Complete identity verification through Paddle's verification flow.
5. Configure payout bank details.
6. Create sandbox API key and webhook secret.
7. Run the local environment diagnostic script.
8. Only after approval, create live API key and live webhook secret.
9. Add products and prices matching `docs/pricing.md`.
10. Wire live checkout URLs only after seller approval and a successful sandbox checkout test.

## 7. Readiness Checks

```powershell
.venv\Scripts\python.exe scripts\check_payment_env.py
```

Expected pre-registration result: `PADDLE_API_KEY` and `PADDLE_WEBHOOK_SECRET` are unset.

Expected sandbox result after approval: both variables are set in `.env.local` or the deployment secret store, but values are never printed.
