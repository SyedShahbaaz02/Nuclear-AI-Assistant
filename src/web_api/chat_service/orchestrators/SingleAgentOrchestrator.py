from opentelemetry import trace
from typing import AsyncIterator

from .OrchestratorBase import OrchestratorBase
from agents import NRCRecommendationAgent, RecommendationExtractionAgent
from models import ReportabilityContext
from state import StateBase


class SingleAgentOrchestrator(OrchestratorBase[ReportabilityContext]):
    """Sequential orchestration for agents using Semantic Kernel's SequentialOrchestrator."""

    def __init__(self, state: StateBase[ReportabilityContext]):
        """
        Initialize the SingleAgentOrchestrator with a given state.

        Args:
            state: The state object containing the chat request and other necessary information.
        """
        super().__init__(state)

    async def invoke_stream(self) -> AsyncIterator[str]:
        """Invoke the orchestration of communication with agents and stream responses.

        Yields:
            str: Streamed response from agent.
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("SingleAgentOrchestrator.invoke_stream"):
            agent: NRCRecommendationAgent = NRCRecommendationAgent(state=self._state)
            message = ""
            async for response in await agent.invoke_stream():
                message += response.message.content
                agent.track_token_usage(response)
                yield response

            # If the eval content is included, we need to extract the recommendations
            if self._state.get_state().include_eval_content:
                self._state.get_state().message_history.add_assistant_message(message)
                extraction_agent = RecommendationExtractionAgent(state=self._state)
                await extraction_agent.invoke()

            # Since the single agent orchestrator only uses one agent, we know that all of the documents received from
            # the indexes were reviewed by the agent. So we need to mark them all as such.
            state = self._state.get_state()
            for result in state.plugin_results:
                result.cited = True
