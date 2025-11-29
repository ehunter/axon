"""Tests for NIH NeuroBioBank CSV adapter.

These tests define the expected behavior of the NIH data importer.
Following TDD: tests written first, then implementation.
"""

import pytest
from decimal import Decimal

from axon.ingest.adapters.nih import NIHAdapter, NIHRecord


class TestNIHRecordParsing:
    """Tests for parsing individual CSV rows into NIHRecord."""

    def test_parse_basic_record(self):
        """Should parse a basic CSV row into NIHRecord."""
        row = {
            "Subject ID": "NIH1000",
            "Repository": "Miami",
            "Subject Age": "37",
            "Subject Sex": "Male",
            "Race": "White",
            "Ethnicity": "Not Hispanic or Latino",
            "Clinical Brain Diagnosis (Basis for Clinical Diagnosis)": "Alcohol abuse, unspecified (Investigator Impression)",
            "ICD for Clinical Brain Diagnosis": "F10.1",
            "Neuropathology Diagnosis": "Coding Pending",
            "Brain Region": "Hippocampus, Amygdala, Cerebellum",
            "Brain Hemisphere": "Left, Right",
            "PMI (hours)": "29.5",
            "RIN": "7.8",
            "Preparation": "Left - Frozen, Right - Frozen",
            "Manner of Death": "Suicide",
            "Tissue Source": "None",
        }
        
        adapter = NIHAdapter()
        record = adapter.parse_row(row)
        
        assert record.subject_id == "NIH1000"
        assert record.repository == "Miami"
        assert record.age == 37
        assert record.sex == "male"  # normalized to lowercase
        assert record.race == "White"
        assert record.ethnicity == "Not Hispanic or Latino"

    def test_parse_repository_naming(self):
        """Should normalize repository names with NIH prefix for NIH sites."""
        adapter = NIHAdapter()
        
        # NIH sites should get prefixed
        assert adapter.normalize_repository("Miami") == "NIH Miami"
        assert adapter.normalize_repository("Maryland") == "NIH Maryland"
        assert adapter.normalize_repository("Sepulveda") == "NIH Sepulveda"
        assert adapter.normalize_repository("Pittsburgh") == "NIH Pittsburgh"
        assert adapter.normalize_repository("HBCC") == "NIH HBCC"
        assert adapter.normalize_repository("Maryland Psychiatric") == "NIH Maryland Psychiatric"
        assert adapter.normalize_repository("ADRC") == "NIH ADRC"
        
        # Non-NIH banks keep original names
        assert adapter.normalize_repository("Harvard") == "Harvard"
        assert adapter.normalize_repository("Mt. Sinai") == "Mt. Sinai"

    def test_parse_rin_placeholder(self):
        """Should convert RIN 99.99 to None (it's a placeholder)."""
        adapter = NIHAdapter()
        
        assert adapter.parse_rin("99.99") is None
        assert adapter.parse_rin("99.99, 99.99") is None
        assert adapter.parse_rin("7.8") == Decimal("7.8")
        assert adapter.parse_rin("8.3") == Decimal("8.3")
        assert adapter.parse_rin("") is None
        assert adapter.parse_rin("No Test Results Reported") is None

    def test_parse_pmi(self):
        """Should parse PMI hours correctly."""
        adapter = NIHAdapter()
        
        assert adapter.parse_pmi("29.5") == Decimal("29.5")
        assert adapter.parse_pmi("0") == Decimal("0")
        assert adapter.parse_pmi("") is None
        assert adapter.parse_pmi("Not Reported") is None

    def test_parse_age(self):
        """Should parse age correctly."""
        adapter = NIHAdapter()
        
        assert adapter.parse_age("37") == 37
        assert adapter.parse_age("0") == 0
        assert adapter.parse_age("88") == 88
        assert adapter.parse_age("") is None
        assert adapter.parse_age("Unknown") is None

    def test_parse_sex(self):
        """Should normalize sex values."""
        adapter = NIHAdapter()
        
        assert adapter.parse_sex("Male") == "male"
        assert adapter.parse_sex("Female") == "female"
        assert adapter.parse_sex("Unknown") is None
        assert adapter.parse_sex("Not Reported") is None
        assert adapter.parse_sex("Other") == "other"

    def test_parse_brain_regions(self):
        """Should parse comma-separated brain regions."""
        adapter = NIHAdapter()
        
        regions = "Hippocampus, Amygdala, Cerebellum (hemisphere)"
        result = adapter.parse_brain_regions(regions)
        
        assert result == "Hippocampus, Amygdala, Cerebellum (hemisphere)"

    def test_parse_hemisphere(self):
        """Should parse hemisphere information."""
        adapter = NIHAdapter()
        
        assert adapter.parse_hemisphere("Left, Right") == "both"
        assert adapter.parse_hemisphere("Left") == "left"
        assert adapter.parse_hemisphere("Right") == "right"
        assert adapter.parse_hemisphere("") is None

    def test_parse_preservation_method(self):
        """Should parse preparation/preservation method."""
        adapter = NIHAdapter()
        
        prep = "Left - Frozen, Right - Formalin Fixed"
        result = adapter.parse_preservation(prep)
        
        assert "Frozen" in result
        assert "Formalin Fixed" in result

    def test_parse_diagnosis_with_basis(self):
        """Should extract diagnosis and basis from combined field."""
        adapter = NIHAdapter()
        
        diag = "Alzheimer's disease with late onset (Confirmed Diagnosis)"
        result = adapter.parse_diagnosis(diag)
        
        assert result["diagnosis"] == "Alzheimer's disease with late onset"
        assert result["basis"] == "Confirmed Diagnosis"

    def test_parse_diagnosis_no_basis(self):
        """Should handle diagnosis without basis in parentheses."""
        adapter = NIHAdapter()
        
        diag = "No clinical brain diagnosis found"
        result = adapter.parse_diagnosis(diag)
        
        assert result["diagnosis"] == "No clinical brain diagnosis found"
        assert result["basis"] is None


class TestNIHRecordToSample:
    """Tests for converting NIHRecord to Sample model."""

    def test_convert_to_sample_dict(self):
        """Should convert NIHRecord to a dict suitable for Sample model."""
        row = {
            "Subject ID": "NIH1000",
            "Repository": "Miami",
            "Subject Age": "65",
            "Subject Sex": "Female",
            "Race": "White",
            "Ethnicity": "Not Hispanic or Latino",
            "Clinical Brain Diagnosis (Basis for Clinical Diagnosis)": "Alzheimer's disease with late onset (Confirmed Diagnosis)",
            "ICD for Clinical Brain Diagnosis": "G30.1",
            "Neuropathology Diagnosis": "Alzheimer's disease with late onset",
            "ICD for Neuropathology Diagnosis": "G30.1",
            "Brain Region": "Hippocampus, Frontal cortex",
            "Brain Hemisphere": "Left, Right",
            "PMI (hours)": "12.5",
            "RIN": "7.2",
            "Preparation": "Left - Frozen, Right - Frozen",
            "Manner of Death": "Natural",
            "Tissue Source": "None",
            "Thal Phase": "Phase 5 (A3)",
            "Braak NFT Stage": "Stage VI (B3)",
            "CERAD Score": "Frequent neuritic plaques (C3)",
            "ADNC": "High",
        }
        
        adapter = NIHAdapter()
        sample_dict = adapter.to_sample_dict(row)
        
        assert sample_dict["source_bank"] == "NIH Miami"
        assert sample_dict["external_id"] == "NIH1000"
        assert sample_dict["donor_age"] == 65
        assert sample_dict["donor_sex"] == "female"
        assert sample_dict["donor_race"] == "White"
        assert sample_dict["primary_diagnosis"] == "Alzheimer's disease with late onset"
        assert sample_dict["primary_diagnosis_code"] == "G30.1"
        assert sample_dict["postmortem_interval_hours"] == Decimal("12.5")
        assert sample_dict["rin_score"] == Decimal("7.2")
        assert sample_dict["hemisphere"] == "both"
        assert sample_dict["manner_of_death"] == "Natural"
        
        # Extended data should contain neuropathology scores
        assert "neuropathology_scores" in sample_dict["extended_data"]
        scores = sample_dict["extended_data"]["neuropathology_scores"]
        assert scores["thal_phase"] == "Phase 5 (A3)"
        assert scores["braak_nft_stage"] == "Stage VI (B3)"
        assert scores["cerad_score"] == "Frequent neuritic plaques (C3)"
        assert scores["adnc"] == "High"


class TestNIHAdapterFiltering:
    """Tests for filtering rows during import."""

    def test_should_skip_non_brain_rows(self):
        """Should skip rows where Tissue Source is 'Non-Brain'."""
        adapter = NIHAdapter()
        
        brain_row = {"Subject ID": "NIH1000", "Tissue Source": "None"}
        non_brain_row = {"Subject ID": "NIH1000", "Tissue Source": "Non-Brain"}
        
        assert adapter.should_include(brain_row) is True
        assert adapter.should_include(non_brain_row) is False

    def test_should_skip_empty_subject_id(self):
        """Should skip rows with empty Subject ID."""
        adapter = NIHAdapter()
        
        valid_row = {"Subject ID": "NIH1000", "Tissue Source": "None"}
        empty_row = {"Subject ID": "", "Tissue Source": "None"}
        none_row = {"Subject ID": None, "Tissue Source": "None"}
        
        assert adapter.should_include(valid_row) is True
        assert adapter.should_include(empty_row) is False
        assert adapter.should_include(none_row) is False


class TestNIHAdapterValidation:
    """Tests for data validation."""

    def test_validate_required_fields(self):
        """Should validate that required fields are present."""
        adapter = NIHAdapter()
        
        valid_row = {
            "Subject ID": "NIH1000",
            "Repository": "Miami",
            "Tissue Source": "None",
        }
        
        missing_repo = {
            "Subject ID": "NIH1000",
            "Repository": "",
            "Tissue Source": "None",
        }
        
        errors = adapter.validate(valid_row)
        assert len(errors) == 0
        
        errors = adapter.validate(missing_repo)
        assert len(errors) > 0
        assert any("Repository" in e for e in errors)

    def test_validate_numeric_ranges(self):
        """Should validate numeric values are in reasonable ranges."""
        adapter = NIHAdapter()
        
        # Age should be 0-120
        valid = {"Subject ID": "1", "Repository": "Miami", "Tissue Source": "None", "Subject Age": "65"}
        invalid_age = {"Subject ID": "1", "Repository": "Miami", "Tissue Source": "None", "Subject Age": "150"}
        
        assert len(adapter.validate(valid)) == 0
        errors = adapter.validate(invalid_age)
        assert any("age" in e.lower() for e in errors)


class TestNIHAdapterIntegration:
    """Integration tests for processing full CSV data."""

    def test_process_csv_sample(self, tmp_path):
        """Should process a sample CSV file correctly."""
        # Create a minimal test CSV
        csv_content = '''"Subject ID","Repository","Subject Age","Subject Sex","Race","Ethnicity","Clinical Brain Diagnosis (Basis for Clinical Diagnosis)","ICD for Clinical Brain Diagnosis","Neuropathology Diagnosis","Brain Region","Brain Hemisphere","PMI (hours)","RIN","Preparation","Manner of Death","Tissue Source","Thal Phase","Braak NFT Stage","CERAD Score","ADNC"
"NIH1000","Miami","65","Female","White","Not Hispanic or Latino","Alzheimer's disease (Confirmed Diagnosis)","G30.9","Alzheimer's disease","Hippocampus","Left, Right","12.5","7.2","Left - Frozen, Right - Frozen","Natural","None","Phase 5 (A3)","Stage VI (B3)","Frequent (C3)","High"
"NIH1001","Harvard","70","Male","White","Not Hispanic or Latino","Parkinson's disease (Confirmed Diagnosis)","G20","Parkinson's disease","Substantia nigra","Left","18.0","6.8","Left - Frozen","Natural","None","No Results Reported","No Results Reported","No Results Reported","No Results Reported"
"NIH1000","Miami","65","Female","White","Not Hispanic or Latino","None","","None","Non-Brain tissue","","","","","","Non-Brain","","","",""
'''
        
        csv_file = tmp_path / "test_samples.csv"
        csv_file.write_text(csv_content)
        
        adapter = NIHAdapter()
        samples = list(adapter.process_csv(str(csv_file)))
        
        # Should skip the non-brain row
        assert len(samples) == 2
        
        # Check first sample
        assert samples[0]["external_id"] == "NIH1000"
        assert samples[0]["source_bank"] == "NIH Miami"
        assert samples[0]["donor_age"] == 65
        
        # Check second sample (Harvard should not have NIH prefix)
        assert samples[1]["external_id"] == "NIH1001"
        assert samples[1]["source_bank"] == "Harvard"

