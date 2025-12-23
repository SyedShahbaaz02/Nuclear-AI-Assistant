metadata description = 'Main Bicep file for deploying Azure resources for the Ask Licensing service'

// Default parameters
@description('The default location to use for resources that are created.')
param defaultLocation string = resourceGroup().location

// Storage parameters
@description('The name of the storage account.')
param storageName string
@description('The SKU to use for creating the storage account.')
param storageSku string
@description('The kind of storage account to create.')
param storageKind string
@description('The names of the containers that will used to store documents for ingestion.')
param storageContainerNames array
@description('The retention policy for deleted containers.')
param storageContainerDeleteRetentionPolicy object
@description('The retention policy for deleted blobs.')
param storageDeleteRetentionPolicy object
@description('List of IP addresses or CIDR ranges to allow access to the storage account.')
param storageAllowedIpAddresses array = []

module storage 'modules/storage/storage.bicep' = {
    scope: resourceGroup()
    name: 'strg'
    params: {
        kind: storageKind
        location: defaultLocation
        name: storageName
        sku: storageSku
        storageContainerNames: storageContainerNames
        deleteRetentionPolicy: storageDeleteRetentionPolicy
        containerDeleteRetentionPolicy: storageContainerDeleteRetentionPolicy
        allowedIpAddresses: storageAllowedIpAddresses
    }
}

// Log Analytics Workspace parameters
@description('The name of the workspace.')
param workspaceName string
@description('The SKU for the workspace.')
param workspaceSku string
@description('Log Analytics Retention Period in Days')
param workspaceRetentionInDays int = 30 // Default retention period

module workspace 'modules/analytics/workspace.bicep' = {
    scope: resourceGroup()
    name: 'wkspc'
    params: {
        location: defaultLocation
        name: workspaceName
        sku: workspaceSku
        retentionInDays: workspaceRetentionInDays
    }
}

// Application Insights parameters
@description('The name of the Application Insights resource.')
param appInsightsName string
module appInsights 'modules/analytics/applicationInsights.bicep' = {
    scope: resourceGroup()
    name: 'appIns'
    params: {
        location: defaultLocation
        name: appInsightsName
        workspaceName: workspace.outputs.workspaceName
    }
}

// AI Search parameters
@description('The name of the AI Search instance.')
param aiSearchName string
@description('The location to deploy AI Search to.')
param aiSearchLocation string
@description('The SKU to use for the AI Search instance.')
param aiSearchSku string
@description('The number of partitions for the cluster. Higher helps write speed.')
param aiSearchPartitionCount int
@description('The number of replicas for the cluster. Higher helps read speed.')
param aiSearchReplicaCount int
@description('The name of the diagnostic settings.')
param aiSearchDiagnosticsName string

module aiSearch 'modules/search/aiSearch.bicep' = {
    scope: resourceGroup()
    name: 'srch'
    params: {
        diagnosticsName: aiSearchDiagnosticsName
        location: aiSearchLocation
        name: aiSearchName
        partitionCount: aiSearchPartitionCount
        replicaCount: aiSearchReplicaCount
        sku: aiSearchSku
        workspaceName: workspace.outputs.workspaceName
    }
    dependsOn: [
        storage
    ]
}

@description('Azure Open AI Resource Name')
param openAiAccountName string
@description('Azure Open AI Location')
param openAiLocation string
@description('The name of the Open AI diagnostic settings.')
param openAiDiagnosticsName string
@description('The SKU for the Open AI resource.')
param openAiSku string = 'S0' // Default SKU for OpenAI

module openAi 'modules/openai/openai.bicep' = {
    name: 'openai'
    params: {
        openAiAccountName: openAiAccountName
        location: openAiLocation
        diagnosticsName: openAiDiagnosticsName
        workspaceName: workspace.outputs.workspaceName
        skuName: openAiSku
    }
}

@description('The name of the App Service PLan')
param appServicePlanName string
@description('The SKU for the App Service Plan')
param appServicePlanSku string

module appServicePlan 'modules/host/appServicePlan.bicep' = {
    scope: resourceGroup()
    name: 'asp'
    params:{
        name: appServicePlanName
        location: defaultLocation
        skuName: appServicePlanSku

    }
}

@description('NUREG Search Index Name')
param nuregSearchIndexName string
@description('Reportability Manual Search Index Name')
param reportabilityManualSearchIndexName string
@description('TechSpec Search Index Name')
param tsSearchIndexName string
@description('UFSAR Search Index Name')
param ufsarSearchIndexName string
@description('Log Level for the Streaming API Web App')
param streamingWebAppLogLevel string = 'INFO'
@description('Document SAS token expiration period in days')
param documentSasTokenExpirationDays string
@description('The size of the buffer for the streaming API web app.')
param streamBufferSize int
@description('The type of orchestration for the streaming API web app.')
param orchestrationType string

@description('OpenAI Chat Deployment Name')
param openAiChatDeploymentName string

@description('OpenAI Embedding Deployment Name')
param openAiEmbeddingDeploymentName string

@description('OpenAI API Version')
param openAiApiVersion string

@description('Streaming API Web App Name')
param streamingWebAppName string

// Web App parameters
module webAppStreaming 'modules/api/streamApi.bicep' = {
  name: 'streamingapi'
  scope: resourceGroup()
  params: {
    webAppName: streamingWebAppName
    storageAccountName: storage.outputs.storageAccountName
    applicationInsightsName: appInsights.outputs.appInsightsName
    openAiChatDeploymentName: openAiChatDeploymentName
    openAiEmbeddingDeploymentName: openAiEmbeddingDeploymentName
    openAiApiVersion: openAiApiVersion
    aiSearchName: aiSearch.outputs.aiSearchName
    nuregIndexName: nuregSearchIndexName
    reportabilityManualIndexName: reportabilityManualSearchIndexName
    tsIndexName: tsSearchIndexName
    ufsarIndexName: ufsarSearchIndexName
    appServicePlanId: appServicePlan.outputs.appServicePlanId
    openAiName: openAi.outputs.name
    docIntelAccountName: docIntel.outputs.name
    streamingWebAppLogLevel: streamingWebAppLogLevel
    documentSasTokenExpirationDays: documentSasTokenExpirationDays
    streamBufferSize: streamBufferSize
    orchestrationType: orchestrationType
  }
}

@description('The name of the App Service Environment')
param aseName string

@description('App Service Environment')
resource appServiceEnvironment 'Microsoft.Web/hostingEnvironments@2020-12-01' existing = {
  name: aseName
}

@description('The name of the App Service PLan')
param appServicePlanName01 string
@description('The SKU for the App Service Plan')
param appServicePlanSku01 string

module appServicePlan01 'modules/host/appServicePlan.bicep' = {
    scope: resourceGroup()
    name: 'asp01'
    params:{
        name: appServicePlanName01
        location: defaultLocation
        skuName: appServicePlanSku01
        aseId: appServiceEnvironment.id
    }
}

@description('Streaming API Web App Name')
param streamingWebAppName01 string

// Web App parameters
module webAppStreaming01 'modules/api/streamApi01.bicep' = {
  name: 'streamingapi01'
  scope: resourceGroup()
  params: {
    webAppName: streamingWebAppName01
    storageAccountName: storage.outputs.storageAccountName
    applicationInsightsName: appInsights.outputs.appInsightsName
    openAiChatDeploymentName: openAiChatDeploymentName
    openAiEmbeddingDeploymentName: openAiEmbeddingDeploymentName
    openAiApiVersion: openAiApiVersion
    aiSearchName: aiSearch.outputs.aiSearchName
    nuregIndexName: nuregSearchIndexName
    reportabilityManualIndexName: reportabilityManualSearchIndexName
    tsIndexName: tsSearchIndexName
    ufsarIndexName: ufsarSearchIndexName
    appServicePlanId: appServicePlan01.outputs.appServicePlanId
    openAiName: openAi.outputs.name
    docIntelAccountName: docIntel.outputs.name
    streamingWebAppLogLevel: streamingWebAppLogLevel
    documentSasTokenExpirationDays: documentSasTokenExpirationDays
    streamBufferSize: streamBufferSize
    aseId: appServiceEnvironment.id
    orchestrationType: orchestrationType
  }
}

@description('Document Intelligence Resource Name')
param docIntelAccountName string
@description('The name of the Document Intelligence diagnostic settings.')
param docIntelDiagnosticsName string
@description('The SKU for the Document Intelligence resource.')
param docIntelSku string = 'S0'

module docIntel 'modules/docintel/docintel.bicep' = {
    name: 'docintel'
    params: {
        docIntelAccountName: docIntelAccountName
        location: defaultLocation
        diagnosticsName: docIntelDiagnosticsName
        workspaceName: workspace.outputs.workspaceName
        skuName: docIntelSku
    }
}

// Key Vault parameters
@description('The name of the Key Vault.')
param keyVaultName string

module keyVault 'modules/keyvault/keyvault.bicep' = {
    name: 'keyVault'
    params: {
        name: keyVaultName
        location: defaultLocation
    }
}

@description('The name of the Azure Workbook.')
param workbookName string
@description('The display name for the workbook.')
param workbookDisplayName string
@description('The version of the workbook.')
param workbookVersion string
@description('The category of the workbook.')
param workbookCategory string
@description('The kind for the workbook.')
param kind string

module workbook 'modules/analytics/workbooks.bicep' = {
  name: 'workbook'
  params: {
    workbookName: workbookName
    location: defaultLocation
    displayName: workbookDisplayName
    workbookVersion: workbookVersion
    workbookCategory: workbookCategory
    sourceId: appInsights.outputs.appInsightsId
    kind: kind
  }
}
