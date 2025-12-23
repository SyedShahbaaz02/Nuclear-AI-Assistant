import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from azure.search.documents.aio import SearchClient

from functions import SearchPluginsBase  # noqa: E402
from models import ReportabilityContext  # noqa: E402


class DummyConfig:
    def __init__(self):
        self.index_name = "nureg"
        self.index_name_setting = "NUREG_INDEX"
        self.search_type = MagicMock()
        self.search_fields = ["field1"]
        self.select_fields = ["field1"]
        self.top = 5
        self.vector_fields = ["vector"]
        self.k_nearest_neighbors = 3
        self.threshold = 0.5


def get_mock_search_config():
    return {"nureg": DummyConfig(), "reportability_manual": DummyConfig()}


@pytest.fixture
def mock_context():
    return ReportabilityContext()


@pytest.fixture
def mock_search_config():
    return get_mock_search_config()


@patch.object(SearchPluginsBase, "_load_configuration")
@pytest.mark.asyncio
async def test_init_loads_config(mock_load_config, mock_context):
    # Arrange
    dummy_config = {"nureg": MagicMock()}
    mock_load_config.return_value = dummy_config
    # Act
    plugin = SearchPluginsBase(mock_context)
    # Assert
    assert plugin._search_configurations == dummy_config
    assert plugin._reportability_context == mock_context


@patch("os.path.exists", return_value=False)
def test_load_configuration_file_not_found(mock_exists):
    plugin = SearchPluginsBase.__new__(SearchPluginsBase)
    with pytest.raises(FileNotFoundError):
        plugin._load_configuration()


@pytest.mark.asyncio
async def test_search_results_fulltext(mock_search_config):
    plugin = SearchPluginsBase.__new__(SearchPluginsBase)
    search_client = AsyncMock(spec=SearchClient)
    search_client.search = AsyncMock(return_value="fulltext_results")
    config = mock_search_config["nureg"]
    config.search_type = MagicMock()
    config.search_type.FullText = "FullText"
    config.search_type = "FullText"
    result = await plugin._search_results(search_client, config, "query")
    assert result == "fulltext_results"
    search_client.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_results_vector(mock_search_config):
    plugin = SearchPluginsBase.__new__(SearchPluginsBase)
    search_client = AsyncMock(spec=SearchClient)
    search_client.search = AsyncMock(return_value="vector_results")
    config = mock_search_config["nureg"]
    config.search_type = MagicMock()
    config.search_type.Vector = "Vector"
    config.search_type = "Vector"
    result = await plugin._search_results(search_client, config, "query")
    assert result == "vector_results"
    search_client.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_results_hybrid(mock_search_config):
    plugin = SearchPluginsBase.__new__(SearchPluginsBase)
    search_client = AsyncMock(spec=SearchClient)
    search_client.search = AsyncMock(return_value="hybrid_results")
    config = mock_search_config["nureg"]
    config.search_type = MagicMock()
    config.search_type.Hybrid = "Hybrid"
    config.search_type = "Hybrid"
    result = await plugin._search_results(search_client, config, "query")
    assert result == "hybrid_results"
    search_client.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_results_invalid_type(mock_search_config):
    plugin = SearchPluginsBase.__new__(SearchPluginsBase)
    search_client = AsyncMock(spec=SearchClient)
    config = mock_search_config["nureg"]
    config.search_type = "Invalid"
    with pytest.raises(ValueError):
        await plugin._search_results(search_client, config, "query")


def test_process_results_adds_new_results(mock_context):
    plugin = SearchPluginsBase(mock_context, {})
    dummy_result = MagicMock()
    dummy_result.id = "doc1"
    dummy_result.to_search_result.return_value = MagicMock(document_id="doc1")
    results = plugin._process_results([dummy_result], "query")
    assert results == [dummy_result]
    assert len(mock_context.plugin_results) == 1


def test_process_results_skips_existing(mock_context):
    plugin = SearchPluginsBase(mock_context, {})
    dummy_result = MagicMock()
    dummy_result.id = "doc1"
    dummy_result.to_search_result.return_value = MagicMock(document_id="doc1")
    mock_context.plugin_results.append(MagicMock(document_id="doc1"))
    results = plugin._process_results([dummy_result], "query")
    assert results == []


@pytest.mark.asyncio
async def test_convert_results_filters_by_threshold():
    plugin = SearchPluginsBase.__new__(SearchPluginsBase)
    dummy_model = MagicMock()
    dummy_model.model_validate = MagicMock(return_value="model_instance")
    dummy_result = {"@search.score": 0.8}
    dummy_result2 = {"@search.score": 0.3}
    results = [dummy_result, dummy_result2]

    async def async_gen():
        for r in results:
            yield r
    result = await plugin._convert_results(0.5, async_gen(), "query", dummy_model)
    assert result == ["model_instance"]
    dummy_model.model_validate.assert_called_once_with(dummy_result)

    if __name__ == "__main__":
        pytest.main([__file__])
