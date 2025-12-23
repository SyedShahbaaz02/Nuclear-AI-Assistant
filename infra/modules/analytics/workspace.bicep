metadata description = 'The log analytics workspace used for application and infrastructure observability.'

@description('The name of the workspace.')
param name string
@description('The location to create the workspace in.')
param location string
@description('The SKU for the workspace.')
param sku string
@description('The identity type to use for the workspace.')
param identityType string = 'SystemAssigned'
@description('The length of time, in days, to retain the insights data.')
param retentionInDays int = 30

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
    name: name
    location: location
    identity: {
        type: identityType
    }
    properties: {
        sku: {
            name: sku
        }
        retentionInDays: retentionInDays
    }
}

output workspaceId string = workspace.id
output workspaceName string = workspace.name
