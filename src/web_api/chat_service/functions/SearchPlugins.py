import logging
import os

from abc import ABC, abstractmethod
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizableTextQuery
from enum import Enum
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from typing import Type, TypeVar

from constants import ChatServiceConstants
from models import (
    NUREGSection32, SearchType, SearchConfiguration,
    SearchConfigurationList, ReportabilityContext, ReportabilityManual, NaiveSearch
)
from services import ReportabilityServices

T = TypeVar('T')
logger = logging.getLogger(ChatServiceConstants.LOGGER_NAME.value + __name__)


class Index(Enum):
    NUREG = ("nureg", NUREGSection32)
    REPORTABILITY_MANUAL = ("reportability_manual", ReportabilityManual)
    TS_NAIVE_SEARCH = ("ts_naive_search", NaiveSearch)
    UFSAR_NAIVE_SEARCH = ("ufsar_naive_search", NaiveSearch)

    def __init__(self, index_name: str, model_class: Type[T]):
        self.index_name: str = index_name
        self.model_class: Type[T] = model_class


class SearchPluginsBase(ABC):
    """Base class for search plugins that interact with the ReportabilityContext."""
    def __init__(
        self,
        reportability_context: ReportabilityContext,
        search_configurations: dict[str, SearchConfiguration] = None,
        auto_populate_document_lists: bool = False
    ):
        self._search_configurations = search_configurations or self._load_configuration()
        self._reportability_context: ReportabilityContext = reportability_context
        self._auto_populate_document_lists: bool = auto_populate_document_lists

    @abstractmethod
    def get_documents(self):
        """Abstract method to get documents based on a search query."""
        pass

    def _load_configuration(self) -> dict[str, SearchConfiguration]:
        try:
            search_configurations_path = os.path.join(
                os.path.dirname(__file__),
                'search_configuration.json'
            )
            if not os.path.exists(search_configurations_path):
                raise FileNotFoundError(
                    f"Search configuration file not found at {search_configurations_path}"
                )
            with open(search_configurations_path, 'r') as file:
                search_configurations = SearchConfigurationList.model_validate_json(file.read())
            if not search_configurations:
                raise ValueError("No search configurations found in the file.")
            for name, config in search_configurations.root.items():
                config.index_name = os.getenv(config.index_name_setting)
            logger.info(f"Loaded search configurations: {list(search_configurations.root.keys())}")
            logger.debug(f"Search configurations: {search_configurations.root}")
            return search_configurations.root
        except Exception as e:
            logger.exception(f"Error loading search configurations: {e}", exc_info=e)
            raise

    async def _search_results(
            self, search_client: SearchClient, search_configuration: SearchConfiguration, query: str):
        if search_configuration.search_type == SearchType.FullText:
            return await search_client.search(
                search_text=query,
                search_fields=search_configuration.search_fields,
                select=search_configuration.select_fields,
                top=search_configuration.top
            )
        elif (
            search_configuration.search_type == SearchType.Vector or
            search_configuration.search_type == SearchType.Hybrid
        ):
            if search_configuration.search_type == SearchType.Vector:
                search_fields = None
                search_text = None
            else:
                search_fields = search_configuration.search_fields
                search_text = query
            vector_query = VectorizableTextQuery(
                text=query,
                fields=search_configuration.vector_fields,
                k_nearest_neighbors=search_configuration.k_nearest_neighbors,
                exhaustive=True,
            )
            return await search_client.search(
                search_text=search_text,
                vector_queries=[vector_query],
                search_fields=search_fields,
                select=search_configuration.select_fields,
                top=search_configuration.top
            )
        else:
            raise ValueError("Invalid Search Type")

    async def _get_search_results(
        self,
        index: Index,
        search_query: str
    ) -> list[T]:
        try:
            if search_query is None or search_query.strip() == "":
                raise ValueError("Parameter 'search_query' is required.")
            if index.index_name not in self._search_configurations:
                raise ValueError("Undefined search configuration")

            search_configuration = self._search_configurations[index.index_name]

            search_client: SearchClient = ReportabilityServices.get_ai_search_client(
                search_configuration.index_name
            )
            async with search_client:
                results = await self._search_results(
                    search_client,
                    search_configuration,
                    query=search_query
                )
                results_list = await self._convert_results(
                    search_configuration.threshold, results, search_query, index.model_class
                )

            return self._process_results(results_list, search_query)
        except Exception as e:
            logger.exception(f"Error performing search: {e}", exc_info=e)
            raise

    def _process_results(self, results, query: str) -> list:
        # lets make sure we add the results to the context, but only if the document isn't already present,
        # we also don't want to return results that are already in the context
        only_new_results: list = []
        for result in results:
            if not any(
                existing.id == result.id for existing in self._reportability_context.plugin_results
            ):
                result.search_query = query
                self._reportability_context.plugin_results.append(result)
                only_new_results.append(result)

        return only_new_results

    async def _convert_results(self, threshold: float, results: list, query: str, model_class: Type[T]) -> list[T]:
        results_list = []
        async for result in results:
            score = result['@search.score']
            if score is not None and score >= threshold:
                model_instance = model_class.model_validate(result)
                results_list.append(model_instance)

            logger.debug(
                f"Found {len(results_list)} results for query: {query} "
                f"with threshold: {threshold}"
            )

        return results_list


class NuregPlugin(SearchPluginsBase):
    @kernel_function(
        name="search_nureg",
        description="""
        Search for relevant information from NUREG 1022 Section 3.2. This section provides detailed guidance on the
        types of events that must be reported to the NRC. Each subsection corresponds to a specific regulatory
        requirement and includes explanations, examples, and clarifications to help licensees determine whether
        an event is reportable.

        Parameters:
            search_query (str): The search query string. Always use the parameter name 'search_query'.
        Returns:
            str: A string representation of the relevant subsection(s) of NUREG 1022. Each subsection will include the:
                Document Id: The unique identifier for the document.
                Section Name: The section title within NUREG 1022 this entry is.
                CFR 50.72: List of 10 CFR 50.72 subsections referenced.
                CFR 50.73: List of 10 CFR 50.73 subsections referenced.
                Description: Textual description of the section.
                Discussion: Detailed discussion or analysis.
                Examples: List of example objects, each with a title and description.
        """
    )
    async def get_documents(
        self,
        search_query: str
    ) -> str:
        """Search for relevant NUREG 1022 Section 3.2 documents based on the search query."""
        results_list: list[NUREGSection32] = await self._get_search_results(
            Index.NUREG, search_query)
        return "\n\n".join(item.to_agent_string() for item in results_list)


class ReportabilityManualPlugin(SearchPluginsBase):
    @kernel_function(
        name="search_reportability_manual",
        description="""
        Search for relevant information from Constellation's Reportability Manual. This manual provides
        comprehensive guidance on the reportability of events to different Regulatory agencies, including the NRC.
        Each section corresponds to a specific regulatory requirement and includes explanations,
        examples, and clarifications to help licensees determine whether an event is reportable.

        Parameters:
            search_query (str): The search query string. Always use the parameter name 'search_query'.
        Returns:
            str: A string representation of the relevant subsection(s) of Reportability Manual.
            Each section will include the:
                Document Id: The unique identifier for the document.
                Section Name: The title of the section within the reportability
                    manual this entry is.
                References: List of regulatory subsections referenced.
                Reference Content: actual content from references.
                Discussion: Detailed discussion or analysis.
                Required Notifications: List of required notifications, each
                    notification identifies the time limit and a
                    description of the notification requirement.
                Required Reports: List of required reports, each report
                    identifies the time limit and a description of the
                    report requirement.
        """
    )
    async def get_documents(
        self,
        search_query: str
    ) -> str:
        """Search for relevant Reportability Manual documents based on the search query."""
        results_list: list[ReportabilityManual] = await self._get_search_results(
            Index.REPORTABILITY_MANUAL,
            search_query
        )
        return "\n\n".join(item.to_agent_string() for item in results_list)


class TSNaivePlugin(SearchPluginsBase):
    @kernel_function(
        name="search_ts_naive",
        description="""
        Search for relevant information in a naive way, which is everything ingested as it is. This index covers
        all the manuals or documents related to constellation or nuclear, that we want to focus on and ingest.

        Parameters:
            search_query (str): The search query string. Always use the parameter name 'search_query'.
        Returns:
            str: A string representation of the content of the chunk.
        """
    )
    async def get_documents(
        self,
        search_query: str
    ) -> str:
        """Search for relevant documents based on the search query."""
        results_list: list[NaiveSearch] = await self._get_search_results(
            Index.TS_NAIVE_SEARCH,
            search_query
        )
        return "\n\n".join(item.to_agent_string() for item in results_list)


class UFSARNaivePlugin(SearchPluginsBase):
    @kernel_function(
        name="search_ufsar_naive",
        description="""
        Search for relevant information in a naive way, which is everything ingested as it is. This index covers
        all the manuals or documents related to constellation or nuclear, that we want to focus on and ingest.

        Parameters:
            search_query (str): The search query string. Always use the parameter name 'search_query'.
        Returns:
            str: A string representation of the content of the chunk.
        """
    )
    async def get_documents(
        self,
        search_query: str
    ) -> str:
        """Search for relevant documents based on the search query."""
        results_list: list[NaiveSearch] = await self._get_search_results(
            Index.UFSAR_NAIVE_SEARCH,
            search_query
        )
        return "\n\n".join(item.to_agent_string() for item in results_list)
