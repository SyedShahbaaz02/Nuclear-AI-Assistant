from abc import ABC, abstractmethod
from opentelemetry import trace
from semantic_kernel.agents import Agent, ChatCompletionAgent
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.contents import StreamingChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from typing import AsyncIterator, List, Tuple

from functions.SearchPlugins import SearchPluginsBase
from models import ReportabilityContext, TokenUsage
from services import ReportabilityServices
from state import StateBase


class AgentBase(ABC):
    """Abstract base class for streaming agents acting on a ResportabilityContext."""
    """The plugin definitions and services are defined in the subclasses."""
    _plugin_defs: List[Tuple[SearchPluginsBase, str]]
    _services: List[AIServiceClientBase]
    _trace_name: str
    display_name: str

    def __init__(
            self,
            display_name: str,
            trace_name: str,
            state: StateBase[ReportabilityContext],
            plugin_defs: List[Tuple[SearchPluginsBase, str]] = None,
            services: List[AIServiceClientBase] = None
    ) -> None:
        """Initializes the agent with a StateBase.

        Args:
            state (StateBase): The state for agent operations.
        """
        self.display_name = display_name
        self._trace_name = trace_name
        self._state = state
        self._plugin_defs = plugin_defs if plugin_defs is not None else []
        self._services = services if services is not None else []
        self._services.append(ReportabilityServices.get_chat_completion_service())
        self._agent = None

    def _get_kernel(self) -> Kernel:
        """Returns the Kernel instance for the agent.

        Returns:
            Kernel: The kernel instance.
        """
        kernel = Kernel()

        for service in self._services:
            kernel.add_service(service)

        for plugin_def in self._plugin_defs:
            kernel.add_plugin(plugin_def[0], plugin_def[1])

        return kernel

    @abstractmethod
    def _get_instructions(self) -> str:
        """Returns the instructions for the agent.

        Returns:
            str: Instructions for the agent.
        """
        pass

    @abstractmethod
    async def invoke_stream(self) -> AsyncIterator[AgentResponseItem[StreamingChatMessageContent]]:
        """Streams agent responses based on input data and context.

        Args:
            input_data (Any): Data to process.

        Yields:
            Any: Streamed response items.
        """
        pass

    def _get_kernel_arguments(self, kernel: Kernel) -> KernelArguments:
        """Returns the kernel arguments for the agent.

        By default, this returns None, but can be overridden by subclasses.

        Returns:
            KernelArguments: Kernel arguments for the agent.
        """
        return None

    def _get_agent(self) -> Agent:
        if self._agent is not None:
            return self._agent

        kernel = self._get_kernel()

        self._agent = ChatCompletionAgent(
            kernel=kernel,
            instructions=self._get_instructions(),
            arguments=self._get_kernel_arguments(kernel),
            name=self._trace_name
        )

        return self._agent

    def track_token_usage(self, response: AgentResponseItem) -> None:
        """Tracks token usage from the agent response.

        Args:
            response (AgentResponseItem): The response containing token usage info.
        """
        state: ReportabilityContext = self._state.get_state()
        usage = response.metadata.get('usage')
        if state and usage:
            token_usage: TokenUsage = TokenUsage(
                agent_name=self._trace_name,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens
            )
            state.token_usage.append(token_usage)
            # Add token usage to current trace span
            span = trace.get_current_span()
            if span is not None:
                span.set_attribute("agent_name", self._trace_name)
                span.set_attribute("prompt_tokens", usage.prompt_tokens)
                span.set_attribute("completion_tokens", usage.completion_tokens)
