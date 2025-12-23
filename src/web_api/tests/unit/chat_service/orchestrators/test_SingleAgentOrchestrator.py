import pytest
from unittest.mock import AsyncMock, patch
from orchestrators import SingleAgentOrchestrator
from models import ReportabilityContext  # noqa: E402
from agents import NRCRecommendationAgent  # noqa: E402


@pytest.mark.asyncio
async def test_invoke_stream_yields_agent_responses():
    # Arrange
    mock_state = ReportabilityContext()
    orchestrator = SingleAgentOrchestrator(state=mock_state)
    mock_agent = AsyncMock(spec=NRCRecommendationAgent)

    async def async_gen():
        for r in ["response1", "response2"]:
            yield r
    mock_agent.invoke_stream.return_value = async_gen()

    with patch("orchestrators.SingleAgentOrchestrator.NRCRecommendationAgent", return_value=mock_agent):
        # Act
        responses = []
        async for r in orchestrator.invoke_stream():
            responses.append(r)

        # Assert
        assert responses == ["response1", "response2"]


@pytest.mark.asyncio
async def test_invoke_stream_tracing_called():
    # Arrange
    mock_state = ReportabilityContext()
    orchestrator = SingleAgentOrchestrator(state=mock_state)
    mock_agent = AsyncMock(spec=NRCRecommendationAgent)

    async def async_gen():
        yield "response"
    mock_agent.invoke_stream.return_value = async_gen()
    from unittest.mock import MagicMock

    mock_tracer = MagicMock()
    mock_span_cm = MagicMock()
    mock_tracer.start_as_current_span.return_value = mock_span_cm
    mock_span_cm.__enter__.return_value = MagicMock()
    mock_span_cm.__exit__.return_value = None

    with patch("orchestrators.SingleAgentOrchestrator.NRCRecommendationAgent", return_value=mock_agent), \
         patch("orchestrators.SingleAgentOrchestrator.trace.get_tracer", return_value=mock_tracer):
        # Act
        responses = []
        async for r in orchestrator.invoke_stream():
            responses.append(r)

        # Assert
        mock_tracer.start_as_current_span.assert_called_with("SingleAgentOrchestrator.invoke_stream")
        assert responses == ["response"]


@pytest.mark.asyncio
async def test_invoke_stream_handles_empty_agent_response():
    # Arrange
    mock_state = ReportabilityContext()
    orchestrator = SingleAgentOrchestrator(state=mock_state)
    mock_agent = AsyncMock(spec=NRCRecommendationAgent)

    async def async_gen():
        if False:
            yield
    mock_agent.invoke_stream.return_value = async_gen()

    with patch("orchestrators.SingleAgentOrchestrator.NRCRecommendationAgent", return_value=mock_agent):
        # Act
        responses = []
        async for r in orchestrator.invoke_stream():
            responses.append(r)

        # Assert
        assert responses == []
