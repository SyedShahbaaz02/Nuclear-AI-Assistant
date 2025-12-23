import os
import json
import logging

from azure.storage.blob import BlobClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from fastapi import Request, Response, APIRouter, HTTPException

from .nureg_search_field_extraction import (
    extract_sections,
    extract_5072_content_per_subsection,
    extract_5073_content_per_subsection,
    extract_description_content_per_subsection,
    extract_discussions_content_per_subsection,
    extract_example_content_per_subsection,
    extract_page_numbers_per_subsection,
    remove_internal_fields,
)

nureg_search = APIRouter(tags=["nureg"])
logger = logging.getLogger("web_api.nureg_search")


def download_pdf_blob(blob_url: str) -> bytes:
    key = os.environ["AZURE_BLOB_KEY"]
    blob_client = BlobClient.from_blob_url(blob_url=blob_url, credential=key)
    downloader = blob_client.download_blob()
    return downloader.readall()


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


def analyze_document(document_intelligence_client: DocumentIntelligenceClient, pdf_bytes: bytes) -> dict:
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-layout",
        body=pdf_bytes
    )
    result = poller.result()
    return result


def generate_sections(blob_url: str) -> dict:
    try:
        pdf_bytes = download_pdf_blob(blob_url=blob_url)

        document_intelligence_endpoint = os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
        document_intelligence_key = os.environ["AZURE_DOCUMENT_INTELLIGENCE_KEY"]
        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=document_intelligence_endpoint,
            credential=AzureKeyCredential(document_intelligence_key))
        analysis_result = analyze_document(document_intelligence_client, pdf_bytes)
        sections = extract_sections(analysis_result, "3.2")
        sections = extract_5072_content_per_subsection(analysis_result, sections, "3.2")
        sections = extract_5073_content_per_subsection(analysis_result, sections, "3.2")
        sections = extract_description_content_per_subsection(analysis_result, sections, "3.2")
        sections = extract_discussions_content_per_subsection(analysis_result, sections, "3.2")
        sections = extract_example_content_per_subsection(analysis_result, sections, "3.2")
        sections = extract_page_numbers_per_subsection(analysis_result, sections, "3.2")
        sections = remove_internal_fields(sections)
        storage_account_name, container_name, blob_name = get_blob_url_parts(blob_url)
        for section in sections:
            section["storageAccountName"] = storage_account_name
            section["containerName"] = container_name
            section["blobName"] = blob_name
        return sections
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@nureg_search.route(path="/nureg/sections:generate", methods=["POST"])
async def main(req: Request) -> Response:
    try:
        body = await req.json()
        logger.debug(f"Request body: {body}")
    except ValueError as e:
        logger.exception(e)
        return Response("Body not valid JSON", status_code=400)

    values = []

    for record in body["values"]:
        record_id = record.get("recordId", "")
        blob_url = record["data"]["path"]
        sections = generate_sections(blob_url)
        logger.debug(f"Blob URL: {blob_url}")

        values.append({
            "recordId": record_id,
            "data": {
                "sections": sections
            }
        })

    response_body = {
        "values": values
    }

    return Response(content=json.dumps(response_body), media_type="application/json")
