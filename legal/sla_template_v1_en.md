# Knoema Service Level Agreement Template v1

> STATUS: DRAFT - LEGAL REVIEW PENDING (do not publish)

This SLA template is intended for enterprise and team customers. It must be attached to a signed order form before it creates binding service commitments.

## 1. Covered Service

This SLA applies to the paid hosted Knoema API, hosted replay services, and enterprise deployment endpoints identified in the applicable order form. It does not apply to local open-source use, free demos, preview experiments, third-party model provider outages, customer-managed infrastructure, or customer bring-your-own provider keys.

## 2. Uptime Commitment

| Tier | Monthly uptime target | Service commitment |
| --- | ---: | --- |
| Enterprise | 99.5% | Contracted SLA, eligible for service credits |
| Team | 99.0% | Contracted SLA if listed in the order form |
| Pro | Best effort | No service credits unless separately agreed |
| Free | Best effort | No service credits |

Monthly uptime is calculated as total minutes in the calendar month minus excluded downtime, divided by total minutes in the calendar month.

## 3. Exclusions

Downtime does not include scheduled maintenance, emergency maintenance, customer network or device issues, customer code or configuration errors, customer-managed provider keys, third-party LLM provider outages, payment processor outages, cloud provider regional incidents outside Celovin's control, force majeure events, abuse mitigation, legal compliance actions, or suspensions for non-payment or breach.

## 4. Scheduled Maintenance

Celovin will use commercially reasonable efforts to provide at least 48 hours' notice for scheduled maintenance expected to affect production availability. Emergency maintenance may be performed with shorter notice when needed to protect security, data integrity, or service reliability.

## 5. Support Response Targets

| Tier | Initial response target | Channel |
| --- | --- | --- |
| Enterprise | 4 business hours | Named support contact or agreed ticket channel |
| Team | 1 business day | Support email or ticket channel |
| Pro | 3 business days | Support email |
| Free | Community or best effort | Public or self-service channel |

Response targets are not resolution commitments. Business hours are Korea business hours unless the order form states otherwise.

## 6. Service Credits

If Celovin fails to meet an applicable monthly uptime commitment and Customer submits a credit request within 30 days after the affected month, Customer may receive the following credit against future service fees:

| Monthly uptime | Credit |
| --- | ---: |
| 99.0% to below 99.5% | 10% of monthly covered service fees |
| 98.0% to below 99.0% | 25% of monthly covered service fees |
| Below 98.0% | 50% of monthly covered service fees |

Service credits are Customer's sole and exclusive remedy for SLA failure. Credits cannot exceed the monthly covered service fees for the affected service and are not cash refunds.

## 7. Claim Process

Customer must submit the affected workspace, dates, times, observed error, and supporting logs. Celovin will review service telemetry and determine eligibility in good faith.

## 8. Force Majeure

Celovin is not responsible for delay or failure caused by events beyond reasonable control, including natural disasters, war, civil unrest, labor disputes, governmental actions, internet backbone failures, cloud provider incidents, payment network failures, or widespread security emergencies.

