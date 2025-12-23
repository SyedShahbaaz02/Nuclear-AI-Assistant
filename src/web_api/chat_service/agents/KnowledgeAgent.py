import json
import logging

from abc import ABC, abstractmethod
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.functions import KernelArguments
from typing import AsyncIterable, Iterable, List, Tuple, Type

from .AgentBase import AgentBase
from constants import ChatServiceConstants
from functions.SearchPlugins import SearchPluginsBase
from models import ReportabilityContext
from state import StateBase
from prompts.AgentsPrompt import AgentsPrompt
from util import get_agent_response_item

logger = logging.getLogger(ChatServiceConstants.LOGGER_NAME.value + __name__)


class KnowledgeAgentBase(AgentBase, ABC):
    """Abstract base class for knowledge agents that review and cite documents."""

    def __init__(
            self,
            display_name: str,
            trace_name: str,
            state: StateBase[ReportabilityContext],
            plugin_defs: List[Tuple[SearchPluginsBase, str]] = None
    ) -> None:
        """Initializes the agent with a state object."""
        super().__init__(display_name=display_name, trace_name=trace_name, state=state, plugin_defs=plugin_defs)

    @abstractmethod
    def get_knowledge_specific_instructions(self) -> str:
        """Returns the instructions for the agent."""
        pass

    @abstractmethod
    def get_reviewed_doc_model(self) -> Type:
        """Returns the class type for reviewed documents."""
        pass

    def _get_instructions(self) -> str:
        return self.get_knowledge_specific_instructions() + " " + AgentsPrompt.KnowledgeAgentPrompt

    def _mark_cited_document(self, state: ReportabilityContext, response: AgentResponseItem[ChatMessageContent]):
        logger.debug(f"Parsing response from the Knowledge agent {response}.")
        document_ids = json.loads(response.message.content)
        if not isinstance(document_ids, list):
            raise ValueError("Response is not a list of document identifiers.")
        if not all(isinstance(doc_id, str) for doc_id in document_ids):
            raise ValueError("All document identifiers must be strings.")
        for result in state.plugin_results:
            if result.id in document_ids:
                result.cited = True

    def _yield_reviewed_documents(
        self, state: ReportabilityContext, thread: ChatHistoryAgentThread
    ) -> Iterable[AgentResponseItem[StreamingChatMessageContent]]:
        doc_model = self.get_reviewed_doc_model()
        for document in state.plugin_results:
            if isinstance(document, doc_model):
                yield get_agent_response_item(
                    (
                        f"\nReviewed [{document.get_display_value()}]"
                        f"({document.get_document_url()}). \n"
                    ),
                    thread,
                    flush=True,
                    yield_to_user=True,
                    add_to_chat_history=False
                )

    def _yield_cited_documents(
        self, state: ReportabilityContext, thread: ChatHistoryAgentThread
    ) -> Iterable[AgentResponseItem[StreamingChatMessageContent]]:
        doc_model = self.get_reviewed_doc_model()
        for document in state.plugin_results:
            if isinstance(document, doc_model) and document.cited:
                yield get_agent_response_item(
                    (
                        f"\nCiting [{document.get_display_value()}]"
                        f"({document.get_document_url()}) . \n"
                    ),
                    thread,
                    flush=True,
                    yield_to_user=True,
                    add_to_chat_history=False
                )
                yield get_agent_response_item(
                    document.to_agent_string(),
                    thread,
                    flush=False,
                    yield_to_user=False,
                    add_to_chat_history=True,
                    combine_before_adding_to_history=False
                )

    async def invoke_stream(self) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Streams agent responses based on input data and context."""
        agent: ChatCompletionAgent = self._get_agent()
        state = self._state.get_state()
        thread: ChatHistoryAgentThread = state.get_agent_thread()
        execution_settings: PromptExecutionSettings = agent.kernel.get_prompt_execution_settings_from_service_id(
            service_id=ChatServiceConstants.CHAT_SERVICE_ID.value
        )
        execution_settings.temperature = ChatServiceConstants.DEFAULT_TEMPERATURE.value

        async for response in agent.invoke(
            arguments=KernelArguments(settings=execution_settings),
            thread=thread,
            messages=state.message_history
        ):
            self.track_token_usage(response)
            self._mark_cited_document(state, response)
            for item in self._yield_reviewed_documents(state, thread):
                yield item
            for item in self._yield_cited_documents(state, thread):
                yield item
