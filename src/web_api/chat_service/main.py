import logging
import os
import sys

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

sys.path.append(os.path.dirname(__file__))  # Ensures local imports work

from constants import ChatServiceConstants, EnvironmentVariables  # noqa: E402
from models import (  # noqa: E402
    AIChatError,
    AIChatErrorResponse,
    AIChatRequest
)
from orchestrators import SingleAgentOrchestrator, SequentialAgentOrchestrator, \
                          ConcurrentAgentOrchestrator  # noqa: E402
from state import MemoryState, StateBase  # noqa: E402
from util import stream_processor, stream_error_handler  # noqa: E402


# ASGI Application
stream = APIRouter(prefix="/stream", tags=["stream"])
logger = logging.getLogger(ChatServiceConstants.LOGGER_NAME.value + __name__)


# HTTP streaming Endpoint
@stream.route(path="/stream", methods=["POST"])
async def stream_openai_text(
    req: Request
) -> StreamingResponse:
    """
    Handles streaming OpenAI text responses via an HTTP request.

    Args:
        req (Request): The incoming HTTP request object, expected to have a JSON body with chat messages.

    Returns:
        StreamingResponse: An asynchronous streaming response with the generated text, using the "text/event-stream"
        media type.

    Raises:
        StreamingResponse: Returns a streaming error response with status code 400 if validation fails, or 500 for
        other exceptions.
    """
    try:
        logger.info("Received streaming request for OpenAI text processing.")
        content_type = req.headers['content-type']
        if content_type.startswith("application/json"):
            chat_request_data = await req.body()
            chat_request = AIChatRequest.model_validate_json(chat_request_data)
        else:
            raise Exception(
                "Unsupported Media Type: Only 'application/json' is supported.")

        orchestrationType = req.query_params.get("orchestrationType")
        if orchestrationType is None:
            orchestrationType = os.environ.get(EnvironmentVariables.ORCHESTRATION_TYPE.value, "concurrent")

        state: StateBase = MemoryState(chat_request=chat_request)
        # make sure we capture whether the eval content should be included in the final delta context object
        eval_content = req.query_params.get("evaluation", "False")
        state.get_state().include_eval_content = eval_content.lower() == "true"

        orchestrator = _get_orchestrator(orchestrationType, state)

        response = orchestrator.invoke_stream()

        return StreamingResponse(
            stream_processor(
                streaming_response=response, reportability_context=state.get_state()), media_type="text/event-stream")
    except (ValidationError, ValueError) as ve:
        logger.exception(f"Validation error: {ve}", exc_info=ve)
        error_response = AIChatErrorResponse(error=AIChatError(code="invalid_request_error", message=str(ve)))
        return StreamingResponse(stream_error_handler(error_response), media_type="text/event-stream", status_code=400)
    except Exception as e:
        logger.exception(f"Error processing request: {e}", exc_info=e)
        return StreamingResponse(stream_error_handler(e), media_type="text/event-stream", status_code=500)


def _get_orchestrator(orchestrationType, state):
    match orchestrationType:
        case "sequential":
            orchestrator = SequentialAgentOrchestrator(state=state)
        case "single":
            orchestrator = SingleAgentOrchestrator(state=state)
        case "concurrent":
            orchestrator = ConcurrentAgentOrchestrator(state=state)
        case _:
            logger.warning(
                    f"Unknown orchestration type: {orchestrationType}. Defaulting to SingleAgentOrchestrator.")
            orchestrator = SingleAgentOrchestrator(state=state)
    return orchestrator
