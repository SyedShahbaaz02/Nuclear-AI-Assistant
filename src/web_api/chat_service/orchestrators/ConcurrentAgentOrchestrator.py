from .OrchestratorBase import OrchestratorBase
from models import Intent, ReportabilityContext
from opentelemetry import trace
from asyncio import FIRST_COMPLETED, Task, create_task, wait
from typing import AsyncIterable, AsyncIterator, Collection
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.contents import StreamingChatMessageContent
from agents import (
    AgentBase,
    IntentAgent,
    NuregAgent,
    RecommendationAgent,
    RecommendationExtractionAgent,
    ReportabilityManualAgent,
)
from util import StreamingMessageMetadata, get_agent_response_item
from state import StateBase


class ConcurrentAgentOrchestrator(OrchestratorBase[ReportabilityContext]):
    """Concurrent orchestration for agents."""

    def __init__(self, state: StateBase[ReportabilityContext]):
        """
        Initialize the ConcurrentAgentOrchestrator with a given state.

        Args:
            state: The state object containing the chat request and other necessary information.
        """
        super().__init__(state)
        self._intent_agent: AgentBase = IntentAgent(state=state)
        self._extraction_agent: RecommendationExtractionAgent = RecommendationExtractionAgent(state=state)
        self._reportability_agent:  ReportabilityManualAgent = ReportabilityManualAgent(state=state)
        self._nureg_agent:  NuregAgent = NuregAgent(state=state)
        self._recommendation_agent: RecommendationAgent = RecommendationAgent(state=state)
        self._extraction_agent: RecommendationExtractionAgent = RecommendationExtractionAgent(state=state)

    async def _execute_nureg_agent(self) -> AsyncIterator[AgentResponseItem[StreamingChatMessageContent]]:
        async for response in self._nureg_agent.invoke_stream():
            yield response

    async def _execute_reportability_agent(self) -> AsyncIterator[AgentResponseItem[StreamingChatMessageContent]]:
        async for response in self._reportability_agent.invoke_stream():
            yield response

    async def _merge_iterators(self,
                               iterators: Collection[AsyncIterator[AgentResponseItem[StreamingChatMessageContent]]]) \
            -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """
        Enable consumption of multiple `AsyncIterator`s from within one `for` loop.

        - Ignore any exceptions.
        - Yield until all iterators have exhausted.
        """

        # turn async generator into coroutine
        async def await_next(iterator: AsyncIterator[AgentResponseItem[StreamingChatMessageContent]]) -> \
                AgentResponseItem[StreamingChatMessageContent]:
            """Turn an awaitable into a coroutine for `create_task`."""
            return await iterator.__anext__()

        # turn coroutine into a task.
        def as_task(iterator: AsyncIterator[AgentResponseItem[StreamingChatMessageContent]]) -> \
                Task[AgentResponseItem[StreamingChatMessageContent]]:
            return create_task(await_next(iterator))

        yield get_agent_response_item(
            f"## Engaging {self._reportability_agent.display_name} {self._nureg_agent.display_name}\n\n",
            self._state.get_state().get_agent_thread(),
            flush=True
        )
        # Create a task for each iterator, keyed on the iterator.
        next_tasks = {iterator: as_task(iterator) for iterator in iterators}

        # As iterators are exhausted, they'll be removed from that mapping.
        # Repeat for as long as any are NOT exhausted.
        while next_tasks:
            # Wait until one of the iterators yields (or errors out).
            # This also returns pending tasks, but we've got those in our mapping.
            done, _ = await wait(next_tasks.values(), return_when=FIRST_COMPLETED)

            for task in done:
                iterator = next(it for it, t in next_tasks.items() if t == task)

                try:
                    abc = task.result()
                    yield abc
                except StopAsyncIteration:
                    del next_tasks[iterator]
                except Exception as e:
                    print(e)
                else:
                    next_tasks[iterator] = as_task(iterator)

    async def invoke_stream(self) -> AsyncIterator[str]:
        """Invoke the orchestration of communication with agents and stream responses.

        Yields:
            str: Streamed response from agent.
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("ConcurrentAgentOrchestrator.invoke_stream"):
            self._intent_agent: AgentBase = IntentAgent(state=self._state)

            async for response in await self._intent_agent.invoke_stream():
                self._intent_agent.track_token_usage(response)
                if response.message.content:
                    yield response

            if self._state.get_state().intent == Intent.INVALID:
                return

            iterators = [self._execute_reportability_agent(), self._execute_nureg_agent()]
            message = ""

            async for response in self._merge_iterators(iterators):
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

            async for response in self._recommendation_agent.invoke_stream():
                yield response

            await self._extraction_agent.invoke()
