from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.contents import StreamingChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from typing import AsyncIterable

from .AgentBase import AgentBase
from constants import ChatServiceConstants
from models import ReportabilityContext
from functions import TSNaivePlugin, UFSARNaivePlugin, NuregPlugin, ReportabilityManualPlugin
from state import StateBase
from prompts.AgentsPrompt import AgentsPrompt


class NRCRecommendationAgent(AgentBase):
    """
    NRCRecommendationAgent is an agent responsible for making reportability recommendations
    for incidents at a power plant, specifically determining if an issue should be reported
    to the Nuclear Regulatory Commission (NRC) according to NUREG 1022 and relevant sections
    of 10 CFR 50.72 and 10 CFR 50.73.

    Methods:
        invoke_stream(context: KernelProcessStepContext, reportability_context: ReportabilityContext)
            Asynchronously constructs a prompt and leverages an AI agent with access to regulatory
            documents to determine reportability. The agent provides an approximate recommendation
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
            state=state,
            display_name="NRC Recommendation Agent",
            trace_name="NRCRecommendationAgent",
            plugin_defs=[
                (NuregPlugin(state.get_state(), auto_populate_document_lists=True), "NuregPlugin"),
                (
                    ReportabilityManualPlugin(state.get_state(), auto_populate_document_lists=True),
                    "ReportabilityManualPlugin"
                ),
                (TSNaivePlugin(state.get_state(), auto_populate_document_lists=True), "TSNaivePlugin"),
                (UFSARNaivePlugin(state.get_state(), auto_populate_document_lists=True), "UFSARNaivePlugin")
            ]
        )

    def _get_instructions(self) -> str:
        return AgentsPrompt.NRCRecommendationAgentPrompt

    def _get_kernel_arguments(self, kernel: Kernel) -> KernelArguments:
        execution_settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=ChatServiceConstants.CHAT_SERVICE_ID.value
        )

        return KernelArguments(settings=execution_settings)

    @kernel_function(
        name="NRCRecommendationAgent.invoke_stream",
        description="Streams recommendations for NRC reportability based on user input and regulatory documents."
    )
    async def invoke_stream(self) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Asynchronously constructs a prompt and leverages an AI agent to determine reportability."""
        # Construct a prompt for making a recommendation
        agent: ChatCompletionAgent = self._get_agent()
        state: ReportabilityContext = self._state.get_state()
        thread: ChatHistoryAgentThread = state.get_agent_thread()

        req_settings = agent.kernel.get_prompt_execution_settings_from_service_id(service_id="azure-openai")

        req_settings.temperature = ChatServiceConstants.DEFAULT_TEMPERATURE.value

        return agent.invoke_stream(
            thread=thread,
            arguments=KernelArguments(settings=req_settings),
            messages=state.message_history,
        )
