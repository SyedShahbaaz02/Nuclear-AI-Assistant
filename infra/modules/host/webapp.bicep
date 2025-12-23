@description('Name of the Web App')
param webAppName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Application Insights Resource Name')
param applicationInsightsName string = ''

@description('App Service Plan Resource Id')
param appServicePlanId string

@description('App Settings to apply to the Web App')
param appSettings object = {}

@description('Allowed origins for hitting the API')
param allowedOrigins array = ['*']

param alwaysOn bool = true

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
    name: applicationInsightsName
}

resource webApp 'Microsoft.Web/sites@2022-09-01' = {
    name: webAppName
    location: location
    kind: 'app'
    identity: {
        type: 'SystemAssigned'
    }
    properties: {
        serverFarmId: appServicePlanId
        httpsOnly: true
        clientCertEnabled: true
        clientCertMode: 'Optional'
        siteConfig: {
            minTlsVersion: '1.3'
            http20Enabled: true
            linuxFxVersion: 'PYTHON|3.11'
            alwaysOn: alwaysOn
            cors: {
                allowedOrigins: union([ 'https://portal.azure.com', 'https://ms.portal.azure.com' ], allowedOrigins)
            }
            healthCheckPath: '/'
        }
    }

    resource configAppSettings 'config' = {
        name: 'appsettings'
        properties: union(appSettings, {
            APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
            APPINSIGHT_INSTRUMENTATIONKEY: appInsights.properties.InstrumentationKey
            APPINSIGHTS_PROFILERFEATURE_VERSION: '1.0.0'
            APPINSIGHTS_SNAPSHOTFEATURE_VERSION: '1.0.0'
            ApplicationInsightsAgent_EXTENSION_VERSION: '~3'
            SCM_DO_BUILD_DURING_DEPLOYMENT: 1
        })
    }
}

resource configLogs 'Microsoft.Web/sites/config@2022-03-01' = {
    name: 'logs'
    parent: webApp
    properties: {
        applicationLogs: { fileSystem: { level: 'Verbose' } }
        detailedErrorMessages: { enabled: true }
        failedRequestsTracing: { enabled: true }
        httpLogs: { fileSystem: { enabled: true, retentionInDays: 1, retentionInMb: 35 } }
    }
}

output name string = webApp.name
output uri string = 'https://${webApp.properties.defaultHostName}'
