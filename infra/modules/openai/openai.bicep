@description('Name of the Azure OpenAI resource')
param openAiAccountName string
@description('Location for the Azure OpenAI resource')
param location string = resourceGroup().location
@description('The identity type to use for the Azure Open AI account.')
param identityType string = 'SystemAssigned'
@description('SKU name for Azure OpenAI')
param skuName string = 'S0'

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
    name: openAiAccountName
    location: location
    kind: 'OpenAI'
    identity: {
        type: identityType
    }
    sku: {
        name: skuName
    }
    properties: {
        customSubDomainName: toLower(openAiAccountName)
        publicNetworkAccess: 'Enabled'
        networkAcls: {
            defaultAction: 'Allow'
        }
    }
}

@description('The name of the log analytics workspace to associate with.')
param workspaceName string
@description('The name of the diagnostic settings.')
param diagnosticsName string

module diagnostics 'diagnostics.bicep' = {
    params: {
        name: diagnosticsName
        openAiName: openAi.name
        workspaceName: workspaceName
    }
}

output id string = openAi.id
output name string = openAi.name
