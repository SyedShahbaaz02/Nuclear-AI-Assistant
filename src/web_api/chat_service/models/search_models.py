from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel, Field, RootModel
from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    vectorstoremodel,
)
from typing import Annotated, List
from urllib.parse import quote, unquote

from services import ReportabilityServices


class SearchType(str, Enum):
    """Enumeration for different types of search operations."""
    FullText = "FullText"
    Vector = "Vector"
    Hybrid = "Hybrid"


class SearchConfiguration(BaseModel):
    """
    Configuration for search operations.

    Attributes:
        index_name_setting: The name of the environment variable where the index name can be found.
        index_name: The name of the Azure Cognitive Search index to perform the search on.
        search_type: The type of search to perform (FullText, Vector, or Hybrid).
        k_nearest_neighbors: The number of nearest neighbors to return for vector searches.
        top: The maximum number of results to return for the search.
        search_fields: The fields to search in for full-text or hybrid searches.
        select_fields: The fields to select in the search results.
        vector_fields: The field containing the vector embeddings for vector or hybrid searches.
        threshold: The threshold for similarity in vector searches, used to filter results.
    """
    index_name_setting: str = Field(
        ..., description="The name of the environment variable the name of the index can be found in.")
    index_name: str | None = Field(
        default=None, description="The name of the Azure Cognitive Search index to perform the search on.")
    search_type: SearchType = Field(
        ..., description="The type of search to perform: FullText, Vector, or Hybrid.")
    k_nearest_neighbors: int = Field(
        ..., description="The number of nearest neighbors to return for vector searches.")
    top: int = Field(
        ..., description="The maximum number of results to return for the search.")
    search_fields: list[str] = Field(
        ..., description="The fields to search in for full-text or hybrid searches.")
    select_fields: list[str] = Field(
        ..., description="The fields to select in the search results.")
    vector_fields: str = Field(
        ..., description="The field containing the vector embeddings for vector or hybrid searches.")
    threshold: float = Field(
        ..., description="The threshold for similarity in vector searches, used to filter results.")


class SearchConfigurationList(RootModel[dict[str, SearchConfiguration]]):
    """
    A validated dictionary of search configurations.
    """


class Example(BaseModel):
    """
    Represents an example related to a NUREG section.

    Attributes:
        title: Title of the example.
        description: Description of the example.
    """
    title: Annotated[str, VectorStoreRecordDataField()] = Field(..., description="Title of the example.")
    description: Annotated[str, VectorStoreRecordDataField()] = Field(..., description="Description of the example.")


class SearchPluginResult(BaseModel):
    """
    Represents a search result returned by the search plugin.

    Attributes:
        search_type: The type of search that produced this result.
        document_id: Unique identifier for the document.
        document_uri: URI of the document.
        search_query: The search query that produced this result, if applicable.
        cited: Indicates if the document has been cited in the chat history.
    """
    search_type: str
    document_id: str
    document_uri: str
    search_query: str | None = None
    cited: bool = False


class SearchModelsBase(ABC, BaseModel):
    """
    A base class for aggregating the information retrieved from a search query.

    Attributes:
        id: Unique identifier for the section.
        storageAccountName: Name of the Azure storage account where the document is stored.
        containerName: Name of the Azure Blob Storage container where the document is stored.
        blobName: Name of the blob (document) in Azure Blob Storage.
        pageNumber: Page number in the document where the section is located.
        cited: Indicates if the document has been cited in the chat history.
        search_query: The search query used to retrieve this document.
    """
    id: Annotated[str, VectorStoreRecordKeyField] = Field(default="naive", description="Unique identifier of section.")
    storageAccountName: Annotated[str, VectorStoreRecordDataField()] = Field(default="naive")
    containerName: Annotated[str, VectorStoreRecordDataField()] = Field(default="naive")
    blobName: Annotated[str, VectorStoreRecordDataField()] = Field(default="naive")
    pageNumber: Annotated[int, VectorStoreRecordDataField()] = Field(default=0)
    cited: Annotated[bool, VectorStoreRecordDataField()] = Field(
        default=False, description="Indicates if the document has been cited in the chat history."
    )
    search_query: Annotated[str, VectorStoreRecordDataField()] = Field(
        default="", description="The search query used to retrieve this document."
    )

    @abstractmethod
    def get_display_value(self) -> str:
        """
        Gets the value to display to user that can identify this document

        Returns:
            str: The value to display to the user that can identify this document.
        """
        pass

    def get_document_url(self) -> str:
        """
        Gets the blob url from the blob attributes returned from the search
        Returns:
           str: Blob url from the search results.
        """
        blob_name_unencoded = unquote(self.blobName)
        blob_name_encoded = quote(blob_name_unencoded)

        sas_token = ReportabilityServices.get_sas_token(self.storageAccountName,
                                                        self.containerName,
                                                        blob_name_unencoded)

        blob_url = (f"https://{self.storageAccountName}.blob.core.usgovcloudapi.net/{self.containerName}/"
                    f"{blob_name_encoded}?{sas_token}#page={self.pageNumber}")

        return blob_url

    def to_search_result(self) -> SearchPluginResult:
        """
        Converts the SearchModelsBase instance to a SearchPluginResult.

        Returns:
            SearchPluginResult: The converted search result.
        """
        blob_uri = self.get_document_url()

        return SearchPluginResult(
            search_type=self.__class__.__name__.lower(),
            document_id=self.id,
            document_uri=blob_uri,
            search_query=self.search_query,
            cited=self.cited
        )

    @abstractmethod
    def to_agent_string(self) -> str:
        """
        Returns a concise, readable string representation of the object for AI agent consumption.
        This method must be implemented by subclasses.

        Returns:
            str: A string representation of the object suitable for AI agent consumption.
        """
        pass


@vectorstoremodel
class NUREGSection32(SearchModelsBase):
    """
    Represents a section of NUREG 1022, Section 3.2.

    Attributes:
        section: The section number within NUREG 1022 this entry is.
        lxxii: List of CFR 50.72 subsections referenced.
        lxxiii: List of CFR 50.73 subsections referenced.
        description: Textual description of the section.
        discussion: Detailed discussion or analysis.
        pageNumber: Page number in the NUREG document.
        examples: List of example objects, each with a title and description.
    """
    section: Annotated[str, VectorStoreRecordDataField()] = Field(
        ..., description="The title of the section within NUREG 1022 this entry is from.")
    lxxii: Annotated[list[str], VectorStoreRecordDataField()] = Field(
        ..., description="List of 10 CFR 50.72 subsections referenced.")
    lxxiii: Annotated[list[str], VectorStoreRecordDataField()] = Field(
        ..., description="List of 10 CFR 50.73 subsections referenced.")
    description: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="descriptionVector")
    ] = Field(..., description="Textual description of the section.")
    discussion: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="discussionVector")
    ] = Field(..., description="Detailed discussion or analysis.")
    examples: Annotated[List[Example], VectorStoreRecordDataField()] = Field(
        ..., description="List of example events, each with a title and description.")

    def to_agent_string(self) -> str:
        """
        Returns a concise, readable string representation of the NUREGSection32 object for AI agent consumption.
        """
        examples_str = "\n".join([
            f"- {ex.title}: {ex.description}" for ex in self.examples
        ]) if self.examples else "None"
        return (
            "NUREG Section 3.2 Entry:\n"
            f"Document Id: {self.id}\n"
            f"Section Name: {self.section}\n"
            f"10 CFR 50.72: {', '.join(self.lxxii)}\n"
            f"10 CFR 50.73: {', '.join(self.lxxiii)}\n"
            f"Description: \n{self.description}\n"
            f"Discussion: \n{self.discussion}\n"
            f"Examples:\n{examples_str}"
        )

    def get_display_value(self):
        """Returns the section name as the display value for this NUREG section."""
        return self.section


class RequiredNotification(BaseModel):
    """
    Represents a requirement to provide notification

    Attributes:
        timeLimit: Time limit for providing the notification.
        notification: Description of the notification that is required.
    """
    timeLimit: Annotated[str, VectorStoreRecordDataField()] = Field(
        ..., description="Time limit for providing the notification.")
    notification: Annotated[str, VectorStoreRecordDataField()] = Field(
        ..., description="Description of the notification that is required.")


class RequiredReport(BaseModel):
    """
    Represents a requirement to provide a report.

    Attributes:
        timeLimit: Time limit for providing the report.
        notification: Notification
    """
    timeLimit: Annotated[str, VectorStoreRecordDataField()] = Field(
        ..., description="Time limit for providing the report.")
    notification: Annotated[str, VectorStoreRecordDataField()] = Field(
        ..., description="Notification")


@vectorstoremodel
class ReportabilityManual(SearchModelsBase):
    """
    The implementation of the SearchModelBase for the Reportability Manual.
    """
    sectionName: Annotated[str, VectorStoreRecordDataField()] = Field(...)
    references: Annotated[list[str], VectorStoreRecordDataField()] = Field(...)
    referenceContent: Annotated[str, VectorStoreRecordDataField()] = Field(...)
    discussion: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="discussionVector")
    ] = Field(...)
    requiredNotifications: Annotated[List[RequiredNotification], VectorStoreRecordDataField()] = Field(...)
    requiredWrittenReports: Annotated[List[RequiredReport], VectorStoreRecordDataField()] = Field(...)

    def to_agent_string(self) -> str:
        """
        Returns a concise, readable string representation of the ReportabilityManual object for AI agent consumption.
        """
        notifications_str = "\n".join([
            f"- {rn.timeLimit}: {rn.notification}" for rn in self.requiredNotifications
        ]) if self.requiredNotifications else "None"

        reports_str = "\n".join([
            f"- {rr.timeLimit}: {rr.notification}" for rr in self.requiredWrittenReports
        ]) if self.requiredWrittenReports else "None"

        return (
            "Reportability Manual Entry:\n"
            f"Document Id: {self.id}\n"
            f"Section Name: {self.sectionName}\n"
            f"References: \n{self.references}\n"
            f"Reference Content: \n{self.referenceContent}\n"
            f"Discussion: \n{self.discussion}\n"
            f"Required Notifications:\n{notifications_str}\n"
            f"Required Reports:\n{reports_str}"
        )

    def get_display_value(self):
        """Returns the section name as the display value for this Reportability Manual entry."""
        return self.sectionName


@vectorstoremodel
class NaiveSearch(SearchModelsBase):
    """
    The implementation of the SearchModelBase for the Naive Search.
    """
    chunk_id: Annotated[str, VectorStoreRecordDataField()] = Field(...)
    title: Annotated[str, VectorStoreRecordDataField()] = Field(...)
    url: Annotated[str, VectorStoreRecordDataField()] = Field(...)
    content: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="contentVector")
    ] = Field(...)

    def to_agent_string(self) -> str:
        """
        Returns a concise, readable string representation of the NaiveSearch object for AI agent consumption.
        """
        return (
            "Naive Search Entry:\n"
            f"Document Id: {self.chunk_id}\n"
            f"Title: {self.title}\n"
            f"url: \n{self.url}\n"
            f"Content: \n{self.content}\n"
        )

    def get_display_value(self):
        """Returns the title as the display value for this Naive Search entry."""
        return self.title
