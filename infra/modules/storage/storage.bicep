metadata description = 'The storage accounts for the Ask Licensing service.'

// The storage account
@description('The name of the storage account.')
param name string
@description('The location for the storage account.')
param location string
@description('The SKU to use for creating the storage account.')
param sku string
@description('The kind of storage account to create.')
param kind string
@description('The identity type to use for the storage account.')
param identityType string = 'SystemAssigned'
@description('The access tier to assign to the storage account.')
param accessTier string = 'Hot'
@description('Whether to allow public access to blobs or containers.')
param allowBlobPublicAccess bool = false
@description('List of IP addresses or CIDR ranges to allow access to the storage account.')
param allowedIpAddresses array = []
@description('Default Action for network ACLs.')
param defaultAction string = 'Allow'

var combinedWithAzDoIpAddresses = union(allowedIpAddresses, [
  '20.37.158.0/23'
  '52.150.138.0/24'
  '20.42.5.0/24'
  '20.41.6.0/23'
  '40.80.187.0/24'
  '40.119.10.0/24'
  '40.82.252.0/24'
  '20.42.134.0/23'
  '20.125.155.0/24'
])

resource storage 'Microsoft.Storage/storageAccounts@2024-01-01' = {
    name: name
    location: location
    sku: {
        name: sku
    }
    kind: kind
    identity: {
        type: identityType
    }
    properties: {
        supportsHttpsTrafficOnly: true
        networkAcls: {
            defaultAction: defaultAction
            bypass: 'AzureServices, Logging, Metrics'
            ipRules: [
                for ip in combinedWithAzDoIpAddresses: {
                    action: 'Allow'
                    value: ip
                }
            ]
        }
        accessTier: accessTier
        allowBlobPublicAccess: allowBlobPublicAccess
    }
}

// The CORS policy for the blob service
@description('The CORS rules for the blob service.')
param cors object = {
    corsRules: [
        {
            allowedHeaders: [
                '*'
            ]
            allowedMethods: [
                'DELETE'
                'GET'
                'HEAD'
                'MERGE'
                'OPTIONS'
                'PATCH'
                'POST'
                'PUT'
            ]
            allowedOrigins: [
                'https://formrecognizer.appliedai.azure.us'
            ]
            exposedHeaders: [
                '*'
            ]
            maxAgeInSeconds: 120
        }
    ]
}

// The storage policies and containers
@description('The names of the containers that will used to store documents for ingestion.')
param storageContainerNames array = []
@description('The retention policy for deleted containers.')
param containerDeleteRetentionPolicy object
@description('The retention policy for deleted blobs.')
param deleteRetentionPolicy object
@description('Whether to allow public access to the container.')
param publicAccess string = 'None'
@description('The default encryption scope for the container.')
param defaultEncryptionScope string = '$account-encryption-key'
@description('Whether to deny encryption scope override for the container.')
param denyEncryptionScopeOverride bool = false

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
    parent: storage
    name: 'default'
    properties: {
        containerDeleteRetentionPolicy: containerDeleteRetentionPolicy
        cors: cors
        deleteRetentionPolicy: deleteRetentionPolicy
    }

    resource ingestionContainers 'containers' =  [for containerName in storageContainerNames: {
        name: containerName
        properties: {
            publicAccess: publicAccess
            defaultEncryptionScope: defaultEncryptionScope
            denyEncryptionScopeOverride: denyEncryptionScopeOverride
        }
    }]
}

output storageAccountName string = storage.name
