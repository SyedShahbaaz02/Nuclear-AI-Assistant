@description('The name of the App Service Plan.')
param name string
@description('The location for the App Service Plan.')
param location string = resourceGroup().location
@description('The sku for the App Service Plan.')
param skuName string
@description('The ASE for the App Service Plan.')
param aseId string?


resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = if (aseId != null) {
    name: name
    location: location
    sku: {
        name: skuName
    }
    kind: 'app,linux'
    properties: {
        reserved: true
        hostingEnvironmentProfile: {
            id: aseId
        }
    }
}

resource appServicePlan01 'Microsoft.Web/serverfarms@2022-03-01' = if (aseId == null) {
    name: name
    location: location
    sku: {
        name: skuName
    }
    kind: 'app,linux'
    properties: {
        reserved: true
    }
}

output appServicePlanId string = (appServicePlan.id != null) ? appServicePlan.id : appServicePlan01.id
