metadata description = 'Configures the application insights infrastructure for the Ask Licensing service.'

@description('The workspace name to associate with applications insights.')
param workspaceName string

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
    name: workspaceName
}

@description('The name of the application insights instance.')
param name string
@description('The location to deploy application insights to.')
param location string
@description('The kind of application insights instance.')
param kind string = 'web'
@description('The type of the application that is being monitored.')
param applicationType string = 'web'

resource ingestionInsights 'Microsoft.Insights/components@2020-02-02' = {
    name: name
    location: location
    kind: kind
    properties: {
        Application_Type: applicationType
        WorkspaceResourceId: workspace.id
    }
}

output appInsightsName string = ingestionInsights.name
output appInsightsId string = ingestionInsights.id
