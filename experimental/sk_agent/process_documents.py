import os
import json

from dotenv import load_dotenv
from urllib.parse import quote

from openai import AzureOpenAI
from azure.identity import ClientSecretCredential
from azure.core.credentials import AzureKeyCredential

from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeResult,
    AnalyzeDocumentRequest,
    DocumentFieldType,
    DocumentSelectionMarkState,
    ParagraphRole)

from azure.search.documents import SearchClient

global LER_CONTINUATION_TITLE
global EXCLUDED_PARAGRAPH_CONTENT


def list_blob_urls(storage_account_name, container_name) -> list[str]:
    """
    Lists all blob URLs in the specified Azure Blob Storage container that start with 'ler' and end with '.pdf'.

    Args:
        storage_account_name (str): The name of the Azure storage account.
        container_name (str): The name of the container in the storage account.

    Returns:
        list[str]: A list of blob URLs.
    """
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
    # create a service principal credential
    blob_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.usgovcloudapi.net",
        credential=blob_credential
    )
    container_client = blob_service_client.get_container_client(container_name)
    blob_urls = []
    for blob in container_client.list_blobs(name_starts_with='ler'):
        if blob.name.endswith('.pdf'):
            safe_blob_name = quote(blob.name)  # Automatically replaces spaces with %20 and makes it URL-safe
            blob_url = f"https://{storage_account_name}.blob.core.usgovcloudapi.net/{container_name}/{safe_blob_name}"
            blob_urls.append(blob_url)
    return blob_urls


def isLERContinutationSection(section, analyzed_result):
    """
    Checks if a given section is a Licensee Event Report (LER) continuation section.

    Args:
        section: The section to check.
        analyzed_result: The analyzed result containing document structure.

    Returns:
        bool: True if the section is an LER continuation section, False otherwise.
    """
    _, first_element_kind, index = section.elements[0].split('/')

    if first_element_kind != 'paragraphs':
        return False

    first_paragraph = analyzed_result.paragraphs[int(index)]
    if first_paragraph.role == ParagraphRole.TITLE and first_paragraph.content == LER_CONTINUATION_TITLE:
        return True
    else:
        return False


def processContinuationSections(section_index, analyzed_result, narrative_paragraphs):
    """
    Recursively processes continuation sections to extract narrative paragraphs.

    Args:
        section_index (int): The index of the section to process.
        analyzed_result: The analyzed result containing document structure.
        narrative_paragraphs (list): A list to store extracted narrative paragraphs.
    """
    section = analyzed_result.sections[section_index]

    for element in section.elements:
        _, kind, index = element.split('/')
        if kind == 'paragraphs':
            paragraph = analyzed_result.paragraphs[int(index)]
            # skip the first paragraph if it contains boilerplate text
            if paragraph.content in EXCLUDED_PARAGRAPH_CONTENT:
                continue
            narrative_paragraphs.append(paragraph.content)
        elif kind == 'sections':
            processContinuationSections(int(index), analyzed_result, narrative_paragraphs)


def processRootSection(analyzed_result, narrative_paragraphs):
    """
    Processes the root section of the document to extract narrative paragraphs from LER continuation sections.

    Args:
        analyzed_result: The analyzed result containing document structure.
        narrative_paragraphs (list): A list to store extracted narrative paragraphs.
    """
    # Sections are organized as a tree
    # The root section contains all the seperate sections as children
    # We only want to process sections that have a title of LER_CONTINUATION_TITLE
    # Since that contains Narrative information
    section_tree_root = analyzed_result.sections[0]
    for section in section_tree_root.elements:
        _, kind, index = section.split('/')
        section = analyzed_result.sections[int(index)]
        if isLERContinutationSection(section, analyzed_result):
            processContinuationSections(int(index), analyzed_result, narrative_paragraphs)


def analyze_layout(url):
    """
    Analyzes the layout of a document using Azure Document Intelligence and extracts relevant data.

    Args:
        url (str): The URL of the document to analyze.

    Writes:
        JSON files containing extracted data to the 'index_data' directory.
    """
    di_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    di_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    # sample document
    formUrl = url
    blob_name = formUrl.split('/')[-1].replace('%20', ' ')
    blob_prefix = blob_name.split(' ')[0]
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=di_endpoint, credential=AzureKeyCredential(di_key)
    )

    poller = document_intelligence_client.begin_analyze_document(
        "custom-ler-2025-03-26", AnalyzeDocumentRequest(url_source=formUrl))

    result: AnalyzeResult = poller.result()

    index_data = []
    narrative_paragraphs = []
    processRootSection(result, narrative_paragraphs)

    for document in result.documents:
        if document.doc_type == "custom-ler-2025-03-26":
            event_year = document.fields.get("Event Date Year").content
            event_month = document.fields.get("Event Date Month").content
            event_day = document.fields.get("Event Date Day").content
            event_datetime = f"{event_year}-{event_month}-{event_day}T00:00:00Z"

            report_year = document.fields.get("Report Date Year").content
            report_day = document.fields.get("Report Date Day").content
            report_month = document.fields.get("Report Date Month").content
            report_datetime = f"{report_year}-{report_month}-{report_day}T00:00:00Z"

            ler_year = document.fields.get("LER Number Year").content
            ler_seq_no = document.fields.get("LER Number Seq No").content
            ler_rev_no = document.fields.get("LER Number Rev No").content
            ler_number = f"{ler_year}-{ler_seq_no}-{ler_rev_no}"

            cfr_requirements = []
            for name, field in document.fields.items():
                if field.type == DocumentFieldType.SELECTION_MARK and \
                        field.value_selection_mark == DocumentSelectionMarkState.SELECTED:
                    cfr_requirements.append(name)

            document_data = {
                "ler_number": f"{blob_prefix}_{ler_number}",
                "report_date": report_datetime,
                "event_date": event_datetime,
                "facility_name": document.fields.get("Facility Name").content,
                "title": document.fields.get("Title").content,
                "cfr_requirements": cfr_requirements,
                "abstract": document.fields.get("Abstract").content,
                "narrative": '\n'.join(narrative_paragraphs)
            }
            index_data.append(document_data)

    # Write index_data to JSON files
    with open(f"index_data/{blob_name}_index.json", "w") as index_file:
        json.dump(index_data, index_file, indent=4)


def get_embedding(text):
    """
    Generates an embedding vector for the given text using Azure OpenAI.

    Args:
        text (str): The text to generate an embedding for.

    Returns:
        list[float]: The embedding vector.
    """
    openai_client = AzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    )
    get_embeddings_response = openai_client.embeddings.create(model=os.getenv("AZURE_EMBEDDING_MODEL_NAME"), input=text)
    return get_embeddings_response.data[0].embedding


def embed_documents():
    """
    Adds embedding vectors to the analyzed documents and writes them to the 'index_data/embedded' directory.
    """
    for blob in os.listdir("./index_data"):
        if blob.endswith("_index.json"):
            doc_json = json.loads(open(f"./index_data/{blob}").read())[0]
            doc_json["abstractVector"] = get_embedding(doc_json["abstract"])
            doc_json["titleVector"] = get_embedding(doc_json["title"])
            doc_json["narrativeVector"] = get_embedding(doc_json["narrative"])
            with (open(f"./index_data/embedded/{blob}", "w")) as f:
                f.write(json.dumps(doc_json))


def upload_data():
    """
    Uploads embedded document data to an Azure Cognitive Search index.
    """
    # Retrieve configuration from environment variables
    search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
    search_index_name = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")
    search_api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")

    # Authenticate using AzureKeyCredential
    search_credential = AzureKeyCredential(search_api_key)

    # Initialize the SearchClient
    search_client = SearchClient(endpoint=search_endpoint, index_name=search_index_name, credential=search_credential)

    # Directory containing JSON files
    index_data_folder = "./index_data/embedded"

    # Upload documents from JSON files in the folder
    for filename in os.listdir(index_data_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(index_data_folder, filename)
            try:
                with open(file_path, "r") as file:
                    documents = json.load(file)
                    result = search_client.upload_documents(documents)
                    print(f"Uploaded {filename}: {result}")
            except Exception as e:
                print(f"An error occurred while uploading {filename}: {e}")


def main():
    """
    Main function to process documents, generate embeddings, and upload data to Azure Cognitive Search.
    """
    blob_urls = list_blob_urls(
        storage_account_name="czvgnalcs00dsta001", container_name="non-eci"
    )

    for blob_url in blob_urls:
        print(f"Processing: {blob_url}")
        analyze_layout(blob_url)

    # add embeddings to each of the analyzed blobs
    for blob in os.listdir("./index_data"):
        if blob.endswith("_index.json"):
            doc_json = json.loads(open(f"./index_data/{blob}").read())[0]
            doc_json["abstractVector"] = get_embedding(doc_json["abstract"])
            doc_json["titleVector"] = get_embedding(doc_json["title"])
            doc_json["narrativeVector"] = get_embedding(doc_json["narrative"])
            with (open(f"./index_data/embedded/{blob}", "w")) as f:
                f.write(json.dumps(doc_json))

    upload_data()


if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    LER_CONTINUATION_TITLE = "LICENSEE EVENT REPORT (LER) CONTINUATION SHEET"

    EXCLUDED_PARAGRAPH_CONTENT = {
        'LICENSEE EVENT REPORT (LER) CONTINUATION SHEET',
        'NARRATIVE',
        'NRC FORM 366A (04-02-2024)',
        (
            '(See NUREG-1022, R.3 for instruction and guidance for completing this form'
            'http://www.nrc.gov/reading-rm/doc-collections/nuregs/staff/sr1022/r3/)'
        ),
        'APPROVED BY OMB: NO. 3150-0104 EXPIRES: 04/30/2027',
        (
            'Estimated burden per response to comply with this mandatory collection '
            'request: 80 hours. Reported lessons learned are incorporated into the '
            'licensing process and fed back to industry. Send comments regarding '
            'burden estimate to the FOIA, Library, and Information Collections Branch '
            '(T-6 A10M), U. S. Nuclear Regulatory Commission, Washington, DC 20555-0001, '
            'or by email to Infocollects.Resource@nrc.gov, and the OMB reviewer at: '
            'OMB Office of Information and Regulatory Affairs, (3150-0104), Attn: Desk '
            'Officer for the Nuclear Regulatory Commission, 725 17th Street NW, '
            'Washington, DC 20503. The NRC may not conduct or sponsor, and a person is '
            'not required to respond to, a collection of information unless the document '
            'requesting or requiring the collection displays a currently valid OMB '
            'control number.'
        )
    }
    main()
