# Overview

This folder, `reportability_manual_search`, contains code that extracts structured section data from a PDF of the
Reportability Manual. Custom code is provided in
[reportability_manual.py](./saf_search_field_extraction.py) to extract the fields defined in the index at
[reportability_manual_index.json](../../../infra/config/aisearch/indexes/reportability_manual_index.json). The [main.py](./main.py)
provides a [FastAPI](https://fastapi.tiangolo.com/) endpoint for extracting structured section data from PDF documents
stored in Azure Blob Storage.

When a POST request is made to `/search/reportability_manual/data:generate` with a blob URL, the function downloads the
PDF from Azure Blob Storage, uses Azure Document Intelligence to analyze the document layout, extracts and organizes
relevant section content, and returns the structured section data as JSON.

## Testing Locally

### Preparation and Debugging

To begin debugging locally, first follow the
[preparation instructions in the Web App documentation](../README.md#preparing-to-run-locally), then follow the
[debugging locally instructions](../README.md#debugging-the-web-app-locally).

#### Using the VSCode "REST Client" Extension

Using the [instructions for the REST client](../README.md#using-the-vscode-rest-client-extension) the
[streaming test](../tests/integration/sa) file can be used to exercise the endpoint locally.

## Testing Deployed Web App Endpoint

A prerequisite to this is to ensure the web app is deployed. You should use the DevOps Pipeline to deploy the Web App.

With the Web API deployed first, locate the Azure App Service resource in the Azure Portal and copy the custom domain
value in the Overview section. Next, go to the
[REST test file](../tests/integration/reportability_manual_data_extract.rest)
and replace `http://localhost:7071` with `https://<custom-domain-url-endpoint>`. Click "Send Request" and you should
 see the response output.

***Be sure to revert any changes to the `.rest` file before committing any code.***
