import os
import logging
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentContentFormat
from fastapi import Request, Response, APIRouter, HTTPException
from .reportability_manual import extract_sections_data

reportability_manual_search = APIRouter(tags=["reportability_manual"])
logger = logging.getLogger("web_api." + __name__)


def analyze_layout(url):

    document_intelligence_endpoint = os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
    document_intelligence_key = os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"]
    # Initialize the Document Intelligence client
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=document_intelligence_endpoint, credential=AzureKeyCredential(document_intelligence_key)
    )

    # Start the analysis process
    poller = document_intelligence_client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=AnalyzeDocumentRequest(url_source=url),
        output_content_format=DocumentContentFormat.MARKDOWN
    )

    # Retrieve the result
    result = poller.result()
    markdown_text = result.content
    return markdown_text


def get_blob_url_parts(blob_url: str) -> str:
    """
    Extracts the blob storage URL from the provided blob URL.
    """
    if not blob_url.startswith("https://"):
        raise ValueError("Invalid blob URL format. Must start with 'https://'.")

    # Assuming the blob URL is in the format:
    # https://<storage_account_name>.blob.core.windows.net/<container_name>/<blob_folder>/<blob_name>
    path = blob_url.replace('https://', '')
    parts = path.split('/')

    if len(parts) < 4:
        raise ValueError("Invalid blob URL format. Expected at least 4 parts.")
    # Extract storage account name, container name, and blob name
    storage_account_name = parts[0].split('.')[0]
    container_name = parts[1]
    blob_name = '/'.join(parts[2:])

    return storage_account_name, container_name, blob_name


def generate_reportability_manual_data(blob_storage_url: str) -> dict:
    try:
        markdown_result = analyze_layout(blob_storage_url)
        section_data = extract_sections_data(markdown_result)
        storage_account_name, container_name, blob_name = get_blob_url_parts(blob_storage_url)
        for section in section_data:
            section["storageAccountName"] = storage_account_name
            section["containerName"] = container_name
            section["blobName"] = blob_name
        return section_data

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@reportability_manual_search.route(path="/reportability_manual/data:generate", methods=["POST"])
async def main(req: Request) -> Response:
    try:
        body = await req.json()
        logging.debug(f"Request body: {body}")
    except ValueError as e:
        logging.exception(e)
        return Response("Body not valid JSON", status_code=400)

    values = []

    for record in body["values"]:
        record_id = record.get("recordId", "")
        blob_url = record["data"]["path"]
        section_data = generate_reportability_manual_data(blob_url)

        logger.debug(f"Blob URL: {blob_url}")

        values.append({
            "recordId": record_id,
            "data": {
                "sections": section_data
            }
        })

    response_body = {
        "values": values
    }

    return Response(content=json.dumps(response_body), media_type="application/json")
