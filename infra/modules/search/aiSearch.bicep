metadata description = 'The module for deploying the AI Search service and its dependencies.'

@description('The name of the AI Search instance.')
param name string
@description('The location for the AI Search instance.')
param location string
@description('The SKU to use for the AI Search instance.')
param sku string
@description('The identity type to use for AI Search.')
param identityType string = 'SystemAssigned'
@description('Whether to disable the local auth or not.')
param disableLocalAuth bool = false
@description('The encryption with CMK (Customer Managed Key) settings.')
param encryptionWithCmk object = {
    enforcement: 'Unspecified'
}
@description('The network rule set for the AI Search instance.')
param networkRuleSet object = {
    bypass: 'None'
}
@description('The semantic search settings.')
param semanticSearch string = 'free'
@description('The number of partitions for the cluster. Higher helps write speed.')
param partitionCount int
@description('The number of replicas for the cluster. Higher helps read speed.')
param replicaCount int

resource aiSearch 'Microsoft.Search/searchServices@2023-11-01' = {
  name: name
  location: location
  sku: {
    name: sku
  }
  identity: {
    type: identityType
  }
  properties: {
    disableLocalAuth: disableLocalAuth
    encryptionWithCmk: encryptionWithCmk
    networkRuleSet: networkRuleSet
    partitionCount: partitionCount
    replicaCount: replicaCount
    semanticSearch: semanticSearch
  }
}

@description('The name of the application insights to associate with.')
param workspaceName string
@description('The name of the diagnostic settings.')
param diagnosticsName string


module diagnostics 'diagnostics.bicep' = {
    params: {
        name: diagnosticsName
        searchName: aiSearch.name
        workspaceName: workspaceName
    }
}

output aiSearchName string = aiSearch.name
