# Knoema Data Processing Agreement Template

> STATUS: DRAFT - LEGAL REVIEW PENDING (do not publish)

This template is intended for business customers that require a data processing agreement. It must be reviewed and conformed to the final order form, privacy policy, infrastructure, and governing law before signature.

## 1. Parties and Roles

Customer is the controller, business, or equivalent decision-maker for personal data submitted to the Service. Celovin is the processor, service provider, or equivalent service operator when it processes that personal data on Customer's documented instructions.

For self-service account, billing, tax, security, fraud prevention, and legal compliance activities, Celovin may process limited information as an independent controller or business as described in the privacy policy.

## 2. Subject Matter and Duration

Celovin processes personal data to provide Knoema services, including account administration, workspace access, hosted simulations, API execution, usage metering, customer support, security monitoring, and enterprise deployment operations. Processing continues for the term of the applicable order form and any retention period required for legal, security, or dispute purposes.

## 3. Categories of Data and Data Subjects

Personal data may include user identifiers, business contact information, authentication metadata, billing metadata, API usage metadata, support communications, IP addresses, user agents, and Customer-submitted content if the Customer configures the Service to process it.

Data subjects may include Customer employees, contractors, authorized users, administrators, and individuals whose information Customer lawfully provides to the Service.

## 4. Customer Instructions

Celovin will process personal data only on Customer's documented instructions, including this DPA, the order form, the privacy policy, and product settings. Celovin will notify Customer if it believes an instruction violates applicable data protection law, unless prohibited by law.

## 5. Confidentiality

Celovin will ensure that personnel authorized to process personal data are bound by confidentiality obligations and receive access only as needed for the Service.

## 6. Security Measures

Celovin will maintain administrative, technical, and organizational measures designed to protect personal data, including:

- TLS for data in transit and encryption at rest for managed storage.
- Least-privilege access control and two-factor authentication for internal administrative access.
- API key hashing and secret storage outside the repository.
- Logging for authentication, billing, usage metering, and security events.
- Separation of customer workspaces through application-level access controls.
- Vulnerability and dependency review appropriate to the size and risk of the Service.
- Incident response procedures with evidence preservation and customer notification workflow.

## 7. Subprocessors

Customer authorizes Celovin to use subprocessors needed for the Service. The initial categories and providers are:

| Subprocessor | Purpose | Location notes |
| --- | --- | --- |
| Toss Payments | Korean domestic payment processing, refunds, settlement | Korea and processor-operated regions |
| Paddle | Merchant-of-record global payments, tax, settlement | Processor-operated regions |
| Stripe | Test-mode or future metered billing integrations | Processor-operated regions |
| Hugging Face Hub | Model, dataset, and hosting workflows | Processor-operated regions |
| OpenAI or Customer-selected LLM providers | Model inference when configured | Provider-operated regions |
| AWS or equivalent cloud infrastructure | Hosting, storage, networking, backups, logs | Region selected for the deployment |

Celovin will impose data protection obligations on subprocessors that are materially consistent with this DPA. Enterprise order forms may add notice periods or objection rights for new subprocessors.

## 8. International Transfers

Where GDPR applies and personal data is transferred outside the EEA or another protected jurisdiction, the parties will use appropriate safeguards such as standard contractual clauses or another lawful transfer mechanism. Customer is responsible for assessing whether its use of the Service is lawful for its own data and jurisdiction.

## 9. Assistance

Taking into account the nature of processing and information available to Celovin, Celovin will reasonably assist Customer with data subject requests, security obligations, data protection impact assessments, regulator inquiries, and breach notifications. Customer remains responsible for communicating with data subjects and regulators unless the parties agree otherwise.

## 10. Security Incident Notification

Celovin will notify Customer without undue delay after confirming a personal data breach affecting Customer personal data. For GDPR-covered personal data, Celovin's operational target is to notify Customer within 72 hours after confirmation, unless law enforcement or security needs require delay. Notifications will describe the known facts, affected systems, mitigation steps, and contact channel.

## 11. Deletion and Return

At Customer's written request or at termination, Celovin will delete or return Customer personal data, subject to legal retention, security logs, backup lifecycle, and technical feasibility. Backup deletion occurs according to the ordinary backup rotation.

## 12. Audits

Customer may request reasonable information about Celovin's security and compliance controls. Any audit must be scoped to the Service, protect Celovin and third-party confidential information, avoid disruption, and be conducted under a mutually agreed process.

## 13. Precedence

If this DPA conflicts with the commercial terms or an order form, the order form controls commercial terms and this DPA controls data processing obligations, unless the order form expressly states otherwise.

