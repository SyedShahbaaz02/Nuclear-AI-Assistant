from config import START_DATE, END_DATE, DOCUMENT_TYPE, DOCUMENT_TITLE

def build_query():
    base_url = "https://adams.nrc.gov/wba/services/search/advanced/nrc"

    # Replace spaces with '+'
    doc_type_encoded = DOCUMENT_TYPE.replace(" ", "+")
    doc_title_encoded = DOCUMENT_TITLE.replace(" ", "+")

    query = (
        f"?q="
        f"(mode:sections,sections:("
        f"filters:(public-library:!t),"
        f"options:(within-folder:(enable:!t,insubfolder:!f,path:%27%27)),"
        f"properties_search_all:!("
        f"!(DocumentType,starts,%27{doc_type_encoded}%27,%27%27),"
        f"!(%27$title%27,contains,%27{doc_title_encoded}%27,%27%27),"
        f"!(DocumentDate,range,(left:%27{START_DATE}%27,right:%27{END_DATE}%27),%27%27))"
        f"))"
        f"&qn=New&tab=advanced-search-pars&s=%24title&so=ASC"
    )

    full_url = base_url + query

    return full_url
