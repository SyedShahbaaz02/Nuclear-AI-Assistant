from api.query_builder import build_query
from api.fetcher import fetch_xml
from utils.parser import extract_accession_numbers
from utils.downloader import download_pdf

def main():
    print("🔧 Building query...")
    full_url = build_query()

    print("Fetching results from ADAMS API...")
    xml_content = fetch_xml(full_url)

    print("Parsing accession numbers...")
    accession_numbers = extract_accession_numbers(xml_content)

    print(f"Found {len(accession_numbers)} document(s). Starting download...\n")
    for acc in accession_numbers:
        download_pdf(acc)

if __name__ == "__main__":
    main()
