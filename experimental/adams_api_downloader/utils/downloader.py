import requests
import os
from config import DOWNLOAD_DIR


def download_pdf(accession_number):
    
    # Extract first 4 characters after 'ML' to form the folder
    folder_segment = accession_number[2:6]  # e.g., '2506' from 'ML25062A082'

    # Construct the NRC Docs URL
    url = f"https://www.nrc.gov/docs/ML{folder_segment}/{accession_number}.pdf"
    print(f"📥 Attempting: {url}")
    print(url)
    
    response = requests.get(url)

    if response.status_code == 200:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        file_path = os.path.join(DOWNLOAD_DIR, f"{accession_number}.pdf")
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded: {file_path}")
    else:
        print(f"Failed to download {accession_number} (HTTP {response.status_code})")
