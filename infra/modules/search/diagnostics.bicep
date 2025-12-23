metadata description = 'Associates the Log Analytics instance with AI Search.'

@description('The name of the application insights to associate with.')
param workspaceName string

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
    name: workspaceName
}

@description('The name of the AI Search instance.')
param searchName string

resource search 'Microsoft.Search/searchServices@2023-11-01' existing = {
    name: searchName
}

@description('The name of the diagnostic settings.')
param name string
@description('Determines whether the logs are enabled.')
param logsEnabled bool = true
@description('The timegrain of the metrics in ISO8601 format.')
param timeGrain string = 'PT1M'
@description('Determines whether the metrics are enabled.')
param metricsEnabled bool = true

resource aiSearchDiagnosticSettings 'microsoft.insights/diagnosticSettings@2021-05-01-preview' = {
    name: name
    scope: search
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
