# Luvoire Security Posture v1

> STATUS: DRAFT - LEGAL REVIEW PENDING (do not publish)

This customer-facing security posture is a draft. It describes intended commercial controls for Luvoire and must be reviewed against the deployed production environment before being shared as a security representation.

## 1. Scope

Luvoire is a persistent-agent simulation and synthetic replay platform. The commercial service includes APIs, hosted demos, billing metering, workspace administration, and enterprise deployment options. Security controls are designed around synthetic simulation workloads, usage metering, prompt routing, and customer-managed scenarios.

This document is not a SOC 2 report, ISO certification, penetration-test attestation, or external audit report. External audit is pending and any customer security questionnaire must be answered against the actual deployment in place at the time of review.

## 2. Data Classification

| Data class | Examples | Default handling |
| --- | --- | --- |
| Customer prompts | Prompts, scenario descriptions, configuration text | Processed to provide the requested service; not stored in default commercial usage logs unless a feature or contract enables it |
| Customer outputs | Generated text, simulation logs, synthetic replay results | Returned to Customer and stored only when Customer chooses persistence or hosted replay features |
| Usage logs | tenant_id, model, token counts, cost basis, latency, prompt hash, completion hash | Stored for billing, analytics, abuse response, and dispute handling |
| Account data | Email address, organization, workspace roles, authentication events | Stored for account administration and security |
| Payment metadata | Transaction ID, payment status, tax and settlement metadata | Stored by payment processors and limited records retained by Celovin |
| Secrets | API keys, provider keys, webhook secrets | Stored outside source control; customer BYO keys are passed per call and are not persisted by default |
| Public artifacts | Documentation, pricing pages, status pages, attribution files | Public or customer-facing by design |

## 3. Encryption

Luvoire targets TLS 1.3 for data in transit where supported by the hosting stack and payment or model providers. Managed storage for production deployments should use AES-256 or cloud-provider equivalent encryption at rest. Backups should inherit the same encryption posture as the managed storage service.

Customer BYO provider keys are not written to default usage logs. API key management stores only SHA-256 hashes of issued tenant keys. Webhook payloads are signed with HMAC-SHA256 using tenant or endpoint secrets.

## 4. Access Control

Celovin follows least-privilege access principles. Administrative access to production systems should require two-factor authentication. Repository and deployment permissions should be limited to personnel with a current operational need. Workspace authorization is enforced at the application layer, and enterprise deployments may add customer-specific network or identity controls.

Production data access should be logged where technically feasible. Support access should be limited to the minimum information needed to resolve a ticket.

## 5. Secret Management

Secrets are configured through environment variables or managed secret stores and must not be committed to the repository. Local development examples must use placeholder names, not live values. Rotation should occur after personnel changes, suspected exposure, vendor incident, or at least annually for production secrets. Customer API keys can be revoked and rotated through the tenant key lifecycle.

## 6. Logging and Monitoring

Commercial logs should capture authentication events, API key usage metadata, billing meter records, webhook delivery status, tier limit events, and safety filter blocks. Prompt and completion bodies are excluded from default billing logs. Logs are used for reliability, abuse response, customer support, billing disputes, and incident investigation.

## 7. Incident Response

Celovin's incident response workflow should include triage, severity assignment, containment, evidence preservation, eradication, recovery, customer notification, and post-incident review. For personal data breaches affecting GDPR-covered data, the target is customer notification within 72 hours after confirmation, unless delayed by law enforcement, security containment, or incomplete facts.

Incident notifications should describe known facts, affected services, mitigation steps, recommended customer actions, and a contact channel. A root-cause summary should be provided after investigation where appropriate.

## 8. Subprocessors and Third Parties

Luvoire may rely on the following third parties depending on customer configuration:

- Hugging Face Hub for model, dataset, and hosting workflows.
- OpenAI and other LLM providers for model inference.
- Stripe for test-mode or future metered billing integrations.
- Toss Payments for Korean domestic payment processing.
- Paddle for global merchant-of-record payment processing.
- Cloud infrastructure providers for hosting, storage, networking, backups, and logs.

Third-party providers process data under their own terms and security programs. Enterprise customers may request a current subprocessor list in the order process.

## 9. Development and Supply Chain

The repository uses automated tests, type checking, linting, attribution checks, and SBOM generation to reduce regression risk. Dependency metadata and license notices are maintained through regenerable artifacts. Security findings are triaged based on exploitability, affected surface, and customer impact.

## 10. Customer Responsibilities

Customers are responsible for lawful input data, user access review, BYO provider key protection, workspace role hygiene, local exports, downstream disclosure of outputs, and independent validation before high-impact use. Luvoire must not be used for real-person profiling, operational law-enforcement targeting, surveillance, weapons, or other prohibited uses described in the commercial terms.

