import pytest
from fastapi import Request
from fastapi.responses import StreamingResponse
from unittest.mock import AsyncMock, MagicMock
from main import stream_openai_text


@pytest.mark.asyncio
async def test_stream_openai_text_success(monkeypatch):
    # Arrange
    mock_body = b'{"messages": [{"role": "user", "content": "Hello"}]}'
    mock_headers = {'content-type': 'application/json'}
    mock_request = MagicMock(spec=Request)
    mock_request.headers = mock_headers
    mock_request.body = AsyncMock(return_value=mock_body)

    mock_orchestrator = MagicMock()
    mock_orchestrator.invoke_stream.return_value = "stream_response"
    monkeypatch.setattr(
        "main.SingleAgentOrchestrator",
        lambda state: mock_orchestrator
    )

    # Act
    response = await stream_openai_text(mock_request)

    # Assert
    assert isinstance(response, StreamingResponse)
    assert response.media_type == "text/event-stream"
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_stream_openai_text_invalid_content_type():
    # Arrange
    mock_headers = {'content-type': 'text/plain'}
    mock_request = MagicMock(spec=Request)
    mock_request.headers = mock_headers

    # Act
    response = await stream_openai_text(mock_request)

    # Assert
    assert isinstance(response, StreamingResponse)
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_stream_openai_text_validation_error(monkeypatch):
    # Arrange
    mock_body = b'invalid json'
    mock_headers = {'content-type': 'application/json'}
    mock_request = MagicMock(spec=Request)
    mock_request.headers = mock_headers
    mock_request.body = AsyncMock(return_value=mock_body)

    # Act
    response = await stream_openai_text(mock_request)

    # Assert
    assert isinstance(response, StreamingResponse)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_stream_openai_text_generic_exception(monkeypatch):
    # Arrange
    mock_body = b'{}'
    mock_headers = {'content-type': 'application/json'}
    mock_request = MagicMock(spec=Request)
    mock_request.headers = mock_headers
    mock_request.body = AsyncMock(return_value=mock_body)

    def raise_exception(_):
        raise Exception("Some error that is not a ValidationError")

    monkeypatch.setattr(
        "main.AIChatRequest.model_validate_json",
        raise_exception
    )

    # Act
    response = await stream_openai_text(mock_request)

    # Assert
    assert isinstance(response, StreamingResponse)
    assert response.status_code == 500
