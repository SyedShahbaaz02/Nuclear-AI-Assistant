@description('Name of the Document Intelligence resource')
param docIntelAccountName string

@description('Location for the Document Intelligence resource')
param location string = resourceGroup().location

@description('SKU name for Document Intelligence')
param skuName string = 'S0'

resource docIntel 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
    name: docIntelAccountName
    location: location
    kind: 'FormRecognizer'
    sku: {
        name: skuName
    }
    identity: {
        type: 'SystemAssigned'
    }
    properties: {
        publicNetworkAccess: 'Enabled'
        customSubDomainName: toLower(docIntelAccountName)
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
        docIntelName: docIntel.name
        workspaceName: workspaceName
    }
}

output id string = docIntel.id
output name string = docIntel.name
