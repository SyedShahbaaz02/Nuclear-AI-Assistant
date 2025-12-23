# Overview

This folder, `nureg_search`, contains code for the web skill used by AI search to extract the 14 subsections of Chapter
3.2 from a PDF of NUREG-1022. Custom code is provided in the
[`nureg_search_field_extraction.py`](./nureg_search_field_extraction.py) that helps extract fields that we need defined
in the index under `./infra/config/aisearch/indexes/indexes/nureg_section_3_2.json`. The
[`function_app.py`](./function_app.py) provides a [FastAPI](https://fastapi.tiangolo.com/) endpoint for extracting
structured section data from the document stored in Azure Blob Storage.

When a POST request is made to `/search/nureg/sections:generate` with a blob URL in the JSON payload, the function
downloads the PDF from Azure Blob Storage, uses Azure Document Intelligence to analyze the document layout, extracts and
organizes relevant section content, and returns the structured section data as JSON.

## Testing Locally

### Preparation and Debugging

To begin debugging locally, first follow the
[preparation instructions in the Web App documentation](../README.md#preparing-to-run-locally), then follow the
[debugging locally instructions](../README.md#debugging-the-web-app-locally).

#### Using the VSCode "REST Client" Extension

Using the [instructions for the REST client](../README.md#using-the-vscode-rest-client-extension) the
[streaming test](../tests/integration/nureg_section_3.2.rest) file can be used to exercise the endpoint locally.

## Testing Deployed Web App Endpoint

A prerequisite to this is to ensure the web app is deployed. You should use the DevOps Pipeline to deploy the Web App.

With the Web API deployed first, locate the Azure App Service resource in the Azure Portal and copy the custom domain
value in the Overview section. Next, go to the [REST test file](../tests/integration/nureg_section_3.2.rest)
and replace `http://localhost:7071` with `https://<custom-domain-url-endpoint>`. Click "Send Request" and you should
 see the response output.

***Be sure to revert any changes to the `.rest` file before committing any code.***
