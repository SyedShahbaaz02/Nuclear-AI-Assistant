import os

from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion, AzureTextEmbedding)

from constants import ChatServiceConstants, EnvironmentVariables


class ReportabilityServices:
    """
    ReportabilityServices provides static methods to initialize and retrieve Azure-based AI services
    for chat completion and text embedding functionalities. The services are configured using
    environment variables for credentials and deployment details.
    """
    @staticmethod
    def get_ai_search_client(index_name: str) -> SearchClient:
        """
        Initializes and returns an instance of SearchClient for querying Azure Cognitive Search.

        Args:
            index_name (str): The name of the Azure Cognitive Search index to connect to.

        Environment Variables:
            AZURE_SEARCH_SERVICE_ENDPOINT: The endpoint URL for the Azure Cognitive Search service.
            AZURE_SEARCH_API_KEY: The API key for authenticating with the Azure Cognitive Search service.

        Returns:
            SearchClient: An instance of SearchClient configured with the specified index name and credentials.
        """
        service_endpoint = os.environ[EnvironmentVariables.AZURE_SEARCH_SERVICE_ENDPOINT.value]
        key = os.environ[EnvironmentVariables.AZURE_SEARCH_API_KEY.value]

        credential = AzureKeyCredential(key)
        # Create a SearchClient for querying
        return SearchClient(
            endpoint=service_endpoint,
            index_name=index_name,
            credential=credential)

    @staticmethod
    def get_chat_completion_service() -> AzureChatCompletion:
        """
        Initializes and returns an instance of AzureChatCompletion using configuration values
        from environment variables.

        Environment Variables:
            AZURE_OPENAI_API_KEY: The API key for authenticating with Azure OpenAI.
            AZURE_OPENAI_ENDPOINT: The endpoint URL for the Azure OpenAI service.
            AZURE_OPENAI_DEPLOYMENT: The deployment name for the Azure OpenAI model.
            AZURE_OPENAI_API_VERSION: The API version to use for the Azure OpenAI service.

        Returns:
            AzureChatCompletion: A chat completion instance configured with the specified environment variables.
        """
        api_key = os.getenv(EnvironmentVariables.AZURE_OPENAI_API_KEY.value)
        endpoint = os.getenv(EnvironmentVariables.AZURE_OPENAI_ENDPOINT.value)
        deployment_name = os.getenv(EnvironmentVariables.AZURE_OPENAI_DEPLOYMENT.value)
        api_version = os.getenv(EnvironmentVariables.AZURE_OPENAI_API_VERSION.value)

        return AzureChatCompletion(
            service_id=ChatServiceConstants.CHAT_SERVICE_ID.value,
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
        )

    @staticmethod
    def get_text_embedding_service() -> AzureTextEmbedding:
        """
        Initializes and returns an instance of AzureTextEmbedding using environment variables.

        Environment Variables:
            AZURE_OPENAI_API_KEY: The API key for authenticating with Azure OpenAI.
            AZURE_OPENAI_ENDPOINT: The endpoint URL for the Azure OpenAI service.
            AZURE_EMBEDDING_DEPLOYMENT: The deployment name for the Azure OpenAI embedding model.
            AZURE_OPENAI_API_VERSION: The API version to use for the Azure OpenAI service.

        Returns:
            AzureTextEmbedding: An text embedding service instance configured with the specified environment variables.
        """
        api_key = os.getenv(EnvironmentVariables.AZURE_OPENAI_API_KEY.value)
        endpoint = os.getenv(EnvironmentVariables.AZURE_OPENAI_ENDPOINT.value)
        deployment_name = os.getenv(EnvironmentVariables.AZURE_EMBEDDING_DEPLOYMENT.value)
        api_version = os.getenv(EnvironmentVariables.AZURE_OPENAI_API_VERSION.value)

        return AzureTextEmbedding(
            service_id=ChatServiceConstants.EMBEDDING_SERVICE_ID.value,
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
        )

    @staticmethod
    def get_sas_token(account_name: str, container_name: str, blob_name: str) -> str:
        """
        Retrieves the SAS token for the blob item.

        Args:
            account_name (str): The name of the Azure storage account.
            container_name (str): The name of the container in the Azure storage account.
            blob_name (str): The name of the blob for which the SAS token is generated.

        Returns:
            str: A SAS token that grants read access to the specified blob for a limited time.
        """

        # Define the SAS token parameters
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=os.getenv(EnvironmentVariables.AZURE_BLOB_KEY.value),
            permission=BlobSasPermissions(read=True),
            expiry=(
                datetime.now() +
                timedelta(
                    days=float(
                        os.getenv(EnvironmentVariables.SAS_TOKEN_EXPIRATIONS_DAYS.value)
                    )
                )
            )
        )

        return sas_token
