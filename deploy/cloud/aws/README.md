# AWS Deployment

The AWS template targets ECS Fargate behind an Application Load Balancer with RDS PostgreSQL and ElastiCache Redis. It is intended as a starting point for production review, not a one-command live deployment.

## Terraform

```bash
terraform -chdir=deploy/cloud/aws/terraform init
terraform -chdir=deploy/cloud/aws/terraform validate
terraform -chdir=deploy/cloud/aws/terraform plan -var container_image=example/knoema-api:0.2.0
```

## CloudFormation

```bash
aws cloudformation validate-template --template-body file://deploy/cloud/aws/cloudformation/knoema-stack.yaml
```

## Required Inputs

- `container_image`
- `region`
- `db_username`
- `db_password` supplied through a secret manager or secure CI variable
