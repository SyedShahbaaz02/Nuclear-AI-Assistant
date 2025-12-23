from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import StreamingChatMessageContent
from semantic_kernel.functions import KernelArguments
from typing import AsyncIterable

from .AgentBase import AgentBase
from constants import ChatServiceConstants
from functions import ContextPlugin
from models import ReportabilityContext
from state import StateBase
from prompts.AgentsPrompt import AgentsPrompt


class IntentAgent(AgentBase):
    def __init__(self, state: StateBase[ReportabilityContext]) -> None:
        """Initializes the agent with a ReportabilityContext.

        Args:
            state (StateBase[ReportabilityContext]): The state for agent operations.
        """
        super().__init__(
            display_name="Intent Detection Agent",
            trace_name="IntentDetectionAgent",
            state=state,
            plugin_defs=[(ContextPlugin(state.get_state()), "ContextPlugin")]
        )

    def _get_instructions(self) -> str:
        return AgentsPrompt.IntentAgentPrompt

    async def invoke_stream(self) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Asynchronously constructs a prompt and leverages an AI agent to determine user intent."""
        # Construct a prompt for making a recommendation
        agent: ChatCompletionAgent = self._get_agent()
        state: ReportabilityContext = self._state.get_state()
        thread: ChatHistoryAgentThread = state.get_agent_thread()
        execution_settings: PromptExecutionSettings = agent.kernel.get_prompt_execution_settings_from_service_id(
            service_id=ChatServiceConstants.CHAT_SERVICE_ID.value
            )
        execution_settings.temperature = ChatServiceConstants.DEFAULT_TEMPERATURE.value

        return agent.invoke_stream(
            arguments=KernelArguments(settings=execution_settings),
            thread=thread,
            messages=state.message_history,
        )
