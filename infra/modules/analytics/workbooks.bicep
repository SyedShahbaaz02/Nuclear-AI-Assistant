@description('The name of the Azure Workbook.')
param workbookName string
@description('The location for the workbook.')
param location string
@description('The kind for the workbook.')
param kind string
@description('The display name for the workbook.')
param displayName string
@description('The serializedData for the workbook (JSON content as string).')
var workbookContent = loadTextContent('workbooks.json')
@description('The version of the notebook')
param workbookVersion string
@description('The category of the workbook.')
param workbookCategory string
@description('The source ID for the workbook.')
param sourceId string

resource workbook 'Microsoft.Insights/workbooks@2023-06-01' = {
  name: workbookName
  location: location
  kind: kind
  properties: {
    category: workbookCategory
    displayName: displayName
    serializedData: workbookContent
    version: workbookVersion
    sourceId: sourceId
    tags: []
    }
}
