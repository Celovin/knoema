# Luvoire Privacy Policy v1

> STATUS: DRAFT - LEGAL REVIEW PENDING (do not publish)

This privacy policy is a first draft for Luvoire commercial operations. It must be reviewed against the Korean Personal Information Protection Act, GDPR, CCPA/CPRA, payment processor contracts, and the actual infrastructure configuration before publication.

## 1. Who We Are

Celovin operates Luvoire. For self-service accounts, Celovin generally acts as the business or controller for account, billing, security, and usage operations. For enterprise deployments, Celovin may act as a processor or service provider for Customer under a data processing agreement.

## 2. Personal Information We Process

| Purpose | Categories of information | Typical source |
| --- | --- | --- |
| Account administration | Email address, name or organization, authentication events, workspace role | Customer or authorized users |
| Billing and tax | Payment status, transaction ID, limited billing metadata, tax metadata | Toss Payments, Paddle, Stripe, or Customer |
| Usage metering | tenant_id, model name, token counts, cost basis, latency, prompt hash, completion hash | Service logs |
| Security and abuse prevention | IP address, user agent, API key identifier, failed authentication events, blocked safety events | Service logs |
| Customer support | Support email, issue description, response history | Customer or authorized users |

Prompt and completion bodies are not stored in default commercial usage logs. Usage logs record non-reversible SHA-256 hashes and operational metadata needed for metering, security, and dispute handling.

## 3. Purposes of Processing

Celovin processes personal information to provide and secure the Service, authenticate users, meter usage, process payment, comply with tax and accounting obligations, respond to support requests, enforce acceptable-use restrictions, investigate abuse, and improve reliability.

Celovin does not use Customer prompts or Customer outputs to train a general-purpose model unless Customer expressly agrees in a separate written agreement or an enabled product feature states that use clearly.

## 4. Disclosures and Service Providers

Celovin may share personal information with vendors and subprocessors only as needed for the Service:

- Toss Payments for Korean domestic payment processing.
- Paddle for global merchant-of-record payment processing, tax, and settlement.
- Stripe for test-mode or future metered billing integrations.
- Hugging Face Hub for model, dataset, and hosting-related workflows.
- OpenAI and other LLM providers selected by Celovin or Customer for model inference.
- Cloud infrastructure providers for hosting, storage, networking, backups, and logs.

Celovin requires vendors to process information for limited purposes and apply reasonable security safeguards.

## 5. International Transfers

Personal information may be processed in Korea, the United States, the European Economic Area, and other countries where Celovin's vendors operate. For GDPR-covered data, Celovin will use appropriate transfer safeguards such as standard contractual clauses or another lawful transfer mechanism where required.

## 6. Retention

Celovin keeps personal information for as long as needed to provide the Service, comply with legal obligations, resolve disputes, enforce agreements, and maintain security. Billing and tax records may be retained for statutory periods. Security logs may be retained for a limited operational period. Backups are deleted on the ordinary backup lifecycle.

## 7. GDPR Data Subject Rights

Where GDPR applies, data subjects may have rights to access, rectification, erasure, restriction, portability, objection, and withdrawal of consent. Requests may be submitted through the account email or support channel. Celovin may need to verify identity and may decline or limit a request where permitted by law.

## 8. California Privacy Rights

Where the CCPA/CPRA applies, California residents may have rights to know, access, correct, delete, limit use of sensitive personal information, opt out of sale or sharing, and avoid discrimination for exercising privacy rights. Celovin does not sell personal information as the term is commonly used for data broker sales. If future advertising or analytics features create a sale or sharing obligation, Celovin must publish the required notice and opt-out mechanism before enabling them.

## 9. Children

Luvoire commercial services are not directed to children under 14. If Celovin learns that it has processed a child's personal information without appropriate authorization, Celovin will take appropriate steps to restrict or delete the account and information.

## 10. Security

Celovin applies administrative, technical, and organizational safeguards, including least-privilege access, two-factor authentication for internal access, encrypted transport, encryption at rest, hashed API key storage, security logging, dependency checks, and incident response procedures. No internet service can guarantee absolute security.

## 11. Changes and Contact

Celovin may update this policy to reflect changes in law, vendors, infrastructure, or product features. Before publication, the responsible privacy contact, business address, and data protection contact must be confirmed and inserted through counsel-approved publication workflow.

