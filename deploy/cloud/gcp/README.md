# GCP Deployment

The GCP template targets Cloud Run, Cloud SQL for PostgreSQL, and Memorystore Redis. It keeps image, project, and region values as variables so account-specific state stays outside the repository.

```bash
terraform -chdir=deploy/cloud/gcp/terraform init
terraform -chdir=deploy/cloud/gcp/terraform validate
terraform -chdir=deploy/cloud/gcp/terraform plan -var project_id=my-project -var container_image=gcr.io/my-project/knoema-api:0.2.0
```
