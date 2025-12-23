import pytest
import json
from .utils import assert_missing_required_fields_raises
from models import (
    Example,
    NUREGSection32,
    RequiredNotification,
    RequiredReport,
    ReportabilityManual,
    SearchPluginResult
)  # noqa: E402


class DummyReportabilityServices:
    @staticmethod
    def get_sas_token(account_name: str, container_name: str, blob_name: str) -> str:
        """
        Returns a dummy SAS token for testing purposes.
        """
        return "dummy_sas_token"


@pytest.fixture(autouse=True)
def patch_reportability_services(monkeypatch):
    import models.search_models as search_models  # noqa: E402
    monkeypatch.setattr(search_models, "ReportabilityServices", DummyReportabilityServices)


@pytest.fixture
def reportability_manual():
    return ReportabilityManual(
        id="man1",
        sectionName="Section A",
        references=["ref1", "ref2"],
        referenceContent="Reference content",
        discussion="Manual discussion",
        requiredNotifications=[RequiredNotification(timeLimit="1 hour", notification="Notify NRC")],
        requiredWrittenReports=[RequiredReport(timeLimit="24 hours", notification="Submit written report")],
        storageAccountName="acc",
        containerName="cont",
        blobName="manual.pdf",
        pageNumber=42,
        search_query="Test Search"
    )


@pytest.fixture
def nureg_section32():
    return NUREGSection32(
        id="sec2",
        section="3.2",
        lxxii=["a"],
        lxxiii=["b"],
        description="desc",
        discussion="disc",
        storageAccountName="acc",
        containerName="cont",
        blobName="blob.pdf",
        pageNumber=5,
        examples=[Example(title="ex1", description="desc1")],
        search_query="Test Search"
    )


def test_nureg_section32_to_agent_string(nureg_section32):
    # Arrange
    section = nureg_section32
    # Act
    agent_str = section.to_agent_string()
    # Assert
    assert "Section: 3.2" in agent_str
    assert "10 CFR 50.72: a" in agent_str
    assert "Examples:" in agent_str


def test_reportability_manual_to_agent_string(reportability_manual):
    # Arrange
    manual = reportability_manual
    # Act
    agent_str = manual.to_agent_string()
    # Assert
    assert "Section Name: Section A" in agent_str
    assert "Required Notifications:" in agent_str
    assert "Required Reports:" in agent_str


def test_reportability_manual_to_search_result(reportability_manual):
    # Arrange
    manual = reportability_manual
    # Act
    search_result = manual.to_search_result()
    # Assert
    assert isinstance(search_result, SearchPluginResult)
    assert search_result.search_type == "reportabilitymanual"
    assert search_result.document_id == "man1"
    assert search_result.document_uri == \
        "https://acc.blob.core.usgovcloudapi.net/cont/manual.pdf?dummy_sas_token#page=42"
    assert search_result.search_query == "Test Search"


def test_reportability_manual_model_validation():
    # Arrange
    manual_data = {
        "id": "man1",
        "sectionName": "Section A",
        "references": ["ref1", "ref2"],
        "referenceContent": "Reference content",
        "discussion": "Manual discussion",
        "requiredNotifications": [
            {"timeLimit": "1 hour", "notification": "Notify NRC"}
        ],
        "requiredWrittenReports": [
            {"timeLimit": "24 hours", "notification": "Submit written report"}
        ],
        "storageAccountName": "acc",
        "containerName": "cont",
        "blobName": "manual.pdf",
        "pageNumber": 42
    }
    # Act / Assert
    ReportabilityManual.model_validate_json(json.dumps(manual_data))  # Should not raise an exception
    assert_missing_required_fields_raises(ReportabilityManual, manual_data)


def test_nureg_section32_model_validation():
    # Arrange
    nureg_data = {
        "id": "sec1",
        "section": "3.2",
        "lxxii": ["a", "b"],
        "lxxiii": ["c"],
        "description": "desc",
        "discussion": "disc",
        "storageAccountName": "acc",
        "containerName": "cont",
        "blobName": "blob.pdf",
        "pageNumber": 10,
        "examples": [
            {"title": "ex1", "description": "desc1"}
        ]
    }
    # Act / Assert
    NUREGSection32.model_validate_json(json.dumps(nureg_data))  # Should not raise an exception
    assert_missing_required_fields_raises(NUREGSection32, nureg_data)
