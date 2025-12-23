import pytest
import json
from .utils import assert_missing_required_fields_raises
from models import (
    AIChatRole,
    AIChatMessage,
    AIChatMessageDelta,
    AIChatCompletionDelta,
    AIChatRequest,
)


def test_aichatrequest_messages_validator_raises():
    # Act & Assert
    with pytest.raises(ValueError, match="messages must not be empty"):
        AIChatRequest(messages=[])


def test_aichatrequest_model_validation():
    # Arrange
    manual_data = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ],
        "context": {
            "user": {
                "id": "user-id-anon-001",
                "displayName": "User Anonymous",
                "upn": "user.anon@example.com",
                "employeeId": "anon-001",
                "mail": "user.anon@example.com"
            },
            "facility": ["ABC", "123"],
            "sourceSystem": "Ask Licensing"
        },
        "sessionState": "fake-session-1234-5678-9012-abcdef"
    }
    # Act / Assert
    AIChatRequest.model_validate_json(json.dumps(manual_data))  # Should not raise an exception
    assert_missing_required_fields_raises(AIChatRequest, manual_data)


def test_aichatmessage_model_validation():
    # Arrange
    manual_data = {
        "role": AIChatRole.USER,
        "content": "Hello, how can I help you?",
        "files": [
            {
                "name": "file1.txt",
                "data": "File content here",
                "contentType": "text/plain"
            }
        ]
    }
    # Act / Assert
    AIChatMessage.model_validate_json(json.dumps(manual_data))  # Should not raise an exception
    assert_missing_required_fields_raises(AIChatMessage, manual_data)


def test_aichatmessagedelta_model_validation():
    # Arrange
    manual_data = {
        "role": AIChatRole.ASSISTANT,
        "delta": {
            "content": "This is a delta message"
        }
    }
    # Act / Assert
    AIChatMessageDelta.model_validate_json(json.dumps(manual_data))  # Should not raise an exception
    assert_missing_required_fields_raises(AIChatMessageDelta, manual_data)


def test_aichatcompletiondelta_model_validation():
    # Arrange
    manual_data = {
        "delta": {
            "role": AIChatRole.ASSISTANT,
            "delta": {
                "content": "This is a delta message"
            }
        },
        "sessionState": "fake-session-1234-5678-9012-abcdef",
        "context": {
            "user": {
                "id": "user-id-anon-001",
                "displayName": "User Anonymous",
                "upn": "user.anon@example.com",
                "employeeId": "anon-001",
                "mail": "user.anon@example.com"
            },
            "facility": ["ABC", "123"],
            "sourceSystem": "Ask Licensing"
        }
    }
    # Act / Assert
    AIChatCompletionDelta.model_validate_json(json.dumps(manual_data))  # Should not raise an exception
    assert_missing_required_fields_raises(AIChatCompletionDelta, manual_data)
