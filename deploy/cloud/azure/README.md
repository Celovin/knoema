# Azure Deployment

The Azure template targets Container Apps and Azure Database for PostgreSQL Flexible Server. It keeps all subscription-specific values outside source control.

```bash
az bicep build --file deploy/cloud/azure/bicep/main.bicep
az deployment group what-if --resource-group my-rg --template-file deploy/cloud/azure/bicep/main.bicep
```
