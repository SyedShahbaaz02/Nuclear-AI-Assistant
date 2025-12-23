// The storage account
@description('The name of the key vault.')
param name string
@description('The location for the key vault.')
param location string

resource keyvault 'Microsoft.KeyVault/vaults@2024-12-01-preview' = {
  name: name
  location: location
  properties: {
    tenantId: tenant().tenantId
    enabledForDeployment: true
    enabledForDiskEncryption: true
    enabledForTemplateDeployment: true
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'Enabled'
    sku: {
      family: 'A'
      name: 'standard'
    }
  }

  resource ServicePrincipalSecret 'secrets' = {
    name: 'ServicePrincipalSecret'
    properties: {
      value: 'Replace with your Service Principal Secret after deployment in the keyvault via the portal'
    }
  }
}
