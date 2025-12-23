from pydantic import BaseModel
from typing import Optional
import time
import os
import json
import requests
import openai
from collections import defaultdict
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence.models import ParagraphRole
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (AnalyzeResult, AnalyzeDocumentRequest, DocumentFieldType, DocumentSelectionMarkState)
from azure.core.credentials import AzureKeyCredential
from alcs_prompt import Prompts as pt


class LERmodel(BaseModel):
    ler_container_name: str
    connection_string: str
    openai_endpoint: str
    openai_key: str
    openai_version: str
    openai_deployment: str
    di_endpoint: str
    di_key: str
    min_sleep_time: Optional[int] = 5
    max_sleep_time: Optional[int] = 60


class LERservice():

    def __init__(self, report_model: LERmodel):
        self.ler_model = report_model

        self.ler_urls = list()
        with open(self.ler_model.ler_urls_fln, "r") as file:
            self.ler_urls = [line for line in file if line]
        self.ler_urls = [line.strip() for line in self.ler_urls if line.strip()]
        self.ler_urls = [url for url in self.ler_urls if url.endswith(".pdf")]

        self.blob_service_client = BlobServiceClient.from_connection_string(self.ler_model.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.ler_model.ler_container_name)

        self.openaiclient = openai.AzureOpenAI(
            api_version=self.ler_model.openai_version,
            azure_endpoint=self.ler_model.openai_endpoint,
            api_key=self.ler_model.openai_key
        )

    def downloadLERsFromNRC(self):
        print("Downloading LERs from NRC")
        sleeptime = self.ler_model.min_sleep_time
        os.makedirs(self.ler_model.ler_original_dir, exist_ok=True)

        for url in self.ler_urls:
            reportid = url.split("/")[-1]
            filepath = os.path.join(self.ler_model.ler_original_dir, reportid)
            if os.path.exists(filepath):
                print(f"File already exists - skipping: {reportid}")
                continue

            try:
                response = requests.get(
                    url,
                    stream=True,
                    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                             " (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"})
                response.raise_for_status()
                with open(filepath, "wb") as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        pdf_file.write(chunk)
                print(f"Downloaded: {reportid}")
                sleeptime = max(self.ler_model.min_sleep_time, sleeptime - 1)
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {url}: {e}")
                sleeptime = min(sleeptime + self.ler_model.min_sleep_time, self.ler_model.max_sleep_time)

            time.sleep(sleeptime)

        print("Done with downloading LERs")

    def uploadToAzure(self, data_dir: Optional[str] = None):

        if not data_dir or not os.path.exists(data_dir):
            print(f"Data directory does not exist: {data_dir}")
            return

        for fln in os.listdir(data_dir):
            local_file_path = os.path.join(data_dir, fln)
            with open(local_file_path, "rb") as form:
                self.container_client.upload_blob(name=local_file_path, data=form, overwrite=True)
            print(f"Uploaded: {fln}")

    def uploadOriginalLERs(self):
        print("Uploading LER pdfs to Azure Blob Storage")
        self.uploadToAzure(data_dir=self.ler_model.ler_original_dir)
        print("Done with uploading LER pdfs")

    def uploadProcessedLERs(self):
        print("Uploading processed LERs to Azure Blob Storage")
        self.uploadToAzure(data_dir=self.ler_model.ler_processed_dir)
        print("Done with uploading processed LERs")

    def downloadFromAzure(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        blobs = self.container_client.list_blobs(name_starts_with=data_dir)
        for blob in blobs:
            if blob.name == data_dir:
                print(f"Skipping directory blob: {blob.name}")
                continue
            if not blob.name.endswith(".pdf") and not blob.name.endswith(".txt"):
                print(f"Skipping non-document blob: {blob.name}")
                continue
            local_file_path = blob.name
            print(f"Downloading blob: {blob.name}")
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            with open(local_file_path, "wb") as file:
                blob_data = self.container_client.download_blob(blob.name)
                file.write(blob_data.readall())
            print(f"Downloaded: {blob.name}")

    def downloadOriginalLERsFromAzure(self):
        print("Downloading processed LERs from Azure Blob Storage")
        self.downloadFromAzure(self.ler_model.ler_original_dir)
        print("Done with downloading processed LERs")

    def downloadProcessedLERsFromAzure(self):
        print("Downloading processed LERs from Azure Blob Storage")
        self.downloadFromAzure(self.ler_model.ler_processed_dir)
        print("Done with downloading processed LERs")

    def isLERContinutationSection(self, section, analyzed_result):
        LER_CONTINUATION_TITLE = "LICENSEE EVENT REPORT (LER) CONTINUATION SHEET"
        _, first_element_kind, index = section.elements[0].split('/')
        if first_element_kind != 'paragraphs':
            return False
        first_paragraph = analyzed_result.paragraphs[int(index)]
        if first_paragraph.role == ParagraphRole.TITLE and first_paragraph.content == LER_CONTINUATION_TITLE:
            return True
        else:
            return False

    def processContinuationSections(self, section_index, analyzed_result, narrative_paragraphs):

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
                'Estimated burden per response to comply with this mandatory collection request: 80 hours. Reported '
                'lessons learned are incorporated into the licensing process and fed back to industry. Send comments '
                'regarding burden estimate to the FOIA, Library, and Information Collections Branch (T-6 A10M), '
                'U. S. Nuclear Regulatory Commission, Washington, DC 20555-0001, or by email to '
                'Infocollects.Resource@nrc.gov, and the OMB reviewer at: OMB Office of Information and Regulatory '
                'Affairs, (3150-0104), Attn: Desk Officer for the Nuclear Regulatory Commission, 725 17th Street NW, '
                'Washington, DC 20503. The NRC may not conduct or sponsor, and a person is not required to respond to, '
                'a collection of information unless the document requesting or requiring the collection'
                ' displays a currently valid OMB control number.'
            )
        }

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
                self.processContinuationSections(int(index), analyzed_result, narrative_paragraphs)

    def processRootSection(self, analyzed_result, narrative_paragraphs):
        # Sections are organized as a tree
        # The root section contains all the seperate sections as children
        # We only want to process sections that have a title of LER_CONTINUATION_TITLE
        # Since that contains Narrative information
        section_tree_root = analyzed_result.sections[0]
        for section in section_tree_root.elements:
            _, kind, index = section.split('/')
            section = analyzed_result.sections[int(index)]
            if self.isLERContinutationSection(section, analyzed_result):
                self.processContinuationSections(int(index), analyzed_result, narrative_paragraphs)

    def analyze_layout(self, pdf_path):

        document_intelligence_client = DocumentIntelligenceClient(
            endpoint=self.ler_model.di_endpoint,
            credential=AzureKeyCredential(self.ler_model.di_key)
            )

        with open(pdf_path, "rb") as f:
            file_bytes = f.read()
            poller = document_intelligence_client.begin_analyze_document(
                "custom-ler-2025-03-26", AnalyzeDocumentRequest(bytes_source=file_bytes))
            result: AnalyzeResult = poller.result()

        if len(result.documents) != 1:
            print(f"Expected 1 document, but got {len(result.documents)}")
            return None

        narrative_paragraphs = []
        self.processRootSection(result, narrative_paragraphs)

        document = result.documents[0]

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
                if (
                    field.type == DocumentFieldType.SELECTION_MARK
                    and field.value_selection_mark == DocumentSelectionMarkState.SELECTED
                ):
                    cfr_requirements.append(name)

            document_data = {
                "doc_name" : f"{pdf_path}",
                "ler_number": f"{ler_number}",
                "report_date": report_datetime,
                "event_date": event_datetime,
                "facility_name": document.fields.get("Facility Name").content,
                "title": document.fields.get("Title").content,
                "cfr_requirements": cfr_requirements,
                "abstract": document.fields.get("Abstract").content,
                "narrative": '\n'.join(narrative_paragraphs)
            }

            print(json.dumps(document_data, indent=4))
            return document_data

        return None

    def processLERs(self):
        data_dir = self.ler_model.ler_original_dir
        processed_dir = self.ler_model.ler_processed_dir
        if not os.path.exists(data_dir):
            print(f"Original LER directory does not exist: {data_dir}")
            return

        original_LERs = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
        for fln in original_LERs:
            pdf_path = os.path.join(data_dir, fln)
            form_name = fln.split('.')[0]
            filepath = os.path.join(processed_dir, f"{form_name}.txt")
            if os.path.exists(filepath):
                print(f"File already exists - skipping: {form_name}")
                continue
            try:
                print(f"Processing {fln}")
                output = self.analyze_layout(pdf_path)
                print(f"Finished processing {fln}")
            except Exception as e:
                print(f"Error processing {fln}: {e}")
                continue
            if not output:
                continue
            with open(os.path.join(processed_dir, f"{form_name}.txt"), 'w') as f: json.dump(output, f, indent=4)
        print("Done with processing LERs")

    def getLERdescriptiveStats(self) -> dict:

        noabstract = list()
        nonarrative = list()
        counts = defaultdict(int)
        mult_counts = defaultdict(int)

        processed_files = [f for f in os.listdir(self.ler_model.ler_processed_dir) if f.endswith('.txt')]
        for fln in processed_files:
            filepath = os.path.join(self.ler_model.ler_processed_dir, fln)
            with open(filepath, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {fln}: {e}")
                    continue
                mult_counts[len(data['cfr_requirements'])] += 1
                for cfr in data['cfr_requirements']:
                    counts[cfr] += 1

                if not data["abstract"]:
                    noabstract.append(fln)
                if not data["narrative"]:
                    nonarrative.append(fln)

        return {"noabstract": noabstract, "nonarrative": nonarrative, "counts": counts, "mult_counts": mult_counts}

    def testLLM(self) -> str:
        response = self.openaiclient.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a scientist"},
                {"role": "user", "content": "Tell me a short science joke"},
            ],
            temperature=0.0,
            model=self.ler_model.openai_deployment
        )

        return "Works" if response.choices[0].message.content else "Failed"

    def removeCFRReferences(self, content: str) -> str:
        response = self.openaiclient.chat.completions.create(
            messages=[
                {"role": "system", "content": pt.remove_cfr_references_system_prompt.value},
                {"role": "user", "content": content}
            ],
            temperature=0.0,
            model=self.ler_model.openai_deployment
            )
        return response.choices[0].message.content
