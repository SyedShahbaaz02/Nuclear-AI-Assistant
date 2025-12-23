import re


def extract_sections(result, target_prefix="3.2"):
    """
    Extracts section headings matching the target_prefix from the document result.

    Args:
        result (dict): Parsed document intelligence result containing paragraphs.
        target_prefix (str): Section prefix to match (e.g., "3.2").

    Returns:
        list: List of section dictionaries, each with a "section" key.
    """
    section_pattern = re.compile(rf"^{re.escape(target_prefix)}\.\d+\b")
    sections_array = []
    paragraphs = result['paragraphs']

    for paragraph in paragraphs:
        content = paragraph['content']
        role = paragraph.get('role')

        if role == "sectionHeading" and section_pattern.match(content):
            sections_array.append({
                "section": content
            })

    return sections_array


def get_section_bounds(result, sections, target_prefix="3.2"):
    """
    Calculates and enriches bounding region and page information for each section.

    For each section heading matching the target_prefix, determines the top and bottom Y coordinates and page numbers
    using paragraph bounding regions. Also enriches each section with table boundary information if present.

    Args:
        result (dict): Parsed document intelligence result containing paragraphs and tables.
        sections (list): List of section dictionaries to enrich with bounding information.
        target_prefix (str): Section prefix to match (e.g., "3.2").

    Returns:
        list: The input sections list, with each section containing bounding and table info.
    """
    def find_section_indices(paragraphs, section_pattern):
        return [
            idx for idx, paragraph in enumerate(paragraphs)
            if section_pattern.match(paragraph['content']) and paragraph.get('role', '').lower() == "sectionheading"
        ]

    def get_bounds_for_section(idx, section_indices, paragraphs, next_section_pattern):
        paragraph = paragraphs[idx]
        content = paragraph['content']
        region = paragraph['boundingRegions'][0]
        polygon = region['polygon']
        top_y = polygon[1] if len(polygon) >= 2 else 0
        top_page = region.get('pageNumber', 0)
        bottom_y = 0
        bottom_page = 0

        # find the next section's bottom Y and page
        next_idx_pos = section_indices.index(idx) + 1
        if next_idx_pos < len(section_indices):
            next_idx = section_indices[next_idx_pos]
            next_paragraph = paragraphs[next_idx]
            next_region = next_paragraph['boundingRegions'][0]
            next_polygon = next_region['polygon']
            bottom_y = next_polygon[1] if len(next_polygon) >= 2 else 0
            bottom_page = next_region.get('pageNumber', 0)
        else:
            for para in paragraphs[idx+1:]:
                if next_section_pattern.match(para['content']) and para.get('role', '').lower() == "sectionheading":
                    region = para['boundingRegions'][0]
                    polygon = region['polygon']
                    bottom_y = polygon[1] if len(polygon) >= 2 else 0
                    bottom_page = region.get('pageNumber', 0)
                    break
        return {
            "section": content,
            "topY": top_y,
            "bottomY": bottom_y,
            "topPage": top_page,
            "bottomPage": bottom_page
        }

    def enrich_with_table_bounds(section_bounds, tables, section_map):
        for section in section_bounds:
            last_table_pg = last_table_sixth = last_cell_pg = last_cell_sixth = None
            for table in tables:
                for cell in table.get("cells", []):
                    regions = cell.get("boundingRegions", [])
                    for region in regions:
                        cell_page = region.get("pageNumber")
                        polygon = region.get("polygon", [])
                        sixth_coord = polygon[5] if len(polygon) >= 6 else None

                        if cell_page is None or sixth_coord is None:
                            continue
                        last_cell_pg = cell_page
                        last_cell_sixth = sixth_coord

                        in_section = False
                        # single page section: include cells only if y-coord between topY bottomY
                        if section["topPage"] == section["bottomPage"]:
                            if (
                                cell_page == section["topPage"] and
                                section["topY"] < section["bottomY"] and
                                section["topY"] <= polygon[1] < section["bottomY"]
                            ):
                                in_section = True
                        # multi-page section when we do not know the bottomY
                        elif section["bottomY"] == 0:
                            if (
                                (cell_page == section["topPage"] and polygon[1] >= section["topY"]) or
                                (cell_page > section["topPage"])
                            ):
                                in_section = True
                        # multi-page section when we know the bottomY
                        elif (
                            (cell_page == section["topPage"] and polygon[1] >= section["topY"]) or
                            (cell_page == section["bottomPage"] and polygon[1] < section["bottomY"]) or
                            (section["topPage"] < cell_page < section["bottomPage"])
                        ):
                            in_section = True
                        if in_section:
                            last_table_pg = cell_page
                            last_table_sixth = sixth_coord

            section_obj = section_map.get(section["section"])
            section_obj["lastTableSixthCoord"] = (
                last_table_sixth if last_table_sixth is not None else last_cell_sixth
            )
            section_obj["lastTablePage"] = (
                last_table_pg if last_table_pg is not None else last_cell_pg
            )

    section_pattern = re.compile(rf"^{re.escape(target_prefix)}\.\d+\b")
    next_section_pattern = re.compile(r"^3\.3\b")
    paragraphs = result['paragraphs']
    tables = result.get('tables', [])
    section_map = {s["section"]: s for s in sections}

    section_indices = find_section_indices(paragraphs, section_pattern)
    section_bounds = [
        get_bounds_for_section(idx, section_indices, paragraphs, next_section_pattern)
        for idx in section_indices
    ]
    enrich_with_table_bounds(section_bounds, tables, section_map)


def find_start_index(paragraphs, section_title):
    """
    Returns the index of the section heading paragraph matching the given section_title.

    Args:
        paragraphs (list): List of paragraph dictionaries from the document.
        section_title (str): The exact section heading to find.

    Returns:
        int or None: Index of the matching section heading paragraph, or None if not found.
    """
    for i, p in enumerate(paragraphs):
        if p.get('role', '').lower() == "sectionheading" and p['content'] == section_title:
            return i
    return None


def extract_refs_from_paragraphs(
    paragraphs, start_idx, last_table_page, last_table_y, section_pattern, ref_pattern
):
    """
    Extracts references from paragraphs following a section heading up to the next section heading.

    Args:
        paragraphs (list): List of paragraph dictionaries from the document.
        start_idx (int): Index of the section heading paragraph.
        last_table_page (int): Page number of the last table in the section.
        last_table_y (float): Y coordinate of the last table's sixth polygon point.
        section_pattern (Pattern): Regex pattern for section headings.
        ref_pattern (Pattern): Regex pattern for references to extract.

    Returns:
        list: List of extracted reference strings.
    """
    cfr_pattern = re.compile(r"10\s*CFR\s*$")
    refs = []
    i = start_idx + 1
    while i < len(paragraphs):
        para = paragraphs[i]
        para_role = para.get('role', '').lower()
        para_content = para['content']
        if para_role == "sectionheading" and section_pattern.match(para_content):
            break

        region = para.get('boundingRegions', [{}])[0]
        page = region.get('pageNumber')
        polygon = region.get('polygon', [])
        y_coord = polygon[1] if len(polygon) >= 2 else None

        if (
            (page == last_table_page and y_coord is not None and y_coord <= last_table_y)
            or (page is not None and page < last_table_page)
        ):
            matches = ref_pattern.finditer(para_content)
            for match in matches:
                start = match.start()
                prefix = para_content[max(0, start-10):start]  # extracts up to 10 characters before the start index
                if not cfr_pattern.search(prefix):
                    refs.append(match.group(1))
        else:
            break  # ensures function stops collecting references when it finds a new section heading
        i += 1
    return refs


def extract_5072_content_per_subsection(result, sections, target_prefix="3.2"):
    """
    Extracts 50.72 references for each subsection in the specified section.

    For each section heading matching the target_prefix, finds all 50.72 references in the paragraphs
    following the section's table, up to the next section heading. Only references not immediately
    preceded by '10 CFR' are included.

    Args:
        result (dict): Parsed document intelligence result containing paragraphs and metadata.
        sections (list): List of section dictionaries to enrich with 50.72 reference content.
        target_prefix (str): Section prefix to match (e.g., "3.2").

    Returns:
        list: The input sections list, with each section containing a "lxxiii" key (list of references).
    """
    get_section_bounds(result, sections, target_prefix)
    ref_pattern = re.compile(r"(50\.72(\([a-zA-Z0-9]+\))+)")
    section_pattern = re.compile(rf"^{re.escape(target_prefix)}\.\d+\b")
    paragraphs = result['paragraphs']

    for section in sections:
        section_title = section["section"]
        last_table_page = section.get("lastTablePage")
        last_table_y = section.get("lastTableSixthCoord")
        start_idx = find_start_index(paragraphs, section_title)
        refs = extract_refs_from_paragraphs(
            paragraphs, start_idx, last_table_page, last_table_y, section_pattern, ref_pattern
        )
        section["lxxii"] = refs

    return sections


def extract_5073_content_per_subsection(result, sections, target_prefix="3.2"):
    """
    Extracts 50.73 references for each subsection in the specified section.

    For each section heading matching the target_prefix, finds all 50.73 references in the paragraphs
    following the section's table, up to the next section heading. Only references not immediately
    preceded by '10 CFR' are included.

    Args:
        result (dict): Parsed document intelligence result containing paragraphs and metadata.
        sections (list): List of section dictionaries to enrich with 50.73 reference content.
        target_prefix (str): Section prefix to match (e.g., "3.2").

    Returns:
        list: The input sections list, with each section containing a "lxxiii" key (list of references).
    """
    get_section_bounds(result, sections, target_prefix)
    ref_pattern = re.compile(r"(50\.73(\([a-zA-Z0-9]+\))+)")
    section_pattern = re.compile(rf"^{re.escape(target_prefix)}\.\d+\b")
    paragraphs = result['paragraphs']

    for section in sections:
        section_title = section["section"]
        last_table_page = section.get("lastTablePage")
        last_table_y = section.get("lastTableSixthCoord")
        start_idx = find_start_index(paragraphs, section_title)
        refs = extract_refs_from_paragraphs(
            paragraphs, start_idx, last_table_page, last_table_y, section_pattern, ref_pattern
        )
        section["lxxiii"] = refs

    return sections


def extract_description_content_per_subsection(result, sections, target_prefix="3.2"):
    """
    Extracts the Description content for each subsection in the specified section.

    For each section heading matching the target_prefix, finds the start of the description content
    (immediately after the section's table). Collects all relevant paragraphs until a Discussion heading,
    the next section heading, or an Example heading is encountered. Skips footnotes and page numbers.
    Footnote content from both paragraphs and tables is excluded.

    Args:
        result (dict): Parsed document intelligence result containing paragraphs and metadata.
        sections (list): List of section dictionaries to enrich with description content.
        target_prefix (str): Section prefix to match (e.g., "3.2").

    Returns:
        list: The input sections list, with each section containing a "description" key (string).
    """
    def collect_footnote_contents(paragraphs, tables):
        footnotes = set()
        for para in paragraphs:
            if para.get('role', '').lower() == "footnote":
                footnotes.add(para['content'].strip())
        for table in tables:
            for footnote in table.get("footnotes", []):
                content = footnote.get("content", "")
                if content:
                    footnotes.add(content.strip())
        return footnotes

    def find_section_start(paragraphs, section_title):
        return next(
            (i for i, p in enumerate(paragraphs)
             if p.get('role', '').lower() == "sectionheading" and p['content'] == section_title),
            None
        )

    def extract_description(paragraphs, start_idx, top_page, top_y, section_pattern, discussion_heading_pattern,
                            footnote_contents):
        description = []
        i = start_idx + 1
        found_table_start = False
        while i < len(paragraphs):
            para = paragraphs[i]
            region = para.get('boundingRegions', [{}])[0]
            page = region.get('pageNumber')
            polygon = region.get('polygon', [])
            y_coord = polygon[1] if len(polygon) >= 2 else None

            if not found_table_start:
                if (
                    (page == top_page and y_coord is not None and y_coord >= top_y)
                    or (page is not None and page > top_page)
                ):
                    found_table_start = True
                else:
                    i += 1
                    continue

            para_content = para['content'].strip()
            para_role = para.get('role', '').lower()

            if (
                para_role in ["sectionheading", "title"]
                and (
                    discussion_heading_pattern.match(para_content)
                    or section_pattern.match(para_content)
                )
            ):
                break
            if para_role == "pagenumber" or para_content in footnote_contents:
                i += 1
                continue

            description.append(para_content)
            i += 1
        return description

    get_section_bounds(result, sections, target_prefix)
    section_pattern = re.compile(rf"^({re.escape(target_prefix)}\.\d+)\b")
    discussion_heading_pattern = re.compile(r"^Discussion\d*", re.IGNORECASE)
    paragraphs = result['paragraphs']
    tables = result.get('tables', [])
    footnote_contents = collect_footnote_contents(paragraphs, tables)

    for section in sections:
        section_title = section["section"]
        top_page = section.get("lastTablePage")
        top_y = section.get("lastTableSixthCoord")
        start_idx = find_section_start(paragraphs, section_title)
        if start_idx is None or top_page is None or top_y is None:
            section["description"] = ""
            continue
        desc = extract_description(
            paragraphs, start_idx, top_page, top_y, section_pattern, discussion_heading_pattern, footnote_contents
        )
        section["description"] = " ".join(desc) if desc else ""

    for section in sections:
        if "description" not in section:
            section["description"] = ""

    return sections


def extract_discussions_content_per_subsection(result, sections, target_prefix="3.2"):
    """
    Extracts the Discussion content for each subsection in the specified section of the NUREG document.

    Extraction starts at the paragraph index where the Discussion heading is found.
    It collects all subsequent paragraphs until:
      - The next section heading matching the target_prefix is found,
      - The content matches an Example/Examples heading,
      - Or the paragraph role is "footnote" or "pagenumber" (these are skipped).

    Args:
        result (dict): The parsed document intelligence result containing paragraphs and metadata.
        sections (list): List of section dictionaries to enrich with discussion content.
        target_prefix (str): The section prefix to match (e.g., "3.2").

    Returns:
        list: The input sections list, with each section containing a "discussion" key (string).
    """
    def get_discussion_content(start_idx):
        example_heading_pattern = re.compile(r"^Examples?\d*", re.IGNORECASE)
        discussion_content = []
        i = start_idx + 1
        while i < len(paragraphs):
            para = paragraphs[i]
            para_content = para['content']
            para_role = para.get('role', '').lower()
            if para_role in ["sectionheading", "title"] and example_heading_pattern.match(para_content.strip()):
                break
            if para_role in ["footnote", "pagenumber"]:
                i += 1
                continue
            if para_role in ["sectionheading", "title"] and (
                section_pattern.match(para_content.strip()) or
                example_heading_pattern.match(para_content.strip())
            ):
                break
            discussion_content.append(para_content)
            i += 1
        return discussion_content

    section_pattern = re.compile(rf"^({re.escape(target_prefix)}\.\d+)\b")
    discussion_heading_pattern = re.compile(r"^Discussion\d*", re.IGNORECASE)

    paragraphs = result['paragraphs']
    section_map = {s["section"]: s for s in sections}
    current_section = None
    found_discussion = {}

    for idx, paragraph in enumerate(paragraphs):
        content = paragraph['content']
        match = section_pattern.match(content)
        if match:
            current_section = content
            found_discussion[current_section] = False
            continue

        if current_section and not found_discussion.get(current_section, False):
            if discussion_heading_pattern.match(content.strip()):
                section_obj = section_map.get(current_section)
                if section_obj is not None:
                    section_obj["discussion"] = " ".join(get_discussion_content(idx))
                found_discussion[current_section] = True
    for section in sections:
        if "discussion" not in section:
            section["discussion"] = ""

    return sections


def process_example_content(paragraphs, start_idx, section_pattern, discussion_heading_pattern):
    """
    Extracts example entries from paragraphs starting at start_idx.

    Handles the edge case where the first example title is a plain string (not starting with (number)),
    but only if it is not in all caps. All subsequent titles must start with (number).
    Ignores section headings that do not start with (number) and any all-caps strings.

    Args:
        paragraphs (list): List of paragraph dicts from the document.
        start_idx (int): Index to start extracting examples.
        section_pattern (Pattern): Regex pattern for section headings.
        discussion_heading_pattern (Pattern): Regex pattern for discussion headings.

    Returns:
        list[dict]: List of examples, each with 'title' and 'description' keys.
    """
    examples = []
    paren_number_pattern = re.compile(r"^\(\d+\)")
    stop_extraction_pattern = re.compile(r"^3\.3\b")
    i = start_idx + 1
    current_title = ""
    current_desc = []
    found_first_title = False

    while i < len(paragraphs):
        para = paragraphs[i]
        para_content = para['content'].strip()
        para_role = para.get('role', '').lower()

        if para_role in ["sectionheading", "title"] and section_pattern.match(para_content):
            break
        if para_role in ["sectionheading", "title"] and discussion_heading_pattern.match(para_content):
            break
        if stop_extraction_pattern.match(para_content):
            break
        if para_role in ["footnote", "pagenumber"]:
            i += 1
            continue

        # only treat the first non-empty, non-heading, non-footnote, non-pagenumber, non-all-caps string as a title
        if (
            not found_first_title
            and para_content
            and not paren_number_pattern.match(para_content)
            and not para_content.isupper()
        ):
            current_title = para_content
            current_desc = []
            found_first_title = True
        elif (
            (para_role == "sectionheading" and paren_number_pattern.match(para_content))
            or paren_number_pattern.match(para_content)
        ):
            if current_title:
                examples.append({
                    "title": current_title,
                    "description": " ".join(current_desc).strip()
                })
            current_title = para_content
            current_desc = []
            found_first_title = True
        else:
            current_desc.append(para_content)
        i += 1

    if current_title:
        examples.append({
            "title": current_title,
            "description": " ".join(current_desc).strip()
        })
    return examples


def extract_example_content_per_subsection(result, sections, target_prefix="3.2"):
    """
    Extracts example entries for each subsection in the specified section.

    For each section heading matching the target_prefix, finds the "Example" or "Examples" heading.
    Then, collects all examples under that heading, where each example consists of a title
    (sectionHeading starting with (number))
    and a description (all following content until the next such heading or end of section).
    Ignores section headings that do not start with (number).

    Args:
        result (dict): Parsed document intelligence result containing paragraphs and metadata.
        sections (list): List of section dictionaries to enrich with example content.
        target_prefix (str): Section prefix to match (e.g., "3.2").

    Returns:
        list: The input sections list, with each section containing an "examples" key (list of dicts).
    """
    section_pattern = re.compile(rf"^{re.escape(target_prefix)}\.\d+\b")
    example_heading_pattern = re.compile(r"^Examples?\d*", re.IGNORECASE)
    discussion_heading_pattern = re.compile(r"^Discussion\d*", re.IGNORECASE)

    paragraphs = result['paragraphs']
    section_map = {s["section"]: s for s in sections}
    current_section = None
    found_example = {}

    for idx, paragraph in enumerate(paragraphs):
        content = paragraph['content']
        match = section_pattern.match(content)
        if match:
            current_section = content
            found_example[current_section] = False
            continue

        if current_section and not found_example.get(current_section, False):
            para_role = paragraph.get('role', '').lower()
            if para_role in ["sectionheading", "title"] and example_heading_pattern.match(content.strip()):
                section_obj = section_map.get(current_section)
                if section_obj is not None:
                    section_obj["examples"] = process_example_content(
                        paragraphs, idx, section_pattern, discussion_heading_pattern
                    )
                found_example[current_section] = True
    for section in sections:
        if "examples" not in section:
            section["examples"] = []
    return sections


def extract_page_numbers_per_subsection(result, sections, target_prefix="3.2"):
    section_pattern = re.compile(rf"^({re.escape(target_prefix)}\.\d+)\b")
    paragraphs = result['paragraphs']
    section_map = {s["section"]: s for s in sections}

    for paragraph in paragraphs:
        content = paragraph['content']
        role = paragraph.get('role', '').lower()
        match = section_pattern.match(content)
        if match and role == "sectionheading":
            section_obj = section_map.get(content)
            page_number = paragraph['boundingRegions'][0]['pageNumber']
            if section_obj is not None:
                section_obj["pageNumber"] = page_number
    return sections


def remove_internal_fields(sections):
    for section in sections:
        section.pop("lastTableSixthCoord", None)
        section.pop("lastTablePage", None)
    return sections
