using 'main.bicep'

// Storage parameters
@description('The name of the storage account.')
param storageName = 'czvgnalcs00ssta001'
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
param workspaceName = 'CZV-G-N-ALCS00-S-LAW-01'
@description('The SKU for the workspace.')
param workspaceSku = 'PerGB2018'

// Application Insights paramaters
@description('The name of the Application Insights resource.')
param appInsightsName = 'CZV-G-N-ALCS00-S-AIS-01'

// AI Search parameters
@description('The name of the AI Search instance.')
param aiSearchName = 'czagnalcs00saisrch01'
@description('The location to deploy AI Search to.')
param aiSearchLocation = 'USGov Arizona'
@description('The SKU to use for the AI Search instance.')
param aiSearchSku = 'standard'
@description('The number of partitions for the cluster. Higher helps write speed.')
param aiSearchPartitionCount = 1
@description('The number of replicas for the cluster. Higher helps read speed.')
param aiSearchReplicaCount = 1
@description('The name of the diagnostic settings.')
param aiSearchDiagnosticsName = 'CZV-G-N-ALCS00-S-DIAG-SRCH-01'

// Open AI parameters
@description('Azure Open AI Resource Name')
param openAiAccountName = 'CZA-G-N-ALCS00-S-OAI-01'
@description('Azure Open AI Location')
param openAiLocation = 'USGov Arizona'
@description('The name of the Open AI diagnostic settings.')
param openAiDiagnosticsName = 'CZV-G-N-ALCS00-S-DIAG-OAI-01'
@description('OpenAI Chat Deployment Name')
param openAiChatDeploymentName = 'gpt-4o'
@description('OpenAI Embedding Deployment Name')
param openAiEmbeddingDeploymentName = 'ada-3'
@description('OpenAI API Version')
param openAiApiVersion = '2024-10-21'

// App Service Plan Parameters
@description('The name of the App Service Plan')
param appServicePlanName = 'CZV-G-N-ALCS00-S-ASP-01'
@description('The SKU for the App Service Plan')
param appServicePlanSku = 'P1v2'

// Streaming API Parameters
@description('Streaming API Web App Name')
param streamingWebAppName = 'CZV-G-N-ALCS00-S-APP-01'
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
param orchestrationType = 'concurrent'

// App Service Plan Parameters 01
@description('The name of the App Service Plan')
param appServicePlanName01 = 'CZV-G-N-ALCS00-S-ASP-02'
@description('The SKU for the App Service Plan')
param appServicePlanSku01 = 'I1v2'
@description('The name of the App Service Environment')
param aseName = 'CZV-G-N-ALCS-S-ASE-01'

// Streaming API Parameters 01
@description('Streaming API Web App Name')
param streamingWebAppName01 = 'CZV-G-N-ALCS00-S-APP-02'

// Document Intelligence Parameters
@description('Document Intelligence Resource Name')
param docIntelAccountName = 'CZV-G-N-ALCS00-S-DOCINT-01'
@description('The name of the Document Intelligence diagnostic settings.')
param docIntelDiagnosticsName = 'CZV-G-N-ALCS00-S-DIAG-DOCINT-01'

// Key Vault parameters
@description('The name of the Key Vault.')
param keyVaultName = 'CZV-G-N-ALCS00-S-KV-01'

// Azure Workbooks Parameters
@description('The name of the workbook.')
param workbookName = 'faa52983-b9c4-4da2-ba06-1b3148c8933d'
@description('The display name for the workbook.')
param workbookDisplayName = 'CZV-G-N-ALCS00-S-AWB-01'
@description('The version for the workbook.')
param workbookVersion = 'Notebook/1.0'
@description('The category for the workbook.')
param workbookCategory = 'workbook'
@description('The kind for the workbook.')
param kind = 'shared'
