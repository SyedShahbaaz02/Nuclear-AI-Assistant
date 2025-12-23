@description('Name of the Web App')
param webAppName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Application Insights Resource Name')
param applicationInsightsName string

@description('Application Insights Instrumentation Key')
param appServicePlanId string

@description('Open AI Resource Name')
param openAiName string

@description('OpenAI Chat Model Deployment Name')
param openAiChatDeploymentName string = 'gpt-4o'

@description('OpenAI Embedding Model Deployment Name')
param openAiEmbeddingDeploymentName string = 'ada-3'

@description('OpenAI API Version')
param openAiApiVersion string

@description('AI Search Endpoint URL')
param aiSearchName string

@description('NUREG Index Name')
param nuregIndexName string

@description('Reportability Manual Index Name')
param reportabilityManualIndexName string

@description('TechSpec Index Name')
param tsIndexName string

@description('UFSAR Index Name')
param ufsarIndexName string

@description('Storage Account Name')
param storageAccountName string

@description('Document intelligence Account Name')
param docIntelAccountName string

@description('Log Level for the Streaming API Web App')
param streamingWebAppLogLevel string = 'INFO'

@description('Document SAS token expiration period in days')
param documentSasTokenExpirationDays string

@description('The size of the buffer for the streaming API web app.')
param streamBufferSize int

@description('App Service Environment')
param aseId string

@description('The orchestration type for the streaming API web app.')
param orchestrationType string

resource openAi 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
    name: openAiName
}

resource aiSearch 'Microsoft.Search/searchServices@2023-11-01' existing = {
    name: aiSearchName
}

resource docintel 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
    name: docIntelAccountName
}

resource storage 'Microsoft.Storage/storageAccounts@2022-09-01' existing = {
    name: storageAccountName
}

var aiSearchKey = aiSearch.listAdminKeys().primaryKey
var aiSearchUrl = 'https://${aiSearchName}.search.azure.us'
var openAiKey = openAi.listKeys().key1
var openAiUrl = 'https://${openAi.name}.openai.azure.us/'
var docintelKey = docintel.listKeys().key1
var docintelUrl = 'https://${docIntelAccountName}.cognitiveservices.azure.us/'
var blobKey = storage.listKeys().keys[0].value

module api '../host/webapp01.bicep' = {
    params: {
        webAppName: webAppName
        location: location
        appSettings: {
            AZURE_OPENAI_ENDPOINT: openAiUrl
            AZURE_OPENAI_API_KEY: openAiKey
            AZURE_OPENAI_DEPLOYMENT: openAiChatDeploymentName
            AZURE_EMBEDDING_DEPLOYMENT: openAiEmbeddingDeploymentName
            AZURE_OPENAI_API_VERSION: openAiApiVersion
            AZURE_SEARCH_SERVICE_ENDPOINT: aiSearchUrl
            AZURE_SEARCH_API_KEY: aiSearchKey
            AZURE_SEARCH_NUREG_INDEX_NAME: nuregIndexName
            AZURE_SEARCH_REPORTABILITY_MANUAL_INDEX_NAME: reportabilityManualIndexName
            AZURE_SEARCH_TECHSPEC_INDEX_NAME: tsIndexName
            AZURE_SEARCH_UFSAR_INDEX_NAME: ufsarIndexName
            AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: docintelUrl
            AZURE_DOCUMENT_INTELLIGENCE_KEY: docintelKey
            AZURE_BLOB_KEY: blobKey
            LOG_LEVEL: streamingWebAppLogLevel
            SAS_TOKEN_EXPIRATIONS_DAYS: documentSasTokenExpirationDays
            STREAM_BUFFER_SIZE: streamBufferSize
            ORCHESTRATION_TYPE: orchestrationType
        }
        applicationInsightsName: applicationInsightsName
        appServicePlanId: appServicePlanId
        aseId: aseId
    }
}

output functionAppName string = api.name
