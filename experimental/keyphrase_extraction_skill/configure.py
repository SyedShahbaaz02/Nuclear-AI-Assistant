import os
import pathlib
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.search.documents.indexes import (
    SearchIndexClient,
    SearchIndexerClient
)
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchIndexer,
    SearchIndexerDataSourceConnection,
    SearchIndexerSkillset
)
from dotenv import load_dotenv

APPLICATION_JSON_CONTENT_TYPE = 'application/json'
DEFAULT_AUDIENCE = '.default'
ENV_FILE_NAME = '.env'
ENV_VAR_AI_SEARCH_ENDPOINT = 'AI_SEARCH_ENDPOINT'
ENV_VAR_AI_SEARCH_SERVICE_NAME = 'AI_SEARCH_NAME'
ENV_VAR_STORAGE_ACCOUNT_NAME = 'STORAGE_ACCOUNT_NAME'
ENV_VAR_WEBAPP_NAME = 'WEBAPP_NAME'
ENV_VAR_OPENAI_ADA_DEPLOYMENT_ID = 'OPENAI_ADA_DEPLOYMENT_ID'
ENV_VAR_OPENAI_ADA_LARGE_DEPLOYMENT_ID = 'OPENAI_ADA_LARGE_DEPLOYMENT_ID'
ENV_VAR_OPENAI_API_KEY = 'OPENAI_API_KEY'  # pragma: allowlist secret
ENV_VAR_OPENAI_ENDPOINT = 'OPENAI_ENDPOINT'
ENV_VAR_RESOURCE_GROUP_NAME = 'RESOURCE_GROUP_NAME'
ENV_VAR_SUBSCRIPTION_ID = 'AZURE_SUBSCRIPTION_ID'
GOVCLOUD_MANAGEMENT_ENDPOINT = 'https://management.usgovcloudapi.net'
AI_SEARCH_DATASOURCES_RELATIVE_PATH = '../../infra/config/aisearch/datasources'
AI_SEARCH_INDEXES_RELATIVE_PATH = './index'
AI_SEARCH_INDEXERS_RELATIVE_PATH = './indexer'
AI_SEARCH_SKILLSETS_RELATIVE_PATH = './skillset'
ROOT_FILE_DIR = pathlib.Path(__file__).parent.resolve()


def _generate_ai_search_key_credential(default_credential: DefaultAzureCredential) -> AzureKeyCredential:
    """
    Generates an AI Search Key Credential, used for configuring AI Search
    """
    print('Retrieving AI Search Admin Key.')
    try:
        search_management_client = SearchManagementClient(
            credential=default_credential,
            subscription_id=os.getenv(key=ENV_VAR_SUBSCRIPTION_ID),
            base_url=GOVCLOUD_MANAGEMENT_ENDPOINT,
            credential_scopes=[GOVCLOUD_MANAGEMENT_ENDPOINT + '/' + DEFAULT_AUDIENCE]
        )
        key = search_management_client.admin_keys.get(
            resource_group_name=os.getenv(key=ENV_VAR_RESOURCE_GROUP_NAME),
            search_service_name=os.getenv(key=ENV_VAR_AI_SEARCH_SERVICE_NAME)
        )
    except Exception as e:
        print(f"Unable to retrieve AI Search Admin Keys: {e}")
        raise e

    return AzureKeyCredential(key=key.primary_key)


def _generate_storage_account_connection_string(default_credential: DefaultAzureCredential) -> str:
    """
    Generates the connection string to use for the data source connection.
    """
    print("Retrieving storage account connection string.")
    try:
        storage_client = StorageManagementClient(
            credential=default_credential,
            subscription_id=os.getenv(key=ENV_VAR_SUBSCRIPTION_ID),
            base_url=GOVCLOUD_MANAGEMENT_ENDPOINT,
            credential_scopes=[GOVCLOUD_MANAGEMENT_ENDPOINT + '/' + DEFAULT_AUDIENCE]
        )
        storage_account_name = os.getenv(key=ENV_VAR_STORAGE_ACCOUNT_NAME)
        keys = storage_client.storage_accounts.list_keys(
            resource_group_name=os.getenv(key=ENV_VAR_RESOURCE_GROUP_NAME),
            account_name=storage_account_name
        )
        conn_string = (
            'DefaultEndpointsProtocol=https;AccountName={storage_account_name};' +
            'AccountKey={key};' +
            'EndpointSuffix=core.usgovcloudapi.net'
        ).format(
            storage_account_name=storage_account_name,
            key=keys.keys[0].value
        )
    except Exception as e:
        print(f"Could not retrieve the storage account connection string. {e}")
        raise e

    return conn_string


def _create_or_update_search_indexes(key_credential: AzureKeyCredential):
    """
    Creates or updates the search indexes in Azure AI Search.
    """
    print("Creating or updating search index in Azure AI Search...")

    try:
        index_client = SearchIndexClient(endpoint=os.getenv(key=ENV_VAR_AI_SEARCH_ENDPOINT), credential=key_credential)
        indexes_path = pathlib.Path(ROOT_FILE_DIR, AI_SEARCH_INDEXES_RELATIVE_PATH).resolve()

        for index_file in indexes_path.iterdir():
            if index_file.is_file():
                with index_file.open("r") as index_json:
                    index_str = index_json.read()

                index_str = index_str.replace("<openaiResourceUri>", os.getenv(key=ENV_VAR_OPENAI_ENDPOINT)) \
                                     .replace("<openaiApiKey>", os.getenv(key=ENV_VAR_OPENAI_API_KEY)) \
                                     .replace(
                                         "<openaiAdaDeploymentId>",
                                         os.getenv(key=ENV_VAR_OPENAI_ADA_DEPLOYMENT_ID)
                                     ).replace(
                                        "<openaiAdaLargeDeploymentId>",
                                        os.getenv(key=ENV_VAR_OPENAI_ADA_LARGE_DEPLOYMENT_ID)
                                     )

                index = SearchIndex.deserialize(data=index_str, content_type=APPLICATION_JSON_CONTENT_TYPE)

                result = index_client.create_or_update_index(index=index)
                print(f"Index created/updated successfully: {result.name}")
    except Exception as e:
        print(f"Error creating/updating index: {e}")
        raise e


def _create_or_update_datasources(default_credential: DefaultAzureCredential, indexer_client: SearchIndexerClient):
    """
    Creates or updates the data sources in Azure AI Search.
    """
    print("Creating or updating data sources in Azure AI Search...")

    try:
        datasources_path = pathlib.Path(ROOT_FILE_DIR, AI_SEARCH_DATASOURCES_RELATIVE_PATH).resolve()
        connection_string = _generate_storage_account_connection_string(default_credential=default_credential)

        for datasource_file in datasources_path.iterdir():
            if datasource_file.is_file():
                with open(datasource_file, "r") as datasource_json:
                    datasource_str = datasource_json.read()

                datasource_str = datasource_str.replace("<connectionString>", connection_string)
                data_source = SearchIndexerDataSourceConnection.deserialize(
                    data=datasource_str,
                    content_type=APPLICATION_JSON_CONTENT_TYPE
                )
                result = indexer_client.create_or_update_data_source_connection(data_source_connection=data_source)
                print(f"Data source created/updated successfully: {result.name}")
    except Exception as e:
        print(f"Error creating/updating data source: {e}")
        raise e


def _create_or_update_skillsets(indexer_client: SearchIndexerClient):
    """
    Creates or updates the skillsets in Azure AI Search.
    """
    print("Creating or updating skillsets in Azure AI Search...")

    try:
        skillsets_path = pathlib.Path(ROOT_FILE_DIR, AI_SEARCH_SKILLSETS_RELATIVE_PATH).resolve()

        for skillset_file in skillsets_path.iterdir():
            if skillset_file.is_file():
                with open(skillset_file, "r") as skillset_json:
                    skillset_str = skillset_json.read()

                skillset_str = skillset_str.replace("<openaiResourceUri>", os.getenv(ENV_VAR_OPENAI_ENDPOINT)) \
                                           .replace("<openaiApiKey>", os.getenv(ENV_VAR_OPENAI_API_KEY)) \
                                           .replace(
                                               "<openaiAdaDeploymentId>",
                                               os.getenv(ENV_VAR_OPENAI_ADA_DEPLOYMENT_ID)
                                           ).replace(
                                               "<openaiAdaLargeDeploymentId>",
                                               os.getenv(ENV_VAR_OPENAI_ADA_LARGE_DEPLOYMENT_ID)
                                           ).replace(
                                               "<webAppName>",
                                               os.getenv(ENV_VAR_WEBAPP_NAME).lower()
                                           )

                skillset = SearchIndexerSkillset.deserialize(
                    data=skillset_str,
                    content_type=APPLICATION_JSON_CONTENT_TYPE
                )
                result = indexer_client.create_or_update_skillset(skillset=skillset)
                print(f"Skillset created/updated successfully: {result.name}")
    except Exception as e:
        print(f"Error creating/updating skillset: {e}")
        raise e


def _create_or_update_indexers(indexer_client: SearchIndexerClient):
    """
    Creates or updates the indexers in Azure AI Search.
    """
    print("Creating or updating indexers in Azure AI Search...")

    try:
        indexer_path = pathlib.Path(ROOT_FILE_DIR, AI_SEARCH_INDEXERS_RELATIVE_PATH).resolve()

        for indexer_file in indexer_path.iterdir():
            if indexer_file.is_file():
                with open(indexer_file, "r") as indexer_json:
                    indexer_str = indexer_json.read()

                indexer = SearchIndexer.deserialize(data=indexer_str, content_type=APPLICATION_JSON_CONTENT_TYPE)
                result = indexer_client.create_or_update_indexer(indexer=indexer)
                print(f"Indexer created/updated successfully: {result.name}")
    except Exception as e:
        print(f"Error creating/updating indexer: {e}")
        raise e


def _configure_ai_search():
    print("Configuring Azure AI Search...")
    default_credential = DefaultAzureCredential()
    key_credential = _generate_ai_search_key_credential(default_credential=default_credential)

    _create_or_update_search_indexes(key_credential=key_credential)

    indexer_client = SearchIndexerClient(
        endpoint=os.getenv(ENV_VAR_AI_SEARCH_ENDPOINT),
        credential=key_credential
    )

    _create_or_update_datasources(default_credential=default_credential, indexer_client=indexer_client)
    _create_or_update_skillsets(indexer_client=indexer_client)
    _create_or_update_indexers(indexer_client=indexer_client)

    print("Azure AI Search configuration completed.")


def _deploy_configs():
    """
    Deploys the resource configurations to Azure.
    """

    print("Deploying resource configurations to Azure...")

    _configure_ai_search()

    print("Resource configurations deployed successfully.")


if __name__ == "__main__":
    load_dotenv(pathlib.Path(ROOT_FILE_DIR, ENV_FILE_NAME))
    _deploy_configs()
