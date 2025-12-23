import xml.etree.ElementTree as ET

def extract_accession_numbers(xml_content):
    root = ET.fromstring(xml_content)
    return [
        result.find("AccessionNumber").text
        for result in root.findall(".//result")
        if result.find("AccessionNumber") is not None
    ]
