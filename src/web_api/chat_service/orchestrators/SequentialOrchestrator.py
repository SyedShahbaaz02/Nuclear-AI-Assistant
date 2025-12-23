from opentelemetry import trace
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.contents import StreamingChatMessageContent
from typing import AsyncIterator

from .OrchestratorBase import OrchestratorBase
from agents import (
    AgentBase,
    IntentAgent,
    NuregAgent,
    RecommendationAgent,
    RecommendationExtractionAgent,
    ReportabilityManualAgent,
)
from models import Intent, ReportabilityContext
from state import StateBase
from util import StreamingMessageMetadata, get_agent_response_item


class SequentialAgentOrchestrator(OrchestratorBase[ReportabilityContext]):
    """Sequential orchestration for agents using a sequential flow."""

    def __init__(self, state: StateBase[ReportabilityContext], agents: list[AgentBase] = None):
        """
        Initialize the SequentialAgentOrchestrator with a given state.

        Args:
            state: The state object containing the chat request and other necessary information.
            agents: Optional list of agents to be used in the orchestration. If not provided, defaults to None.
        """
        super().__init__(state)
        self._intent_agent: AgentBase = IntentAgent(state=state)
        self._extraction_agent: RecommendationExtractionAgent = RecommendationExtractionAgent(state=state)
        if agents is not None:
            self._agents = agents
        else:
            self._agents: list[AgentBase] = [
                ReportabilityManualAgent(state=state),
                NuregAgent(state=state),
                RecommendationAgent(state=state)
            ]

    async def invoke_stream(self) -> AsyncIterator[AgentResponseItem[StreamingChatMessageContent]]:
        """Invoke the orchestration of communication with agents and stream responses.

        Yields:
            str: Streamed response from agent.
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("SequentialAgentOrchestrator.invoke_stream"):
            async for response in await self._intent_agent.invoke_stream():
                self._intent_agent.track_token_usage(response)
                if response.message.content:
                    yield response

            if self._state.get_state().intent == Intent.INVALID:
                return
            for agent in self._agents:
                message = ""
                yield get_agent_response_item(
                    f"## Engaging {agent.display_name}\n\n",
                    self._state.get_state().get_agent_thread(),
                    flush=True
                )

                async for response in agent.invoke_stream():
                    yield_to_user = response.message.metadata.get(StreamingMessageMetadata.YIELD_TO_USER.value, True)
                    add_to_chat_history = response.message.metadata.get(
                        StreamingMessageMetadata.ADD_TO_CHAT_HISTORY.value, True
                    )
                    combine_before_adding_to_history = response.message.metadata.get(
                        StreamingMessageMetadata.COMBINE_BEFORE_ADDING_TO_HISTORY.value, True
                    )
                    if add_to_chat_history:
                        if combine_before_adding_to_history:
                            message += response.message.content
                        else:
                            self._state.get_state().message_history.add_assistant_message(response.message.content)
                    if yield_to_user:
                        yield response

                if self._state.get_state().user_input_needed:
                    return

                if message:
                    self._state.get_state().message_history.add_assistant_message(message)

            await self._extraction_agent.invoke()
