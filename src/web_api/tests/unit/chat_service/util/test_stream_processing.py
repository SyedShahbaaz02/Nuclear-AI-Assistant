import pytest
from pydantic import BaseModel
from util import stream_processing
from models import (
    AIChatError,
    AIChatErrorResponse,
)


class DummyMessage:
    def __init__(self, content, role):
        self.content = content
        self.role = role


class DummyChunk:
    def __init__(self, content, metadata=None):
        self.content = content
        self.metadata = metadata or {}


class DummyPluginResult:
    def __init__(self, document_id, document_uri):
        self.document_id = document_id
        self.document_uri = document_uri
        self.search_type = "dummy"
        self.search_query = "dummy query"
        self.cited = True

    def to_search_result(self):
        return self


class DummyReportabilityContext:
    def __init__(self, plugin_results=None):
        self.plugin_results = plugin_results or []
        self.all_chunks = ""
        self.recommendations = []
        self.intent = "Test Intent"
        self.user_input_needed = False
        self.token_usage = [{
            "agent_name": "Test Agent",
            "prompt_tokens": 20,
            "completion_tokens": 10
        }]


@pytest.fixture
def DummyMetadata():
    return {
        "flush": False,
        "yield_to_user": True,
        "add_to_chat_history": True,
        "combine_before_adding_to_history": True
    }


@pytest.mark.asyncio
async def test_object_to_json_line_returns_json_string():
    class DummyModel(BaseModel):
        foo: str
    obj = DummyModel(foo="bar")
    result = stream_processing._object_to_json_line(obj)
    assert result == '{"foo":"bar"}\r\n'


@pytest.mark.asyncio
async def test_stream_error_handler_with_exception():
    # Arrange
    exc = Exception("fail")
    # Act
    gen = stream_processing.stream_error_handler(exc)
    # Assert
    result = [x async for x in gen]
    assert len(result) == 1
    assert result[0] == '{"error":{"code":"internal_error","message":"fail"}}\r\n'


@pytest.mark.asyncio
async def test_stream_error_handler_with_error_response():
    # Arrange
    error = AIChatError(code="test", message="msg")
    error_resp = AIChatErrorResponse(error=error)
    # Act
    gen = stream_processing.stream_error_handler(error_resp)
    # Assert
    result = [x async for x in gen]
    assert len(result) == 1
    assert result[0] == '{"error":{"code":"test","message":"msg"}}\r\n'


@pytest.mark.asyncio
async def test_stream_processor_yields_buffered_chunks(monkeypatch, DummyMetadata):
    # Arrange
    monkeypatch.setenv("STREAM_BUFFER_SIZE", "2")
    reportability_context = DummyReportabilityContext()
    chunks = [
        DummyChunk(DummyMessage("a", "user"), metadata=DummyMetadata),
        DummyChunk(DummyMessage("b", "user"), metadata=DummyMetadata),
        DummyChunk(DummyMessage("c", "user"), metadata=DummyMetadata),
    ]

    async def chunk_gen():
        for c in chunks:
            yield c
    # Act
    gen = stream_processing.stream_processor(reportability_context, chunk_gen())
    # Assert
    results = [x async for x in gen]
    assert len(results) == 3
    assert results[0] == (
        '{"delta":{"role":"user","content":"ab","context":null},"session_state":null,"context":null}\r\n'
    )
    assert results[1] == (
        '{"delta":{"role":"user","content":"c","context":null},"session_state":null,"context":null}\r\n'
    )
    assert reportability_context.all_chunks == "abc"


@pytest.mark.asyncio
async def test_stream_processor_skips_empty_content(monkeypatch, DummyMetadata):
    # Arrange
    monkeypatch.setenv("STREAM_BUFFER_SIZE", "2")
    reportability_context = DummyReportabilityContext()
    chunks = [
        DummyChunk(DummyMessage("", "user"), metadata=DummyMetadata),
        DummyChunk(DummyMessage("x", "user"), metadata=DummyMetadata),
    ]

    async def chunk_gen():
        for c in chunks:
            yield c
    # Act
    gen = stream_processing.stream_processor(reportability_context, chunk_gen())
    # Assert
    results = [x async for x in gen]
    assert len(results) == 2
    assert results[0] == (
        '{"delta":{"role":"user","content":"x","context":null},"session_state":null,"context":null}\r\n'
    )


@pytest.mark.asyncio
async def test_stream_processor_yields_context(monkeypatch, DummyMetadata):
    # Arrange
    monkeypatch.setenv("STREAM_BUFFER_SIZE", "2")
    plugin_results = [DummyPluginResult("doc1", "uri1"), DummyPluginResult("doc2", "uri2")]
    reportability_context = DummyReportabilityContext(plugin_results=plugin_results)
    chunks = [
        DummyChunk(DummyMessage("foo", "assistant"), metadata=DummyMetadata),
        DummyChunk(DummyMessage("bar", "assistant"), metadata=DummyMetadata),
    ]

    async def chunk_gen():
        for c in chunks:
            yield c
    # Act
    gen = stream_processing.stream_processor(reportability_context, chunk_gen())
    # Assert
    results = [x async for x in gen]
    assert len(results) == 2
    assert results[0] == (
        '{"delta":{"role":"assistant","content":"foobar","context":null},"session_state":null,"context":null}\r\n'
    )
    assert results[1] == (
        '{"delta":{"role":"assistant","content":null,"context":null},"session_state":null,"context":'
        '{"documents":[{"id":"doc1","url":"uri1","search_type":"dummy","search_query":"dummy query",'
        '"cited":true},{"id":"doc2","url":"uri2","search_type":"dummy","search_query":"dummy query",'
        '"cited":true}],"recommendations":[],"intent":"Test Intent","user_input_needed":false,'
        '"token_usage":[{"agent_name":"Test Agent","prompt_tokens":20,"completion_tokens":10}]}}\r\n'
    )
