import json

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.functions import KernelArguments
from typing import AsyncIterable

from .AgentBase import AgentBase
from constants import ChatServiceConstants
from models import ReportabilityContext
from state import StateBase
from prompts.AgentsPrompt import AgentsPrompt


class RecommendationExtractionAgent(AgentBase):
    def __init__(self, state: StateBase[ReportabilityContext]) -> None:
        """Initializes the agent with a ReportabilityContext.

        Args:
            context (ReportabilityContext): The context for agent operations.
        """
        super().__init__(
            display_name="Recommendation Extraction Agent",
            trace_name="RecommendationExtractionAgent",
            state=state
        )

    def _get_instructions(self) -> str:
        return AgentsPrompt.RecommendationExtractionAgentPrompt

    def _store_response(self, state: ReportabilityContext, response: AgentResponseItem[ChatMessageContent]):
        self.track_token_usage(response)
        content = response.message.content
        if not content or not content.strip():
            raise ValueError("No content in the agent response to process.")
        try:
            recommendations = json.loads(content)
        except Exception:
            raise ValueError("Agent response content is not valid JSON.")
        if not isinstance(recommendations, list):
            raise ValueError("Agent response content is not a list.")
        state.recommendations.extend(recommendations)

    async def invoke_stream(self) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        raise NotImplementedError("Streaming is not supported for RecommendationExtractionAgent.")

    async def invoke(self) -> AgentResponseItem[ChatMessageContent]:
        """Invokes the agent to process the latest chat message and extract recommendations."""
        agent: ChatCompletionAgent = self._get_agent()
        state: ReportabilityContext = self._state.get_state()
        thread: ChatHistoryAgentThread = state.get_agent_thread()
        execution_settings: PromptExecutionSettings = agent.kernel.get_prompt_execution_settings_from_service_id(
            service_id=ChatServiceConstants.CHAT_SERVICE_ID.value
        )
        execution_settings.temperature = ChatServiceConstants.DEFAULT_TEMPERATURE.value

        # We only need to send the last message in the chat history to the agent,
        # as that's the message that has the recommendation in it.
        if not state.message_history.messages:
            raise ValueError("No messages in the chat history to process.")
        last_message = state.message_history.messages[-1]

        response: AgentResponseItem[ChatMessageContent] = await agent.get_response(
            arguments=KernelArguments(settings=execution_settings),
            thread=thread,
            messages=[last_message],
        )
        self._store_response(state, response)
