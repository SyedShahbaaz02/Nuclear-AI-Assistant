using 'main.bicep'

// Storage parameters
@description('The name of the storage account.')
param storageName = 'czvgnalcs00dsta001'
@description('The SKU to use for creating the storage account.')
param storageSku = 'Standard_RAGRS'
@description('The kind of storage account to create.')
param storageKind = 'StorageV2'
@description('The names of the containers that will used to store documents for ingestion.')
param storageContainerNames = ['non-eci', 'eci']
@description('The retention policy for deleted containers.')
param storageContainerDeleteRetentionPolicy = {
    days: 7
    enabled: true
}
@description('The retention policy for deleted blobs.')
param storageDeleteRetentionPolicy = {
    allowPermanentDelete: false
    days: 7
    enabled: true
}
@description('List of IP addresses or CIDR ranges to allow access to the storage account.')
param storageAllowedIpAddresses = []

// Log Analytics Workspace parameters
@description('The name of the workspace.')
param workspaceName = 'CZV-G-N-ALCS00-D-LAW-01'
@description('The SKU for the workspace.')
param workspaceSku = 'PerGB2018'

// Application Insights paramaters
@description('The name of the Application Insights resource.')
param appInsightsName = 'CZV-G-N-ALCS00-D-AIS-01'

// AI Search parameters
@description('The name of the AI Search instance.')
param aiSearchName = 'czagnalcs00daisrch01'
@description('The location to deploy AI Search to.')
param aiSearchLocation = 'USGov Arizona'
@description('The SKU to use for the AI Search instance.')
param aiSearchSku = 'standard'
@description('The number of partitions for the cluster. Higher helps write speed.')
param aiSearchPartitionCount = 1
@description('The number of replicas for the cluster. Higher helps read speed.')
param aiSearchReplicaCount = 1
@description('The name of the diagnostic settings.')
param aiSearchDiagnosticsName = 'CZV-G-N-ALCS00-D-DIAG-SRCH-01'

// Open AI parameters
@description('Azure Open AI Resource Name')
param openAiAccountName = 'CZV-G-N-ALCS00-D-OAI-02'
@description('Azure Open AI Location')
param openAiLocation = 'USGov Arizona'
@description('The name of the Open AI diagnostic settings.')
param openAiDiagnosticsName = 'CZV-G-N-ALCS00-D-DIAG-OAI-02'
@description('OpenAI Chat Deployment Name')
param openAiChatDeploymentName = 'gpt-4o'
@description('OpenAI Embedding Deployment Name')
param openAiEmbeddingDeploymentName = 'ada-3'
@description('OpenAI API Version')
param openAiApiVersion = '2024-10-21'

// App Service Plan Parameters
@description('The name of the App Service Plan')
param appServicePlanName = 'CZV-G-N-ALCS00-D-ASP-01'
@description('The SKU for the App Service Plan')
param appServicePlanSku = 'P1v2'


// Streaming API Parameters
@description('Streaming API Web App Name')
param streamingWebAppName = 'CZV-G-N-ALCS00-D-APP-01'
@description('NUREG Search Index Name')
param nuregSearchIndexName = 'nureg-section-3-2-index'
@description('Reportability Manual Search Index Name')
param reportabilityManualSearchIndexName = 'reportability-manual-index'
@description('TechSpec Search Index Name')
param tsSearchIndexName = 'techspec-naive-index'
@description('UFSAR Search Index Name')
param ufsarSearchIndexName = 'ufsar-naive-index'
@description('Log Level for the Streaming API Web App')
param streamingWebAppLogLevel = 'DEBUG'
@description('Document SAS token expiration period in days')
param documentSasTokenExpirationDays = '90'
@description('The size of the buffer for the streaming API web app.')
param streamBufferSize = 5
@description('The type of orchestration for the streaming API web app.')
param orchestrationType = 'single'


// App Service Plan Parameters 01
@description('The name of the App Service Plan')
param appServicePlanName01 = 'CZV-G-N-ALCS00-D-ASP-02'
@description('The SKU for the App Service Plan')
param appServicePlanSku01 = 'I2v2'
@description('The name of the App Service Environment')
param aseName = 'CZV-G-N-ALCS-D-ASE-01'

// Streaming API Parameters
@description('Streaming API Web App Name')
param streamingWebAppName01 = 'CZV-G-N-ALCS00-D-APP-02'

// Document Intelligence Parameters
@description('Document Intelligence Resource Name')
param docIntelAccountName = 'CZV-G-N-ALCS00-D-DOCINT-01'
@description('The name of the Document Intelligence diagnostic settings.')
param docIntelDiagnosticsName = 'CZV-G-N-ALCS00-D-DIAG-DOCINT-01'

// Key Vault parameters
@description('The name of the Key Vault.')
param keyVaultName = 'CZV-G-N-ALCS00-D-KV-01'

// Azure Workbooks Parameters
@description('The name of the workbook.')
param workbookName = '9f4fd89d-9c85-4f33-bc41-3a4fadd0308b'
@description('The display name for the workbook.')
param workbookDisplayName = 'CZV-G-N-ALCS00-D-AWB-01'
@description('The version for the workbook.')
param workbookVersion = 'Notebook/1.0'
@description('The category for the workbook.')
param workbookCategory = 'workbook'
@description('The kind for the workbook.')
param kind = 'shared'
