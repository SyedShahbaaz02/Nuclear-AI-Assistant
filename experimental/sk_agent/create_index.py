import os
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchFieldDataType,
    SearchField,
    SemanticConfiguration,
    SemanticField,
    VectorSearch,
    SemanticSearch,
    SemanticPrioritizedFields,
    SearchableField,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
)

global INDEX_NAME


def define_index() -> SearchIndex:
    """
    Defines the structure of the Azure AI Search index, including fields, vector search configurations,
    and semantic configurations.

    Returns:
        SearchIndex: The defined search index object.
    """
    ler_index = SearchIndex(
        name=INDEX_NAME,
        fields=[
            SimpleField(name="ler_number", type=SearchFieldDataType.String, key=True),
            SimpleField(name="report_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SimpleField(name="event_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
            SimpleField(name="facility_name", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SimpleField(name="cfr_requirements", type=SearchFieldDataType.Collection(
                SearchFieldDataType.String), filterable=True),
            SearchableField(name="abstract", type=SearchFieldDataType.String),
            SearchableField(name="narrative", type=SearchFieldDataType.String),
            SearchField(name="abstractVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
            SearchField(name="narrativeVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
            SearchField(name="titleVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True, vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile")
        ]
    )

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="myHnsw"
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
                vectorizer_name="azure_openai"
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="azure_openai",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    deployment_name=os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME"),
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    model_name="text-embedding-ada-002",
                )

            )
        ]
    )

    ler_index.vector_search = vector_search

    semantic_config = SemanticConfiguration(
        name="microsoft-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            keywords_fields=[
                SemanticField(field_name="facility_name"),
                SemanticField(field_name="cfr_requirements"),
            ],
            content_fields=[
                SemanticField(field_name="narrative")
            ]
        )
    )

    # Create the semantic settings with the configuration
    ler_index.semantic_search = SemanticSearch(configurations=[semantic_config])
    return ler_index


def create_index(ler_index: SearchIndex):
    """
    Creates the Azure AI Search index if it does not already exist.

    Args:
        ler_index (SearchIndex): The search index definition to be created.

    Returns:
        Any: The result of the index creation operation.
    """
    search_api_key = os.environ.get('AZURE_AI_SEARCH_API_KEY')  # e.g., 'xxxxxxxxxxxxxxxxxxxx'
    search_endpoint = os.environ.get('AZURE_AI_SEARCH_ENDPOINT')  # e.g., 'https://my-search-service.search.windows.net'
    credential = AzureKeyCredential(search_api_key)

    # Create a SearchIndexClient for index management
    index_client = SearchIndexClient(endpoint=search_endpoint,
                                     credential=credential)

    # Check if the Index Exists
    index_list = index_client.list_index_names()
    if INDEX_NAME in index_list:
        print(f"Index '{INDEX_NAME}' exists.")
    else:
        result = index_client.create_index(ler_index)
        print(f"Successfully created index '{INDEX_NAME}'.")
        index_list = index_client.list_index_names()
        if INDEX_NAME in index_list:
            print(f"Index '{INDEX_NAME}' exists.")
    return result


def main():
    """
    Main function to define and create the Azure AI Search index.
    """
    index_definition = define_index()
    create_index(index_definition)


if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    INDEX_NAME = os.environ.get("AZURE_AI_SEARCH_INDEX_NAME")
    main()
