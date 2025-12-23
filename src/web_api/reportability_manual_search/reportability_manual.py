import re
from bs4 import BeautifulSoup


def split_sections(text):
    """
    Splits the document into sections based on 'REPORTABLE EVENT SAF x.x' or 'REPORTABLE EVENT RAD x.x' or
    'REPORTABLE EVENT SEC x.x' markers.Handles (Cont’d) and works with markdown or plain text.
    args:
        text (str): The input text to split into sections.
    Returns:
        list of reportability manual  blocks as strings
    """
    # Normalize Cont’d by removing it so it doesn't get mistaken for a new SAF
    text = re.sub(r"\s*\(Cont[’']?d\)", "", text, flags=re.IGNORECASE)

    # Regex to find each reportability manual heading like 'REPORTABLE EVENT SAF 1.1:'
    pattern = r"(?:^|\n)\s*(?:#+\s*)?REPORTABLE EVENT (SAF|RAD|SEC)\s+\d+\.\d+.*?:"

    # Find all starting points
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    sections = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append(text[start:end].strip())

    return sections


def extract_id(section: str) -> str:
    """
    Extracts the section type and ID (e.g., 'SAF 1.1', 'RAD 2.3', 'SEC 3.4').
    Args:
        section(str): The section text to search.
    Returns:
        str: The extracted section type and ID(e.g., 'SAF 1.1'), or None if not found.
    """
    match = re.search(r'(SAF|RAD|SEC)\s+(\d+\.\d+)', section, re.IGNORECASE)
    return f"{match.group(1).upper()} {match.group(2)}" if match else None


def extract_requirement(text):
    """
    Extracts the requirement references and content from the given text.
    Args:
        text(str): The input text containing the requirement section.
    Returns:
        tuple: A tuple containing:
            - ref_field(str): The extracted requirement references.
            - ref_content(str): The extracted requirement content.
    """
    # Step 1: Extract content
    split_pattern = r'(?:<t[hd][^>]*>)?\s*(Time(?:\s*\n\s*Limit)?)\s*(?:<\/t[hd]>)?|#+\s*(Time\s+Limit)|\bTime\b'

    pre_req_section = re.split(split_pattern, text, flags=re.IGNORECASE)[0]

    index = text.find("Requirement:")
    index_end = index + len("Requirement:")

    if index != -1:
        pre_req_section = pre_req_section[index_end:]

    # Step 2: Split into paragraphs
    paragraph_split = r'\n\s*\n'
    paragraphs = re.split(paragraph_split, pre_req_section)

    ref_paragraphs = []
    end_index = 0

    # Step 3: Collect paragraphs with "10 CFR"
    pattern = r"C[\s\.]*F[\s\.]*R"

    for idx, para in enumerate(paragraphs):
        if (re.search(pattern, para, flags=re.IGNORECASE)) and '§' not in para and ':' not in para:

            ref_paragraphs.append(para.strip())
            end_index = idx + 1  # capture the last index after CFR

    # Step 4: Get the rest as content
    ref_content_paragraphs = paragraphs[end_index:]
    ref_field = "\n\n".join(ref_paragraphs)
    ref_content = "\n\n".join(p.strip() for p in ref_content_paragraphs if p.strip())

    # Handling HTML Table
    if '</table>' in ref_field:
        soup = BeautifulSoup(ref_field, "html.parser")
        flatten_ref_field = []
        for td in soup.find_all('td'):
            cfr = td.get_text(strip=True)
            if cfr:
                flatten_ref_field.append(cfr)
        ref_field = '\n'.join(r for r in flatten_ref_field)

    # Edge Cases
    if not ref_field:
        refPara2 = re.split(paragraph_split, ref_content)
        if len(refPara2) > 1:
            ref_field = refPara2[0]
            ref_content = ' '.join(x for x in refPara2[1:])
        else:
            ref_field = ref_content
            ref_content = "None"

    return ref_field, ref_content


def extract_description_and_report(data, starting_header, ending_header):
    """
    Extracts the description and report section from the given text.
    Args:
        data(str): The input text containing the description and report section.
        starting_header(str): The header indicating the start of the section.
        ending_header(str): The header indicating the end of the section.
    Returns:
        list: A list of dictionaries containing 'timeLimit' and 'notification' keys.
    """
    # Step 1: Extract section data between starting header and ending header
    start = data.find(starting_header)
    end = data.find(ending_header)
    notifications_section = data[start:end]
    # Step 2: Normalize text (handle tables and line breaks)
    table_pattern = re.compile(r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>", re.DOTALL)
    table_matches = table_pattern.findall(notifications_section)

    results = []

    # Process table entries
    for time, note in table_matches:
        results.append({
            'timeLimit': time.strip(),
            'notification': re.sub(r'\s+', ' ', note.strip())
        })

    # Step 3: Use the provided regex for non-table (text) notifications
    text_only = re.sub(r"<.*?>", "", notifications_section)  # remove HTML tags
    text_only = re.sub(r'\r?\n+', '\n', text_only).strip()   # normalize line breaks

    pattern = re.compile(
        r"(?P<time>(?:^[A-Z0-9 ,'\-/()]+(?:\n|$))+)\n?"   # Group 'time': One or more all-caps lines
        r"(?P<notification>(?:^(?![A-Z0-9 ,'\-/()]+$).+\n?)*)",  # Group 'notification': Non-uppercase body
        re.MULTILINE
    )

    matches = pattern.findall(text_only)

    results = []
    seen = set()

    for time, note in matches:
        key = (time.strip().upper(), note.strip())
        if key not in seen:
            results.append({
                'timeLimit': time.strip().upper(),
                'notification': re.sub(r'\s+', ' ', note.strip())
            })
            seen.add(key)
    if extract_id(data).startswith('SEC'):

        # Pattern 2: "15 MINUTES FAC." style blocks
        pattern2 = re.compile(
            r"(?P<timeLimit>(?:\d{1,2}[- ]MIN(?:UTE)?(?:S)?|\d+ HOUR) (?:FAC|SHIP))\.\s*"
            r"(?P<notification>.*?)(?=(?:\d{1,2}[- ]MIN(?:UTE)?(?:S)?|\d+ HOUR) (?:FAC|SHIP)\.|$)",
            re.DOTALL
        )
        for match in pattern2.finditer(text_only):
            time = match.group("timeLimit").strip().upper()
            note = match.group("notification").strip()
            key = (time, note)
            if key not in seen:
                results.append({
                    'timeLimit': time,
                    'notification': re.sub(r'\s+', ' ', note)
                })
                seen.add(key)

        # Pattern 3: "PROMPTLY", "IMMEDIATELY", etc. style blocks
        pattern3 = re.compile(
            r"(?P<timeLimit>(?:PROMPTLY|IMMEDIATELY|30 DAYS?|CONTACT|1 BUSINESS DAY|3 ATTEMPTS?|WITHIN 24 HOURS))\.?\s*"
            r"(?P<notification>.*?)(?=(?:PROMPTLY|IMMEDIATELY|30 DAYS?|CONTACT|1 BUSINESS DAY|3 ATTEMPTS?|WITHIN 24 HOURS)\b|$)",
            re.DOTALL | re.IGNORECASE
        )

        for match in pattern3.finditer(text_only):
            time = match.group("timeLimit").strip().upper()
            note = match.group("notification").strip()
            key = (time, note)
            if key not in seen:
                results.append({
                    'timeLimit': time,
                    'notification': re.sub(r'\s+', ' ', note)
                })
                seen.add(key)

    return results


def extract_discussion(text):
    """
    Extracts the "Discussion:" section from the given text.
    Args:
        text(str): The input text containing the discussion section.
    Returns:
        str: The extracted discussion section.
    """
    # Normalize line endings
    text = re.sub(r'\r?\n', '\n', text)
    # Check for deleted marker
    if re.search(r'\bDELETED\b', text, re.IGNORECASE):
        raise RuntimeError("Document marked as DELETED. Skipping indexing.")

    # Match variants of "Discussion:" and "References:"
    header1_pattern = r"(?:^|\n)\s*(?:#+\s*)?Discussion\s*:"
    header2_pattern = r"(?:^|\n)\s*(?:#+\s*)?References\s*:"

    # Find match locations
    header1_match = re.search(header1_pattern, text, re.IGNORECASE)
    header2_match = re.search(header2_pattern, text, re.IGNORECASE)

    discussion_section = ""

    if header1_match and header2_match:
        start = header1_match.end()
        end = header2_match.start()
        discussion_section = text[start:end].strip()
    else:
        if not header1_match:
            raise ValueError("The 'Discussion:' section was not found.")
        if not header2_match:
            raise ValueError("The 'References:' section was not found.")
    return discussion_section


def clean_text(raw_text):
    """
    Cleans the input text by removing HTML tags, comments, and unwanted patterns.
    Args:
        raw_text(str): The input text to be cleaned.
    Returns:
        str: The cleaned text.
    """

    text = re.sub(r'<!--.*?-->', '', raw_text, flags=re.DOTALL)  # Remove HTML comments
    text = re.sub(r'^\s*o\s+', '', text, flags=re.MULTILINE)  # Bullet 'o'
    text = re.sub(r'#.*Confidential.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^LS-AA-\d+.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^Revision\s+\d+.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^.*\d+\.\d+\s+\(Cont'd\)\s*$", '', text, flags=re.MULTILINE | re.IGNORECASE)

    return text.strip()


def extract_sections_data(markdown_text):
    """
    Extracts structured data from the markdown text of a reportability manual.
    Args:
        markdown_text(str): The markdown text to extract data from .
    Returns:
        list: A list of dictionaries containing extracted data for each section.
    """
    blocks = split_sections(markdown_text)
    section_data = []

    for block in blocks:
        section_id = extract_id(block)
        # Extract page number
        match = re.search(r'Page (\d+) of \d+', block)
        page_number = int(match.group(1)) - 1 if match else None

        cleaned_block = clean_text(block)

        try:
            discussion = extract_discussion(cleaned_block)
        except RuntimeError:
            print(f"Skipping DELETED block for section ID: {section_id}")
            continue
        except ValueError as e:
            print(f"Skipping section ID {section_id} due to missing section: {e}")
            continue

        data = {
            "sectionName": f"{section_id}",
            "pageNumber": page_number,
            "references": [
                ref.strip()
                for ref in extract_requirement(cleaned_block)[0].split('\n')
                if ref.strip()
            ],
            "referenceContent": extract_requirement(cleaned_block)[1],
            "requiredNotifications": extract_description_and_report(
                cleaned_block, "Required Notification(s):", "Required Written Report(s):"
            ),
            "requiredWrittenReports": extract_description_and_report(
                cleaned_block, 'Required Written Report(s):', 'Discussion:'
            ),
            "discussion": discussion
        }

        section_data.append(data)

    return section_data
