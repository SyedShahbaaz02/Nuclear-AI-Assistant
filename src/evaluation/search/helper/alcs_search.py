from pydantic import BaseModel
from typing import Optional
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from enum import Enum


class SearchType(Enum):
    FullText = 1
    Vector = 2
    Hybrid = 3


class AzureSearchModel(BaseModel):
    azure_search_key: str
    azure_search_service_uri: str
    azure_search_index_name: str
    azure_id_field: Optional[str] = 'id'
    azure_content_field: list[str]
    azure_embedding_field: str
    vector_knn: int
    search_score_field: Optional[str] = '@search.score'


class AzureSearchService():
    def __init__(self, azure_search_model: AzureSearchModel):
        self._azure_search_model = azure_search_model
        self._credential = AzureKeyCredential(azure_search_model.azure_search_key)
        self._select_fields = [azure_search_model.azure_id_field,
                               azure_search_model.azure_embedding_field] + azure_search_model.azure_content_field
        self._search_fields = azure_search_model.azure_content_field

    def get_documents(self,
                      search_text: str = '*',
                      search_fields: list[str] = None,
                      search_type: SearchType = SearchType.FullText,
                      search_count: int = 30) -> list[dict]:

        if search_fields is None:
            search_fields = self._search_fields

        # Instantiate Search Client
        search_client = SearchClient(
            endpoint=self._azure_search_model.azure_search_service_uri,
            index_name=self._azure_search_model.azure_search_index_name,
            credential=self._credential
        )

        # Search documents/entries
        if search_type == SearchType.FullText:
            results = search_client.search(
                                            search_text=search_text,
                                            search_fields=search_fields,
                                            select="*",
                                            top=search_count
                                        )

        elif (search_type == SearchType.Vector or search_type == SearchType.Hybrid):
            vector_query = VectorizableTextQuery(
                                                text=search_text,
                                                fields=self._azure_search_model.azure_embedding_field,
                                                k_nearest_neighbors=self._azure_search_model.vector_knn,
                                                exhaustive=True
                                            )

            results = search_client.search(
                                            search_text=search_text if search_type == SearchType.Hybrid else None,
                                            vector_queries=[vector_query],
                                            search_fields=search_fields if search_type == SearchType.Hybrid else None,
                                            select="*",
                                            top=search_count
                                        )

        else:
            raise ValueError("Invalid Search Type")

        # Add search type to the results
        results_list = [{**dict(item), "type": search_type.name} for item in results]

        return results_list
