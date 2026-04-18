# Cloud Deployment Comparison

Phase 59 adds account-neutral templates for three production paths:

- AWS ECS Fargate, RDS PostgreSQL, ElastiCache Redis, and ALB.
- GCP Cloud Run, Cloud SQL PostgreSQL, and Memorystore Redis.
- Azure Container Apps and Azure Database for PostgreSQL Flexible Server.

## Cost Envelope

| Requests per month | AWS | GCP | Azure | Notes |
| ---: | ---: | ---: | ---: | --- |
| 10k | USD 75-115 | USD 55-95 | USD 65-105 | Small pilot with managed database always on |
| 100k | USD 95-155 | USD 75-135 | USD 85-145 | Early partner traffic |
| 1M | USD 145-260 | USD 120-230 | USD 135-245 | Small commercial workload |

## Recommendation

Use GCP Cloud Run for the fastest low-ops commercial demo, AWS ECS Fargate for buyers already operating inside a VPC-heavy AWS estate, and Azure Container Apps when enterprise procurement favors Microsoft infrastructure.

## Validation

Run the repository validator:

```bash
python deploy/cloud/validate_templates.py
```

The validator checks that the committed template set still contains the required runtime, database, cache, and load-balancing resources. Provider-native validation should be run in an authenticated account before any production deployment.
