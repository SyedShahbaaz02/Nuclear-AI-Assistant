import chainlit as cl
import logging
import uuid

from dotenv import load_dotenv

from models import (
    AIChatRequest,
    AIChatMessage,
    AIChatRole
)
from orchestrators import ConcurrentAgentOrchestrator as AgentOrchestator
from state import MemoryState, StateBase


# Create a custom handler that will capture logs
class CapturingHandler(logging.Handler):
    """
    Custom logging handler to capture logs in memory for later retrieval.
    This handler stores log messages in a list, which can be accessed later for display or processing.
    """
    def __init__(self):
        super().__init__()
        self.logs = []

    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)

    def get_logs(self):
        return self.logs

    def clear(self):
        self.logs = []


# Setup capturing handler
capturing_handler = CapturingHandler()
capturing_handler.setFormatter(
    logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
)

# Add this handler to the semantic kernel loggers
sk_logger = logging.getLogger("semantic_kernel")
sk_logger.setLevel(logging.DEBUG)
sk_logger.addHandler(capturing_handler)

load_dotenv()


@cl.on_chat_start
async def on_chat_start():
    """
    Asynchronously initializes the chat session by creating a new process kernel and setting up the user session.
    Stores the kernel and an empty chat history in the user session for later use.
    """
    welcome_message = AIChatMessage(content="Welcome to the chat!", role=AIChatRole.ASSISTANT)
    request: AIChatRequest = AIChatRequest(messages=[welcome_message], session_state=uuid.uuid4())
    state: StateBase = MemoryState(chat_request=request)
    orchestrator = AgentOrchestator(state=state)

    cl.user_session.set("orchestrator", orchestrator)
    cl.user_session.set("chat_history", state.get_state().message_history)


@cl.on_message
async def on_message(message: cl.Message):
    """
    Processes an incoming user message, updates chat history, and streams the assistant's response.

    Retrieves the current kernel and chat history from the user session, adds the new user message,
    and executes the reportability process asynchronously. Streams the assistant's response back to the user
    in real time and updates the chat history with the assistant's reply.

    Args:
        message (cl.Message): The incoming chat message from the user.

    Raises:
        Exception: Raised automatically by Python if encountered during message processing.
    """
    capturing_handler.clear()

    orchestrator = cl.user_session.get("orchestrator")
    chat_history = cl.user_session.get("chat_history")
    chat_history.add_user_message(message.content)
    # Show thinking indicator while processing
    async with cl.Step(name="Thinking...") as step:
        results = orchestrator.invoke_stream()
        answer = cl.Message(content="")

        async for chunk in results:
            message = chunk.content
            if message.content == '':
                continue

            await answer.stream_token(message.content)

        await handle_logs(step)
        chat_history.add_assistant_message(answer.content)
    await answer.send()


async def handle_logs(step):
    """
    Handles the logs captured by the custom logging handler and sends them to the chat.

    Returns:
        None
    """
    thought_process = capturing_handler.get_logs()

    # Create a formatted thought process for display
    thought_elements = []

    thought_process = capturing_handler.get_logs()

    # Create a formatted thought process for display
    thought_elements = []

    # Extract plugin usage from logs if any
    plugin_logs = [log for log in thought_process if "plugin" in log.lower() or "function" in log.lower()]
    if plugin_logs:
        thought_elements.append(
            cl.Text(name="Plugin Activity", content="\n".join(plugin_logs))
        )

    # Add raw logs for full visibility
    thought_elements.append(
        cl.Text(name="Full Semantic Kernel Logs", content="\n".join(thought_process))
    )

    # Update the step to show thinking process
    step.elements = thought_elements
    await step.update()

if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)
