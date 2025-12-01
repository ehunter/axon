"""Tests for the export service."""

import csv
import json
from io import StringIO

import pytest

from axon.agent.tools import SampleSelection, SelectedSample
from axon.export import ExportService, ExportFormat
from axon.export.service import ExportMetadata, ExportResult


@pytest.fixture
def sample_selection():
    """Create a sample selection for testing."""
    selection = SampleSelection()
    
    # Add cases
    selection.add_case(SelectedSample(
        id="case-1",
        external_id="6662",
        diagnosis="Alzheimer's disease",
        age=75,
        sex="female",
        rin=8.9,
        pmi=8.8,
        brain_region="Frontal cortex",
        source_bank="NIH Sepulveda",
        braak_stage="NFT Stage V",
        copathologies="None recorded",
    ))
    selection.add_case(SelectedSample(
        id="case-2",
        external_id="6713",
        diagnosis="Alzheimer's disease",
        age=81,
        sex="male",
        rin=8.2,
        pmi=23.6,
        brain_region="Frontal cortex",
        source_bank="NIH Miami",
        braak_stage="NFT Stage VI",
        copathologies="CAA noted",
    ))
    
    # Add controls
    selection.add_control(SelectedSample(
        id="ctrl-1",
        external_id="6922",
        diagnosis="Control",
        age=73,
        sex="female",
        rin=9.1,
        pmi=25.9,
        brain_region="Frontal cortex",
        source_bank="NIH Pittsburgh",
        braak_stage=None,
        copathologies="None recorded",
    ))
    
    return selection


@pytest.fixture
def export_metadata():
    """Create export metadata for testing."""
    return ExportMetadata(
        researcher_name="Dr. Test",
        research_purpose="Testing export",
        tissue_use="RNA-seq",
        selection_criteria={
            "diagnosis": "Alzheimer's disease",
            "age_range": "65+",
        },
        notes="Test notes",
    )


class TestExportService:
    """Tests for ExportService."""
    
    def test_export_csv(self, sample_selection, export_metadata):
        """Test CSV export."""
        service = ExportService(sample_selection, export_metadata)
        result = service.export(ExportFormat.CSV)
        
        assert result.format == ExportFormat.CSV
        assert result.sample_count == 3
        assert result.filename.endswith(".csv")
        
        # Parse and verify CSV content
        reader = csv.DictReader(StringIO(result.content))
        rows = list(reader)
        
        assert len(rows) == 3
        
        # Check first case
        assert rows[0]["Group"] == "Case"
        assert rows[0]["Sample ID"] == "6662"
        assert rows[0]["Repository"] == "NIH Sepulveda"
        assert rows[0]["Diagnosis"] == "Alzheimer's disease"
        
        # Check control
        assert rows[2]["Group"] == "Control"
        assert rows[2]["Sample ID"] == "6922"
    
    def test_export_json(self, sample_selection, export_metadata):
        """Test JSON export."""
        service = ExportService(sample_selection, export_metadata)
        result = service.export(ExportFormat.JSON)
        
        assert result.format == ExportFormat.JSON
        assert result.sample_count == 3
        
        # Parse and verify JSON content
        data = json.loads(result.content)
        
        assert "metadata" in data
        assert "cases" in data
        assert "controls" in data
        
        assert data["metadata"]["researcher_name"] == "Dr. Test"
        assert len(data["cases"]) == 2
        assert len(data["controls"]) == 1
        
        # Check case data
        assert data["cases"][0]["external_id"] == "6662"
        assert data["cases"][0]["rin"] == 8.9
    
    def test_export_text(self, sample_selection, export_metadata):
        """Test text export."""
        service = ExportService(sample_selection, export_metadata)
        result = service.export(ExportFormat.TEXT)
        
        assert result.format == ExportFormat.TEXT
        assert result.sample_count == 3
        
        # Verify text content
        content = result.content
        
        assert "BRAIN SAMPLE SELECTION SUMMARY" in content
        assert "Dr. Test" not in content  # researcher_name is optional in text
        assert "Testing export" in content
        assert "RNA-seq" in content
        assert "6662" in content
        assert "NIH Sepulveda" in content
        assert "CASE SAMPLES" in content
        assert "CONTROL SAMPLES" in content
    
    def test_empty_selection_export(self):
        """Test export with empty selection."""
        selection = SampleSelection()
        service = ExportService(selection)
        result = service.export(ExportFormat.CSV)
        
        assert result.sample_count == 0
        
        # CSV should still have header
        reader = csv.DictReader(StringIO(result.content))
        rows = list(reader)
        assert len(rows) == 0
    
    def test_export_without_metadata(self, sample_selection):
        """Test export without metadata."""
        service = ExportService(sample_selection)
        result = service.export(ExportFormat.JSON)
        
        data = json.loads(result.content)
        assert data["metadata"]["researcher_name"] is None
        assert data["metadata"]["research_purpose"] is None


class TestExportMetadata:
    """Tests for ExportMetadata."""
    
    def test_default_metadata(self):
        """Test default metadata values."""
        metadata = ExportMetadata()
        
        assert metadata.researcher_name is None
        assert metadata.research_purpose is None
        assert metadata.tissue_use is None
        assert metadata.selection_criteria == {}
        assert metadata.notes is None
        assert metadata.exported_at is not None


class TestAdminEmail:
    """Tests for admin email generation."""
    
    def test_generate_admin_email(self, sample_selection, export_metadata):
        """Test admin email generation."""
        service = ExportService(sample_selection, export_metadata)
        email = service.generate_admin_email()
        
        assert "Subject: Brain Sample Request" in email
        assert "Dear Brain Bank Administrator" in email
        assert "Dr. Test" in email
        assert "Testing export" in email
        assert "RNA-seq" in email
        assert "Total Samples Requested: 3" in email
        assert "Cases: 2" in email
        assert "Controls: 1" in email
        
        # Check samples by repository
        assert "NIH Sepulveda" in email
        assert "NIH Miami" in email
        assert "NIH Pittsburgh" in email
        assert "6662" in email
    
    def test_admin_email_groups_by_repository(self, sample_selection, export_metadata):
        """Test that admin email groups samples by repository."""
        service = ExportService(sample_selection, export_metadata)
        email = service.generate_admin_email()
        
        # Verify repository grouping exists
        assert "SAMPLES BY REPOSITORY" in email
        
        # Each repository should appear
        repos = ["NIH Sepulveda", "NIH Miami", "NIH Pittsburgh"]
        for repo in repos:
            assert repo in email


class TestSelectedSampleRepository:
    """Tests for SelectedSample repository property."""
    
    def test_repository_alias(self):
        """Test that repository is an alias for source_bank."""
        sample = SelectedSample(
            id="test-1",
            external_id="TEST123",
            diagnosis="Test",
            age=70,
            sex="male",
            rin=7.5,
            pmi=12.0,
            brain_region="Cortex",
            source_bank="Test Bank",
            braak_stage=None,
            copathologies=None,
        )
        
        assert sample.repository == "Test Bank"
        assert sample.repository == sample.source_bank

