from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import StreamingChatMessageContent
from semantic_kernel.functions import KernelArguments
from typing import AsyncIterable

from .AgentBase import AgentBase
from models import ReportabilityContext
from state import StateBase
from util import get_agent_response_item
from constants import ChatServiceConstants
from prompts.AgentsPrompt import AgentsPrompt


class RecommendationAgent(AgentBase):
    """
    RecommendationAgent is an agent responsible for making reportability recommendations
    for incidents at a power plant, specifically determining if an issue should be reported
    to the Nuclear Regulatory Commission (NRC) according to NUREG 1022 and relevant sections
    of 10 CFR 50.72 and 10 CFR 50.73.

    Methods:
        invoke_stream(context: KernelProcessStepContext, reportability_context: ReportabilityContext)
            The agent provides an approximate recommendation
            of whether the issue is likely reportable or not, including reasoning and references to
            specific regulatory subsections. If insufficient information is available, the agent notifies
            the user. The method emits a RECOMMENDATION_READY event with the streaming response.
    """
    def __init__(self, state: StateBase[ReportabilityContext]) -> None:
        """Initializes the agent with a ReportabilityContext.

        Args:
            context (ReportabilityContext): The context for agent operations.
        """
        super().__init__(
            display_name="Recommendation Agent",
            trace_name="RecommendationAgent",
            state=state
        )

    def _get_instructions(self) -> str:
        return AgentsPrompt.RecommendationAgentPrompt

    async def invoke_stream(self) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Asynchronously constructs a prompt and leverages an AI agent to determine reportability."""
        # Construct a prompt for making a recommendation
        agent: ChatCompletionAgent = self._get_agent()
        state: ReportabilityContext = self._state.get_state()
        thread: ChatHistoryAgentThread = state.get_agent_thread()
        execution_settings: PromptExecutionSettings = agent.kernel.get_prompt_execution_settings_from_service_id(
            service_id=ChatServiceConstants.CHAT_SERVICE_ID.value
        )
        execution_settings.temperature = ChatServiceConstants.DEFAULT_TEMPERATURE.value

        async for response in agent.invoke_stream(
            arguments=KernelArguments(settings=execution_settings),
            thread=thread,
            messages=state.message_history
        ):
            self.track_token_usage(response)
            yield get_agent_response_item(
                    response.message.content,
                    thread,
                    flush=False,
                    yield_to_user=True,
                    add_to_chat_history=True,
                    combine_before_adding_to_history=True
                )
