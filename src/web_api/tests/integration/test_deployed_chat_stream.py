import os
import requests
import pytest


@pytest.fixture(scope="module")
def endpoint():
    base_url = os.getenv("CHAT_API_BASE_URL", "http://localhost:7071")
    return f"{base_url}/chat/stream"


@pytest.fixture(scope="module")
def headers():
    return {"Content-Type": "application/json"}


@pytest.mark.smoke
@pytest.mark.parametrize("content", [
    "Hello, is the API working?",
    "Why is the sky blue?",
    "What NRC regulations can you help me with?",
    "Is a reactor SCRAM reportable?",
    "Is a turbine trip reportable?"
])
def test_chat_stream_succeeds_with_proper_payload(content, endpoint, headers):
    # Arrange
    data = {
        "messages": [
            {
                "role": "user",
                "content": content,
            }
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

    # Act
    response = requests.post(endpoint, headers=headers, json=data, stream=True)

    # Assert
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    content_found = any(
        'content' in requests.compat.json.loads(line.decode('utf-8')).get('delta', {})
        for line in response.iter_lines() if line
    )
    assert content_found, "No content found in the streaming response"


@pytest.mark.smoke
@pytest.mark.parametrize("messages", [
    [],                                 # no messages
    [{"role": "user"}],                 # no content
    [{"content": "This should fail"}],  # no role
])
def test_chat_stream_fails_on_malformed_payload(messages, endpoint, headers):
    # Arrange
    data = {
        "messages": messages
    }

    # Act
    response = requests.post(endpoint, headers=headers, json=data, stream=True)

    # Assert
    assert response.status_code == 400, f"Expected status 400, got {response.status_code}"
    error_found = any(
        'message' in requests.compat.json.loads(line.decode('utf-8')).get('error', {})
        for line in response.iter_lines() if line
    )
    assert error_found, "No error found in the streaming response"
