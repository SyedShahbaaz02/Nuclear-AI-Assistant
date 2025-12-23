import asyncio
import os
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread

from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextEmbedding,
)
from semantic_kernel.connectors.memory.azure_ai_search import (
    AzureAISearchCollection,
)
from semantic_kernel.data.vector_search import VectorSearchOptions

from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    vectorstoremodel,
)
from semantic_kernel.functions import (
    KernelArguments,
    KernelParameterMetadata,
    KernelFunction
)

from azure.search.documents.indexes.aio import SearchIndexClient
from azure.core.credentials import AzureKeyCredential

from pydantic import BaseModel
from dotenv import load_dotenv


@vectorstoremodel
class LERResponseClass(BaseModel):
    ler_number: Annotated[str, VectorStoreRecordKeyField]
    report_date: Annotated[str, VectorStoreRecordDataField()]
    event_date: Annotated[str, VectorStoreRecordDataField()]
    facility_name: Annotated[str, VectorStoreRecordDataField()]
    title: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="titleVector")]
    cfr_requirements: Annotated[list[str], VectorStoreRecordDataField()]
    abstract: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="abstractVector")]
    narrative: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="narrativeVector")]

    # If you do not intend to retrieve the vectors (which is normal), don't add these to the data model.
    #
    # titleVector: Annotated[list[float] | None,
    #                        VectorStoreRecordVectorField(
    #                                 dimensions=1536,
    #                                 local_embedding=False,
    #                                 embedding_settings={
    #                                      "embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
    #                                 )]
    # abstractVector: Annotated[list[float] | None,
    #                           VectorStoreRecordVectorField(
    #                                 dimensions=1536,
    #                                 local_embedding=False,
    #                                 embedding_settings={
    #                                     "embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},)]
    # narrativeVector: Annotated[list[float] | None,
    #                            VectorStoreRecordVectorField(
    #                                 dimensions=1536,
    #                                 local_embedding=False,
    #                                 embedding_settings={
    #                                     "embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},)]


@vectorstoremodel
class NUREGResponseClass(BaseModel):
    id: Annotated[str, VectorStoreRecordKeyField]
    parent_id: Annotated[str, VectorStoreRecordDataField()]
    chunk: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")]


def prepare_kernel(functions: list[KernelFunction]) -> Kernel:
    """
    Prepares and configures a Semantic Kernel instance with Azure services and plugins.

    Args:
        functions (list[KernelFunction]): A list of functions to add to the kernel.

    Returns:
        Kernel: A configured Semantic Kernel instance.
    """
    kernel = Kernel()

    # Add the Azure services necessary
    kernel.add_service(AzureChatCompletion(
        service_id="azure-openai",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    ))

    embeddings = AzureTextEmbedding(service_id="azure_embedding",
                                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                                    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                                    deployment_name=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
                                    api_version=os.getenv("AZURE_OPENAI_API_VERSION"))

    if not kernel.services.get("azure_embedding"):
        kernel.add_service(embeddings)

    # Add Search as a plugin to the kernel
    kernel.add_functions(plugin_name="azure_ai_search",
                         functions=functions,
                         )

    return kernel


def prepare_search(index: str) -> AzureAISearchCollection[str, BaseModel]:
    """
    Prepares an Azure AI Search collection for managing and querying index data.

    Returns:
        AzureAISearchCollection[str, BaseModel]: The configured Azure AI Search collection.
    """
    credential = AzureKeyCredential(os.getenv("AZURE_AI_SEARCH_API_KEY"))
    # Create a SearchIndexClient for index management
    index_client = SearchIndexClient(endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
                                     credential=credential)

    if index == "ler":
        collection = AzureAISearchCollection[str, LERResponseClass](
            collection_name=os.getenv("LER_INDEX_NAME"),
            data_model_type=LERResponseClass,
            search_index_client=index_client
        )
    elif index == "nureg":
        collection = AzureAISearchCollection[str, NUREGResponseClass](
            collection_name=os.getenv("NUREG_INDEX_NAME"),
            data_model_type=NUREGResponseClass,
            search_index_client=index_client
        )
    return collection


# Testing method for running search separate from the AI call
async def run_search(kernel, collection: AzureAISearchCollection[str, LERResponseClass]):
    """
    Executes a test search query on the Azure AI Search collection.

    Args:
        kernel (Kernel): The Semantic Kernel instance.
        collection (AzureAISearchCollection[str, LERResponseClass]): The Azure AI Search collection.

    Returns:
        None
    """
    results = await collection.vectorizable_text_search(vectorizable_text="Turbine trip",
                                                        options=VectorSearchOptions(
                                                            vector_field_name="narrativeVector"
                                                        )
                                                        )
    async for result in results.results:
        print(result)


def define_agent(kernel: Kernel) -> ChatCompletionAgent:
    """
    Defines a ChatCompletionAgent for interacting with users and retrieving LER report information.

    Args:
        kernel (Kernel): The Semantic Kernel instance.

    Returns:
        ChatCompletionAgent: The configured chat agent.
    """
    execution_settings = kernel.get_prompt_execution_settings_from_service_id(service_id="azure-openai")

    agent = ChatCompletionAgent(
        kernel=kernel,
        name="ChatCompletionAgent",
        instructions="""
        You are a chat bot. Your name is Mosscap and
        you have one goal: help find the most relevant
        information for the user based on
        their request. You should be polite, helpful,
        but also concise. Always focus your answers around
        what the user is asking for, and what relevant
        information you were able to retrieve.

        You will be provided with tools to access
        regulatory documents, such as LER and NUREG reports.
        You can search for relevant reports based on
        the user's request.

        If no results come back from search, or nothing
        relevant is available, just let the user know.
        Do not draw on your own knowledge, or make up information.
        """,
        arguments=KernelArguments(
            settings=execution_settings,
        )
    )

    return agent


def create_kernel_function(index: str, collection: AzureAISearchCollection[str, BaseModel]) -> KernelFunction:
    """
    Creates a kernel function for searching LER or NUREG reports based on user input.
    Args:
        index (str): The type of index to search ("ler" or "nureg").
        collection (AzureAISearchCollection[str, BaseModel]): The Azure AI Search collection.
    Returns:
        KernelFunction: The configured kernel function for searching.
    """

    text_search = collection.create_text_search_from_vectorizable_text_search()
    if index == "ler":
        function = text_search.create_search(
                                    # For the hybrid search, for now it requires specifying a specific
                                    # vector field to search on, even if there are multiple vectors
                                    # in the index.
                                    options=VectorSearchOptions(
                                        vector_field_name="narrativeVector",
                                        top_k=3,
                                    ),
                                    description="""
                                            Search for relevant LER reports that may relate to the issue you are
                                            investigating. You do not need to know the LER report number, you can
                                            search by keywords across the title, abstract, or narrative.
                                            The narrative is focused on the event and the root cause, while the abstract
                                            is a summary of the entire report.""",
                                    parameters=[
                                        KernelParameterMetadata(name="query",
                                                                description="What to search for.",
                                                                type="str",
                                                                is_required=True,
                                                                type_object=str
                                                                )
                                    ],
                                    function_name="ler_search"
                                )
    elif index == "nureg":
        function = text_search.create_search(
                                    # For the hybrid search, for now it requires specifying a specific
                                    # vector field to search on, even if there are multiple vectors
                                    # in the index.
                                    options=VectorSearchOptions(
                                        vector_field_name="vector",
                                        top_k=3,
                                    ),
                                    description="""
                                            Search for relevant NUREG reports that may relate to the issue you are
                                            investigating. You do not need to know the NUREG report number, you can
                                            search by keywords across the chunks of text.""",
                                    parameters=[
                                        KernelParameterMetadata(name="query",
                                                                description="What to search for.",
                                                                type="str",
                                                                is_required=True,
                                                                type_object=str
                                                                )
                                    ],
                                    function_name="nureg_search"
                                )
    else:
        raise ValueError("Invalid index type. Must be 'ler' or 'nureg'.")
    # Create the function
    return function


async def main():
    """
    Main entry point for the script. Initializes the search collection, kernel, and agent,
    and handles user interaction in a loop.

    Returns:
        None
    """
    print("Which indexes do you want to use? Separate choices with a comma. Current options are: ler or nureg.")
    index = input("Index:> ")
    index = index.split(",")
    index = [i.strip() for i in index]
    index = [i.lower() for i in index]
    # Prepare the Azure AI Search collection
    functions = []
    collections: list[AzureAISearchCollection] = []
    for i in index:
        if i != "ler" and i != "nureg":
            raise ValueError("Invalid index type. Must be 'ler' or 'nureg'.")
        collection = prepare_search(i)
        collections.append(collection)
        search_function = create_kernel_function(i, collection)
        functions.append(search_function)
    kernel = prepare_kernel(functions)
    agent = define_agent(kernel)
    thread: ChatHistoryAgentThread = None

    print("What's your question?")
    is_complete: bool = False
    while not is_complete:
        user_input = input("User:> ")
        if not user_input:
            continue

        if user_input.lower() == "exit":
            is_complete = True
            for collection in collections:
                await collection.search_client.close()
            break
        first_chunk = True

        async for response in agent.invoke_stream(messages=user_input, thread=thread):
            thread = response.thread
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    runner = asyncio.run(main())

    print("Exiting...")
    exit(0)
