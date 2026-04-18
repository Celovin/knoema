param location string = resourceGroup().location
param containerImage string
@secure()
param postgresPassword string

resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'knoema-env'
  location: location
}

resource api 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'knoema-api'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: 'knoema-postgres'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: 'knoema'
    administratorLoginPassword: postgresPassword
    storage: {
      storageSizeGB: 32
    }
  }
}

output apiUrl string = api.properties.configuration.ingress.fqdn
output postgresHost string = postgres.properties.fullyQualifiedDomainName
