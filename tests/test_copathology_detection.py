"""Tests for co-pathology detection logic.

Verifies that:
1. AD staging metrics (ADNC, Thal, CERAD) are NOT reported as co-pathologies
2. TRUE co-pathologies (Lewy, CAA, TDP-43, etc.) are only reported when POSITIVE
3. "None" is returned when no positive co-pathologies are found
"""

import pytest
from axon.agent.icd_mapping import (
    build_copathology_summary,
    extract_copathology_info,
    has_copathology,
    _is_positive_lewy,
    _is_positive_tdp43,
    _is_positive_caa,
    _is_positive_late_nc,
    _is_positive_vascular,
    _is_positive_als_tdp,
)


class TestPositiveDetectionHelpers:
    """Tests for individual co-pathology positive detection functions."""
    
    def test_lewy_negative_cases(self):
        """Lewy body should be negative for 'No Lewy Body Pathology' and similar."""
        assert _is_positive_lewy(None) is False
        assert _is_positive_lewy("") is False
        assert _is_positive_lewy("No Lewy Body Pathology") is False
        assert _is_positive_lewy("None") is False
        assert _is_positive_lewy("No Results Reported") is False
        assert _is_positive_lewy("Not Assessed") is False
    
    def test_lewy_positive_cases(self):
        """Lewy body should be positive for actual pathology findings."""
        assert _is_positive_lewy("Limbic") is True
        assert _is_positive_lewy("Brainstem") is True
        assert _is_positive_lewy("Neocortical") is True
        assert _is_positive_lewy("Amygdala-predominant") is True
    
    def test_tdp43_negative_cases(self):
        """TDP-43 should be negative for 'No' and similar."""
        assert _is_positive_tdp43(None) is False
        assert _is_positive_tdp43("") is False
        assert _is_positive_tdp43("No") is False
        assert _is_positive_tdp43("None") is False
        assert _is_positive_tdp43("Not Assessed") is False
    
    def test_tdp43_positive_cases(self):
        """TDP-43 should be positive for 'Yes' and similar."""
        assert _is_positive_tdp43("Yes") is True
        assert _is_positive_tdp43("Present") is True
    
    def test_caa_negative_cases(self):
        """CAA should be negative for Grade 0 and None."""
        assert _is_positive_caa(None) is False
        assert _is_positive_caa("") is False
        assert _is_positive_caa("Grade 0") is False
        assert _is_positive_caa("None") is False
        assert _is_positive_caa("No Results Reported") is False
    
    def test_caa_positive_cases(self):
        """CAA should be positive for Grade > 0."""
        assert _is_positive_caa("Grade 1") is True
        assert _is_positive_caa("Grade 2") is True
        assert _is_positive_caa("Grade 3") is True
        assert _is_positive_caa("Mild") is True
        assert _is_positive_caa("Moderate") is True
        assert _is_positive_caa("Severe") is True
    
    def test_late_nc_negative_cases(self):
        """LATE-NC should be negative when all regions are 'No'."""
        assert _is_positive_late_nc(None) is False
        assert _is_positive_late_nc("") is False
        assert _is_positive_late_nc("Amygdala - No, Entorhinal Cortex - No, Hippocampus - No, Neocortex - No") is False
    
    def test_late_nc_positive_cases(self):
        """LATE-NC should be positive when any region is 'Yes'."""
        assert _is_positive_late_nc("Amygdala - Yes, Entorhinal Cortex - No") is True
        assert _is_positive_late_nc("Hippocampus - Yes") is True
    
    def test_vascular_negative_cases(self):
        """Vascular should be negative for 'None' and similar."""
        assert _is_positive_vascular(None) is False
        assert _is_positive_vascular("") is False
        assert _is_positive_vascular("None") is False
        assert _is_positive_vascular("No Results Reported") is False
    
    def test_vascular_positive_cases(self):
        """Vascular should be positive for actual findings."""
        assert _is_positive_vascular("Mild") is True
        assert _is_positive_vascular("Moderate") is True
        assert _is_positive_vascular("Severe") is True


class TestBuildCopathologySummary:
    """Tests for build_copathology_summary function."""
    
    def test_no_copathologies_returns_none(self):
        """Should return 'None' when there are no positive co-pathologies."""
        # AD staging metrics should NOT be reported as co-pathologies
        neuropath_metrics = {
            "ADNC": "High",
            "Thal_Phase": "Phase 5 (A3)",
            "CERAD": "Frequent neuritic plaques (C3)",
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert result == "None"
    
    def test_negative_copathology_findings_return_none(self):
        """Should return 'None' when co-pathology metrics are negative."""
        neuropath_metrics = {
            "ADNC": "High",  # AD staging - NOT a co-pathology
            "Lewy_Pathology": "No Lewy Body Pathology",  # Negative
            "CAA": "Grade 0",  # Negative
            "TDP-43": "No",  # Negative
            "LATE-NC": "Amygdala - No, Entorhinal Cortex - No",  # Negative
            "Small_Vessel_Disease": "None",  # Negative
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert result == "None"
    
    def test_positive_lewy_body(self):
        """Should report Lewy body when positive."""
        neuropath_metrics = {
            "Lewy_Pathology": "Limbic",
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert "Lewy body (Limbic)" in result
    
    def test_positive_caa(self):
        """Should report CAA when positive (Grade > 0)."""
        neuropath_metrics = {
            "CAA": "Grade 2",
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert "CAA (Grade 2)" in result
    
    def test_positive_tdp43(self):
        """Should report TDP-43 when positive."""
        neuropath_metrics = {
            "TDP-43": "Yes",
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert "TDP-43" in result
    
    def test_positive_late_nc(self):
        """Should report LATE-NC when any region is positive."""
        neuropath_metrics = {
            "LATE-NC": "Amygdala - Yes, Entorhinal Cortex - No",
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert "LATE-NC" in result
    
    def test_positive_vascular(self):
        """Should report vascular when positive."""
        neuropath_metrics = {
            "Small_Vessel_Disease": "Moderate",
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert "Vascular (Moderate)" in result
    
    def test_multiple_copathologies(self):
        """Should report multiple co-pathologies when present."""
        neuropath_metrics = {
            "Lewy_Pathology": "Limbic",
            "CAA": "Grade 1",
            "ADNC": "High",  # Should NOT be included
        }
        result = build_copathology_summary([], neuropath_metrics)
        assert "Lewy body (Limbic)" in result
        assert "CAA (Grade 1)" in result
        assert "ADNC" not in result
        assert "High" not in result  # ADNC value should not appear
    
    def test_adnc_thal_cerad_not_included(self):
        """AD staging metrics should NEVER be included in co-pathology summary."""
        neuropath_metrics = {
            "ADNC": "High",
            "Thal_Phase": "Phase 5",
            "CERAD": "Frequent",
            "Lewy_Pathology": "Limbic",  # Only this should appear
        }
        result = build_copathology_summary([], neuropath_metrics)
        
        # Should NOT contain AD staging metrics
        assert "ADNC" not in result
        assert "Thal" not in result
        assert "CERAD" not in result
        assert "Phase" not in result
        assert "Frequent" not in result
        
        # Should contain the actual co-pathology
        assert "Lewy body" in result


class TestHasCopathology:
    """Tests for has_copathology function with positive detection."""
    
    def test_has_lewy_negative(self):
        """Should return False when Lewy is negative."""
        copath_info = extract_copathology_info(
            sample_raw_data={"Lewy Pathology": "No Lewy Body Pathology"},
            sample_extended_data=None,
            primary_diagnosis_code=None,
        )
        assert has_copathology(copath_info, ["Lewy"]) is False
    
    def test_has_lewy_positive(self):
        """Should return True when Lewy is positive."""
        copath_info = extract_copathology_info(
            sample_raw_data={"Lewy Pathology": "Limbic"},
            sample_extended_data=None,
            primary_diagnosis_code=None,
        )
        assert has_copathology(copath_info, ["Lewy"]) is True
    
    def test_has_caa_negative(self):
        """Should return False when CAA is Grade 0."""
        copath_info = extract_copathology_info(
            sample_raw_data={"Cerebral Amyloid Angiopathy": "Grade 0"},
            sample_extended_data=None,
            primary_diagnosis_code=None,
        )
        assert has_copathology(copath_info, ["CAA"]) is False
    
    def test_has_caa_positive(self):
        """Should return True when CAA is Grade > 0."""
        copath_info = extract_copathology_info(
            sample_raw_data={"Cerebral Amyloid Angiopathy": "Grade 2"},
            sample_extended_data=None,
            primary_diagnosis_code=None,
        )
        assert has_copathology(copath_info, ["CAA"]) is True


class TestExtractCopathologyInfo:
    """Tests for extract_copathology_info function."""
    
    def test_typical_ad_sample_no_copathologies(self):
        """A typical AD sample with no co-pathologies should return 'None' summary."""
        raw_data = {
            "ADNC": "High",
            "Thal Phase": "Phase 5 (A3)",
            "CERAD Score": "Frequent neuritic plaques (C3)",
            "Lewy Pathology": "No Lewy Body Pathology",
            "TDP-43 Proteinopathy": "No",
            "Cerebral Amyloid Angiopathy": "Grade 0",
            "LATE-NC": "Amygdala - No, Entorhinal Cortex - No, Hippocampus - No, Neocortex - No",
            "Small Vessel Disease/Arteriolar Sclerosis": "None",
        }
        
        copath_info = extract_copathology_info(
            sample_raw_data=raw_data,
            sample_extended_data=None,
            primary_diagnosis_code="G30.1",
        )
        
        assert copath_info.summary == "None"
    
    def test_ad_sample_with_lewy_copathology(self):
        """AD sample with Lewy body co-pathology should report it."""
        raw_data = {
            "ADNC": "High",
            "Lewy Pathology": "Limbic",
            "TDP-43 Proteinopathy": "No",
            "Cerebral Amyloid Angiopathy": "Grade 0",
        }
        
        copath_info = extract_copathology_info(
            sample_raw_data=raw_data,
            sample_extended_data=None,
            primary_diagnosis_code="G30.1",
        )
        
        assert "Lewy body (Limbic)" in copath_info.summary
        assert "ADNC" not in copath_info.summary

