@description('The name of the Log Analytics Workspace to associate with.')
param workspaceName string

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
    name: workspaceName
}

@description('The name of the Document Intelligence instance.')
param docIntelName string

resource docIntel 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
    name: docIntelName
}

@description('The name of the diagnostic settings.')
param name string
@description('Determines whether the logs are enabled.')
param logsEnabled bool = true
@description('The timegrain of the metrics in ISO8601 format.')
param timeGrain string = 'PT1M'
@description('Determines whether the metrics are enabled.')
param metricsEnabled bool = true


resource docIntelDiagnosticSettings 'microsoft.insights/diagnosticSettings@2021-05-01-preview' = {
    name: name
    scope: docIntel
    properties: {
        workspaceId: workspace.id
        logs: [
                {
                    categoryGroup: 'AllLogs'
                    enabled: logsEnabled
                }
            ]
        metrics: [
            {
                category: 'AllMetrics'
                timeGrain: timeGrain
                enabled: metricsEnabled
            }
        ]
    }
}
