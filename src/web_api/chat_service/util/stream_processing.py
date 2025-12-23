import logging
import os

from enum import Enum
from pydantic import BaseModel
from semantic_kernel.agents import ChatHistoryAgentThread
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.contents import StreamingChatMessageContent
from typing import Any, AsyncIterator

from constants import EnvironmentVariables, ChatServiceConstants
from models import (
    AIChatError,
    AIChatErrorResponse,
    AIChatCompletionDelta,
    AIChatMessageDelta,
    ReportabilityContext,
)


logger = logging.getLogger(ChatServiceConstants.LOGGER_NAME.value + __name__)


class StreamingMessageMetadata(Enum):
    """
    Enum for metadata keys used in streaming chat messages to control processing behavior.
    These keys can be used to customize how messages are handled during streaming.
    """
    FLUSH = "flush"
    YIELD_TO_USER = "yield_to_user"
    ADD_TO_CHAT_HISTORY = "add_to_chat_history"
    COMBINE_BEFORE_ADDING_TO_HISTORY = "combine_before_adding_to_history"


def _object_to_json_line(obj: BaseModel):
    return f"{obj.model_dump_json()}\r\n"


def get_agent_response_item(
        message: str,
        thread: ChatHistoryAgentThread,
        **kwargs: Any) -> AgentResponseItem[StreamingChatMessageContent]:
    """
    Creates an AgentResponseItem containing a streaming chat message for the assistant, with customizable metadata.

    Args:
        message (str): The message content to be sent by the assistant.
        thread (ChatHistoryAgentThread): The chat thread to which this message belongs.
        **kwargs (Any): Additional metadata options to control message processing. Supported keys include:
            - StreamingMessageMetadata.FLUSH (bool, optional): Whether to flush the message immediately. Defaults to
              False.
            - StreamingMessageMetadata.YIELD_TO_USER (bool, optional): Whether to yield the message to the user.
              Defaults to True. Some responses from agents are intended for other agents, not the user.
            - StreamingMessageMetadata.ADD_TO_CHAT_HISTORY (bool, optional): Whether to add the message to chat history.
              Defaults to True.
            - StreamingMessageMetadata.COMBINE_BEFORE_ADDING_TO_HISTORY (bool, optional): Whether to combine the message
              with previous ones before adding to history. Defaults to True.
            Additional keyword arguments are included in the metadata dictionary.

    Returns:
        AgentResponseItem[StreamingChatMessageContent]: An agent response item containing the streaming chat message and
        associated metadata.
    """
    metadata: dict[str, Any] = dict(kwargs)
    # Set default values for meta data
    metadata[StreamingMessageMetadata.FLUSH.value] = metadata.pop(StreamingMessageMetadata.FLUSH.value, False)
    metadata[StreamingMessageMetadata.YIELD_TO_USER.value] = metadata.pop(
        StreamingMessageMetadata.YIELD_TO_USER.value, True
    )
    metadata[StreamingMessageMetadata.ADD_TO_CHAT_HISTORY.value] = metadata.pop(
        StreamingMessageMetadata.ADD_TO_CHAT_HISTORY.value, True
    )
    metadata[StreamingMessageMetadata.COMBINE_BEFORE_ADDING_TO_HISTORY.value] = (
        metadata.pop(StreamingMessageMetadata.COMBINE_BEFORE_ADDING_TO_HISTORY.value, True)
    )
    return AgentResponseItem(
        message=StreamingChatMessageContent(
            content=message,
            choice_index=0,
            items=[],
            role="assistant",
            metadata=metadata,
        ),
        thread=thread,
    )


async def stream_error_handler(e: Exception | AIChatErrorResponse):
    """ Handles errors that occur during streaming processing."""
    if isinstance(e, AIChatErrorResponse):
        # If it's already an AIChatErrorResponse, convert it to a JSON line.
        yield _object_to_json_line(e)
        return
    error = AIChatError(code="internal_error", message=str(e))
    yield _object_to_json_line(AIChatErrorResponse(error=error))


async def stream_processor(reportability_context: ReportabilityContext, streaming_response: AsyncIterator[Any]):
    """ Processes streaming chat messages and yields them as JSON lines."""
    def _create_result(buffer, role):
        if buffer and len(buffer) > 0:
            response_chunk = AIChatCompletionDelta(
                delta=AIChatMessageDelta(
                    content="".join(buffer),
                    role=role,
                ),
            )
            return _object_to_json_line(response_chunk)
        return None

    def _create_context(role, reportability_context: ReportabilityContext):
        documents = _get_referenced_documents(reportability_context)

        context = {
            "documents": documents
        }
        if reportability_context.include_eval_content:
            context.update({
                "recommendations": reportability_context.recommendations,
                "intent": reportability_context.intent,
                "user_input_needed": reportability_context.user_input_needed,
                "token_usage": reportability_context.token_usage,
            })

        return AIChatCompletionDelta(
            delta=AIChatMessageDelta(
                role=role,
            ),
            content="",
            context=context
        )

    def _get_referenced_documents(reportability_context: ReportabilityContext) -> list[dict[str, str]]:
        documents = []

        for result in reportability_context.plugin_results:
            if result.cited or reportability_context.include_eval_content:
                search_result = result.to_search_result()
                document = {
                    "id": search_result.document_id,
                    "url": search_result.document_uri,
                    "section": result.get_display_value()
                }
                if reportability_context.include_eval_content:
                    document.update({
                        "search_type": search_result.search_type,
                        "search_query": search_result.search_query,
                        "cited": search_result.cited
                    })
                documents.append(document)

        return documents

    buffer = []
    role = None
    buffer_size = int(os.getenv(EnvironmentVariables.STREAM_BUFFER_SIZE.value, 5))
    async for chunk in streaming_response:
        message = chunk.content
        flush = chunk.metadata.get(StreamingMessageMetadata.FLUSH.value, False)
        if message.content and message.content == '':
            continue
        buffer.append(message.content)
        reportability_context.all_chunks += message.content
        role = message.role  # Use the last role seen in the batch, this should always be the same anyway
        if len(buffer) == buffer_size or flush:
            result = _create_result(buffer, role)
            if result:
                yield result
            buffer = []
    # Yield any remaining content in the buffer
    result = _create_result(buffer, role)
    if result:
        yield result

    context = _create_context(role, reportability_context)
    if context:
        yield _object_to_json_line(context)

    logger.debug("All chunks processed: %s", reportability_context.all_chunks)
