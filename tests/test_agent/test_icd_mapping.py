"""Tests for ICD-10 code mapping and co-pathology detection."""

import pytest
from axon.agent.icd_mapping import (
    parse_icd_codes,
    get_copathology_from_icd,
    extract_copathology_info,
    has_copathology,
    CopathologyInfo,
    ICD10_COPATHOLOGY_MAP,
    COPATHOLOGY_CATEGORIES,
)


class TestParseICDCodes:
    """Tests for ICD code parsing."""
    
    def test_parse_comma_separated(self):
        """Parse comma-separated ICD codes."""
        codes = parse_icd_codes("G30.9, I67.9")
        assert codes == ["G30.9", "I67.9"]
    
    def test_parse_semicolon_separated(self):
        """Parse semicolon-separated ICD codes."""
        codes = parse_icd_codes("G30.1; G31.83")
        assert codes == ["G30.1", "G31.83"]
    
    def test_parse_single_code(self):
        """Parse single ICD code."""
        codes = parse_icd_codes("G30.9")
        assert codes == ["G30.9"]
    
    def test_parse_empty_string(self):
        """Empty string returns empty list."""
        codes = parse_icd_codes("")
        assert codes == []
    
    def test_parse_none(self):
        """None returns empty list."""
        codes = parse_icd_codes(None)
        assert codes == []
    
    def test_filters_invalid_codes(self):
        """Invalid codes are filtered out."""
        codes = parse_icd_codes("G30.9, invalid, I67.9")
        assert codes == ["G30.9", "I67.9"]
    
    def test_case_insensitive(self):
        """Codes are normalized to uppercase."""
        codes = parse_icd_codes("g30.9, i67.9")
        assert codes == ["G30.9", "I67.9"]


class TestGetCopathologyFromICD:
    """Tests for ICD code to co-pathology mapping."""
    
    def test_exact_match(self):
        """Exact ICD code match."""
        result = get_copathology_from_icd("G30.1")
        assert result is not None
        name, category = result
        assert "Alzheimer" in name
        assert category == "AD"
    
    def test_prefix_match(self):
        """Prefix matching for codes not in map."""
        result = get_copathology_from_icd("G30.99")  # Not in map exactly
        assert result is not None
        name, category = result
        assert "Alzheimer" in name
    
    def test_lewy_body_code(self):
        """G31.83 maps to Lewy body dementia."""
        result = get_copathology_from_icd("G31.83")
        assert result is not None
        name, category = result
        assert "Lewy" in name
        assert category == "Lewy"
    
    def test_caa_code(self):
        """I68.0 maps to CAA."""
        result = get_copathology_from_icd("I68.0")
        assert result is not None
        name, category = result
        assert "Amyloid Angiopathy" in name
        assert category == "CAA"
    
    def test_unknown_code_returns_none(self):
        """Unknown codes return None."""
        result = get_copathology_from_icd("Z99.99")
        assert result is None


class TestExtractCopathologyInfo:
    """Tests for comprehensive co-pathology extraction."""
    
    def test_extracts_from_primary_diagnosis_code(self):
        """Extracts co-pathologies from primary_diagnosis_code."""
        result = extract_copathology_info(
            sample_raw_data=None,
            sample_extended_data=None,
            primary_diagnosis_code="G30.9, G31.83",
        )
        
        assert len(result.icd_copathologies) == 2
        categories = [c["category"] for c in result.icd_copathologies]
        assert "AD" in categories
        assert "Lewy" in categories
    
    def test_extracts_from_extended_data(self):
        """Extracts co-pathologies from extended_data.neuropathology_diagnosis_code."""
        result = extract_copathology_info(
            sample_raw_data=None,
            sample_extended_data={"neuropathology_diagnosis_code": "G30.9, I68.0"},
            primary_diagnosis_code=None,
        )
        
        categories = [c["category"] for c in result.icd_copathologies]
        assert "AD" in categories
        assert "CAA" in categories
    
    def test_extracts_neuropath_metrics(self):
        """Extracts neuropathology metrics from raw_data."""
        result = extract_copathology_info(
            sample_raw_data={
                "ADNC": "High",
                "Lewy Pathology": "Limbic/transitional",
                "TDP-43 Proteinopathy": "Present",
                "Thal Phase": "Phase 5 (A3)",
                "CERAD Score": "Frequent neuritic plaques (C3)",
            },
            sample_extended_data=None,
            primary_diagnosis_code=None,
        )
        
        assert result.neuropath_metrics.get("ADNC") == "High"
        assert result.neuropath_metrics.get("Lewy_Pathology") == "Limbic/transitional"
        assert result.neuropath_metrics.get("TDP-43") == "Present"
        assert "Phase 5" in result.neuropath_metrics.get("Thal_Phase", "")
    
    def test_filters_no_results_reported(self):
        """Filters out 'No Results Reported' values."""
        result = extract_copathology_info(
            sample_raw_data={
                "ADNC": "No Results Reported",
                "Lewy Pathology": "Not Assessed",
                "TDP-43 Proteinopathy": "Present",
            },
            sample_extended_data=None,
            primary_diagnosis_code=None,
        )
        
        assert "ADNC" not in result.neuropath_metrics
        assert "Lewy_Pathology" not in result.neuropath_metrics
        assert "TDP-43" in result.neuropath_metrics
    
    def test_builds_summary(self):
        """Builds human-readable summary."""
        result = extract_copathology_info(
            sample_raw_data={"ADNC": "High", "Thal Phase": "Phase 5"},
            sample_extended_data={"neuropathology_diagnosis_code": "G31.83, I68.0"},
            primary_diagnosis_code="G30.9",
        )
        
        assert "Lewy Body Dementia" in result.summary
        assert "ADNC: High" in result.summary


class TestHasCopathology:
    """Tests for co-pathology detection."""
    
    def test_detects_icd_copathology(self):
        """Detects co-pathology from ICD codes."""
        copath_info = extract_copathology_info(
            sample_raw_data=None,
            sample_extended_data=None,
            primary_diagnosis_code="G30.9, G31.83",
        )
        
        assert has_copathology(copath_info, ["Lewy"]) is True
        assert has_copathology(copath_info, ["CAA"]) is False
    
    def test_detects_neuropath_metric_copathology(self):
        """Detects co-pathology from neuropathology metrics."""
        copath_info = extract_copathology_info(
            sample_raw_data={"TDP-43 Proteinopathy": "Present"},
            sample_extended_data=None,
            primary_diagnosis_code="G30.9",
        )
        
        assert has_copathology(copath_info, ["TDP-43"]) is True
        assert has_copathology(copath_info, ["Lewy"]) is False
    
    def test_detects_multiple_categories(self):
        """Detects any of multiple categories."""
        copath_info = extract_copathology_info(
            sample_raw_data=None,
            sample_extended_data=None,
            primary_diagnosis_code="G30.9, I68.0",
        )
        
        assert has_copathology(copath_info, ["Lewy", "CAA"]) is True
        assert has_copathology(copath_info, ["Lewy"]) is False


class TestCopathologyCategories:
    """Tests for co-pathology category definitions."""
    
    def test_key_categories_exist(self):
        """Key co-pathology categories are defined."""
        assert "Lewy" in COPATHOLOGY_CATEGORIES
        assert "CAA" in COPATHOLOGY_CATEGORIES
        assert "TDP-43" not in COPATHOLOGY_CATEGORIES  # Not in categories but handled via metrics
        assert "Vascular" in COPATHOLOGY_CATEGORIES
        assert "FTD" in COPATHOLOGY_CATEGORIES
    
    def test_ad_not_a_copathology(self):
        """Alzheimer's itself is not classified as a co-pathology."""
        # When studying AD, having AD is not a co-pathology
        assert "AD" not in COPATHOLOGY_CATEGORIES


class TestICDCodeMap:
    """Tests for ICD code mapping coverage."""
    
    def test_alzheimer_codes_mapped(self):
        """All G30.x codes are mapped."""
        assert "G30" in ICD10_COPATHOLOGY_MAP
        assert "G30.0" in ICD10_COPATHOLOGY_MAP
        assert "G30.1" in ICD10_COPATHOLOGY_MAP
        assert "G30.9" in ICD10_COPATHOLOGY_MAP
    
    def test_parkinsons_codes_mapped(self):
        """Parkinson's and Lewy body codes are mapped."""
        assert "G20" in ICD10_COPATHOLOGY_MAP
        assert "G31.83" in ICD10_COPATHOLOGY_MAP
    
    def test_vascular_codes_mapped(self):
        """Vascular and cerebrovascular codes are mapped."""
        assert "I67" in ICD10_COPATHOLOGY_MAP
        assert "I68.0" in ICD10_COPATHOLOGY_MAP
        assert "F01" in ICD10_COPATHOLOGY_MAP

