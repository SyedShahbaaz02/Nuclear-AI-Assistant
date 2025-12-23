import pytest
from semantic_kernel.contents import ChatHistory
from semantic_kernel.agents import ChatHistoryAgentThread
from models import (
    AIChatRequest,
    AIChatRole,
    AIChatMessage,
    ReportabilityContext,
)


@pytest.fixture
def ai_chat_request():
    # Arrange
    messages = [
        AIChatMessage(role=AIChatRole.USER, content="Hello"),
        AIChatMessage(role=AIChatRole.ASSISTANT, content="Hi, how can I help?"),
    ]
    return AIChatRequest(messages=messages, session_state="session123")


def test_reportability_context_initialization(ai_chat_request):
    # Act
    context = ReportabilityContext(chat_request=ai_chat_request)
    # Assert
    assert context.current_input_index == 0
    assert isinstance(context.message_history, ChatHistory)
    assert context.chat_request == ai_chat_request
    assert context.all_chunks == ""
    assert len(context.message_history.messages) == 2


def test_reportability_context_transform_chat_request(ai_chat_request):
    # Arrange
    context = ReportabilityContext(chat_request=ai_chat_request)
    # Act
    user_msg = context.message_history.messages[0]
    assistant_msg = context.message_history.messages[1]
    # Assert
    assert user_msg.role == "user"
    assert user_msg.content == "Hello"
    assert assistant_msg.role == "assistant"
    assert assistant_msg.content == "Hi, how can I help?"


def test_reportability_context_get_agent_thread(ai_chat_request):
    # Arrange
    context = ReportabilityContext(chat_request=ai_chat_request)
    # Act
    agent_thread = context.get_agent_thread()
    # Assert
    assert isinstance(agent_thread, ChatHistoryAgentThread)
    assert agent_thread.id == "session123"
