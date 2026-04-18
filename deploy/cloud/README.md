# Cloud Deployment Templates

Phase 59 provides production-oriented templates for AWS, GCP, and Azure. The templates are intentionally conservative and account-neutral: they define infrastructure shape and validation surfaces without embedding credentials, project IDs, subscription IDs, or region-specific secrets.

## Provider Comparison

| Provider | Runtime | Database | Cache | Best fit |
| --- | --- | --- | --- | --- |
| AWS | ECS Fargate behind ALB | RDS PostgreSQL | ElastiCache Redis | Teams already standardized on VPC networking and ECS |
| GCP | Cloud Run | Cloud SQL PostgreSQL | Memorystore Redis | Fast container rollout with simple autoscaling |
| Azure | Container Apps | Azure Database for PostgreSQL | Container Apps environment only | Microsoft-oriented enterprise buyers |

## Monthly Cost Envelope

These estimates assume a small API container, managed PostgreSQL, and light cache usage. They are planning envelopes, not provider quotes.

| Requests per month | AWS | GCP | Azure |
| ---: | ---: | ---: | ---: |
| 10k | USD 75-115 | USD 55-95 | USD 65-105 |
| 100k | USD 95-155 | USD 75-135 | USD 85-145 |
| 1M | USD 145-260 | USD 120-230 | USD 135-245 |

## Validate

```bash
python deploy/cloud/validate_templates.py
```

Provider CLI validation can be added locally when the relevant toolchains are installed:

```bash
terraform -chdir=deploy/cloud/aws/terraform validate
terraform -chdir=deploy/cloud/gcp/terraform validate
az bicep build --file deploy/cloud/azure/bicep/main.bicep
```
