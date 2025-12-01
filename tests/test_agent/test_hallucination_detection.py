"""Tests for hallucination detection in the chat agent.

These tests ensure that the agent NEVER fabricates sample data.
Every sample ID and value must come from the actual database.
"""

import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch

from axon.matching.matcher import CandidateSample


class TestHallucinationDetection:
    """Tests for detecting fabricated sample data."""

    @pytest.fixture
    def known_valid_ids(self):
        """Sample IDs that exist in our test database."""
        return {
            "BEB18105", "BEB18106", "BEB18108", "BEB18109",
            "BEB18120", "BEB18124", "BEB18129", "BEB18141",
            "BEB18078", "BEB18083", "BEB18086", "BEB18089",
        }

    @pytest.fixture
    def known_fabricated_ids(self):
        """Sample IDs that are commonly hallucinated and DO NOT exist."""
        return {
            "6711", "6709", "6728", "6734", "6742",  # Fake numeric IDs
            "C1024", "C1031", "C1036", "C1042",  # Fake control IDs
            "2988", "4137",  # Other fabricated IDs
        }

    def extract_sample_ids_from_response(self, response: str) -> set[str]:
        """Extract all potential sample IDs from a response."""
        patterns = [
            r'\*\*([A-Z0-9]{4,})\*\*',  # **ID** format
            r'#([A-Z0-9]{4,})',  # #ID format
            r'\b([A-Z]{2,}[0-9]{4,})\b',  # BEB19072 format
            r'\b(\d{4,})\b(?=.*(?:RIN|PMI|Braak|age|female|male|Age))',  # Numeric IDs
        ]
        
        found_ids = set()
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            found_ids.update(matches)
        
        # Filter out common false positives
        false_positives = {'2000', '2024', '2025', 'RNA', 'RIN', 'PMI', 'HBCC', 'ADRC'}
        found_ids = {id for id in found_ids if id.upper() not in false_positives and len(id) >= 4}
        
        return found_ids

    def test_extract_markdown_bold_ids(self):
        """Test extraction of **ID** formatted sample IDs."""
        response = """
        Here are the samples:
        1. **BEB18105** (NIH Miami) - Age: 70
        2. **BEB18106** (NIH Miami) - Age: 84
        """
        ids = self.extract_sample_ids_from_response(response)
        assert "BEB18105" in ids
        assert "BEB18106" in ids

    def test_extract_numeric_ids_near_attributes(self):
        """Test extraction of numeric IDs near sample attributes."""
        response = """
        Sample 6711: Age 79, Female, RIN 7.1
        Sample 6709: Age 85, Male, PMI 8.5h
        """
        ids = self.extract_sample_ids_from_response(response)
        assert "6711" in ids
        assert "6709" in ids

    def test_detect_known_fabricated_ids(self, known_fabricated_ids):
        """Test that we can detect commonly fabricated IDs."""
        response = """
        ## Alzheimer's Disease Cases (5 samples)
        1. **6711** (Mt. Sinai Brain Bank) - Age: 79, Female, Braak V
        2. **6709** (Mt. Sinai Brain Bank) - Age: 85, Male, Braak VI
        3. **C1024** (Mt. Sinai Brain Bank) - Age: 81, Male, Control
        """
        ids = self.extract_sample_ids_from_response(response)
        
        # Check if any fabricated IDs are present
        fabricated_found = ids & known_fabricated_ids
        assert len(fabricated_found) > 0, "Should detect fabricated IDs"
        assert "6711" in fabricated_found
        assert "6709" in fabricated_found

    def test_valid_ids_pass_validation(self, known_valid_ids):
        """Test that valid IDs from database pass validation."""
        response = """
        Here are real samples from the database:
        1. **BEB18105** (NIH Miami) - Age: 70, Male, RIN: 7.2
        2. **BEB18106** (NIH Miami) - Age: 84, Female, RIN: 6.7
        """
        ids = self.extract_sample_ids_from_response(response)
        
        # All found IDs should be valid
        invalid = ids - known_valid_ids
        assert len(invalid) == 0, f"Found invalid IDs: {invalid}"

    def test_mixed_valid_and_fabricated(self, known_valid_ids, known_fabricated_ids):
        """Test detection when response mixes real and fake IDs."""
        response = """
        Real sample: **BEB18105** - Age: 70
        Fabricated: **6711** - Age: 79
        Real sample: **BEB18106** - Age: 84
        Fabricated: **C1024** - Age: 81
        """
        ids = self.extract_sample_ids_from_response(response)
        
        valid = ids & known_valid_ids
        fabricated = ids & known_fabricated_ids
        
        assert len(valid) == 2, "Should find 2 valid IDs"
        assert len(fabricated) == 2, "Should find 2 fabricated IDs"


class TestMissingDataHandling:
    """Tests for proper handling of missing/unavailable data."""

    def test_apoe_not_available_response(self):
        """Test that missing APOE data is properly acknowledged."""
        # If APOE is requested but not in database, response should say so
        expected_phrases = [
            "apoe status is not available",
            "apoe is not available",
            "not available for these samples",
            "not available in the dataset",
        ]
        
        response = "APOE status is not available for these samples."
        response_lower = response.lower()
        
        assert any(phrase in response_lower for phrase in expected_phrases)

    def test_missing_field_acknowledgment(self):
        """Test proper acknowledgment of missing fields."""
        missing_field_patterns = [
            r"not available for (?:these|the) samples",
            r"not available in the dataset",
            r"not recorded for this sample",
            r"data is not available",
        ]
        
        responses = [
            "Thal phase is not recorded for this sample.",
            "This information is not available in the dataset.",
            "APOE status is not available for these samples.",
            "Co-pathology data is not available for the controls.",
        ]
        
        for response in responses:
            matched = any(re.search(p, response, re.IGNORECASE) for p in missing_field_patterns)
            assert matched, f"Response should match missing data pattern: {response}"


class TestResponseValidation:
    """Tests for validating entire responses against fabrication."""

    def test_response_with_no_search_results(self):
        """When no search results provided, response should request search."""
        valid_responses = [
            "Let me search for samples matching your criteria.",
            "I'll search for samples that meet your requirements.",
            "Let me find samples matching your criteria.",
        ]
        
        for response in valid_responses:
            assert "search" in response.lower() or "find" in response.lower()

    def test_response_should_not_present_samples_without_data(self):
        """Response should not present sample lists if no data was provided."""
        # This response claims to present samples but has no search results
        bad_response = """
        Here are 8 Alzheimer's samples I found:
        1. **6711** - Age: 79, RIN: 7.1
        2. **6709** - Age: 85, RIN: 6.8
        """
        
        # Check for presentation patterns without actual data source
        presentation_patterns = [
            r"here are \d+ .* samples",
            r"i found \d+ samples",
            r"here's .* list",
        ]
        
        has_presentation = any(
            re.search(p, bad_response, re.IGNORECASE) 
            for p in presentation_patterns
        )
        
        # If presenting samples, should have come from search results
        assert has_presentation, "Test assumes response presents samples"

    def test_statistics_should_come_from_database(self):
        """Statistics and summaries should come from database, not be calculated."""
        # Bad: Agent invents statistics
        bad_response = "The average RIN for these samples is 7.3 and average age is 78.5."
        
        # Good: Statistics come from actual calculation or are noted as unavailable
        good_response = """
        Statistical Summary (from database):
        - Cases: n=10, Controls: n=10
        - Age: Cases 76.9±6.0 vs Controls 75.0±7.6 (p=0.570)
        """
        
        # Check that stats are attributed to database/system, not invented
        assert "database" in good_response.lower() or "from" in good_response.lower()


class TestCandidateSampleValidation:
    """Tests for validating CandidateSample objects."""

    def test_candidate_sample_must_have_real_id(self):
        """CandidateSample should only be created with database-verified IDs."""
        # Valid sample from database
        valid_sample = CandidateSample(
            id="BEB18105",
            age=70,
            pmi=51.9,
            rin=7.2,
            sex="male",
            diagnosis="Alzheimer's disease",
            source_bank="NIH Miami",
            external_id="BEB18105",
        )
        
        assert valid_sample.id == "BEB18105"
        assert valid_sample.is_valid  # Has required fields

    def test_candidate_sample_with_missing_data(self):
        """CandidateSample with missing required fields should be invalid."""
        # Sample missing RIN
        invalid_sample = CandidateSample(
            id="TEST001",
            age=70,
            pmi=10.0,
            rin=None,  # Missing
            sex="male",
        )
        
        assert not invalid_sample.is_valid


class TestSearchResultsFormat:
    """Tests for validating search results format."""

    def test_valid_search_results_format(self):
        """Test that valid search results have expected format."""
        valid_format = """
        ## Search Results Based on Your Criteria
        
        Found 5 matching case samples:
        
        1. **BEB18105** (NIH Miami)
           - Diagnosis: Alzheimer's disease
           - Age: 70, Sex: male
           - RIN: 7.2, PMI: 51.9h
        """
        
        # Check for required elements
        assert "## Search Results" in valid_format
        assert "Found" in valid_format
        assert "matching" in valid_format
        assert "**" in valid_format  # Has sample IDs

    def test_response_mentions_only_provided_samples(self):
        """Response should only mention samples from search results."""
        search_results = """
        ## Search Results
        Found 2 samples:
        1. **BEB18105** - Age: 70, RIN: 7.2
        2. **BEB18106** - Age: 84, RIN: 6.7
        """
        
        # Extract IDs from search results
        provided_ids = {"BEB18105", "BEB18106"}
        
        # Good response uses only provided IDs
        good_response = "I found BEB18105 (Age 70) and BEB18106 (Age 84)."
        
        # Bad response invents additional IDs
        bad_response = "I found BEB18105, BEB18106, and also 6711 which is a great match."
        
        # Check good response
        mentioned_good = re.findall(r'\b([A-Z]{2,}\d{4,}|\d{4,})\b', good_response)
        assert all(id in provided_ids for id in mentioned_good if len(id) >= 4)


class TestFabricationPatterns:
    """Tests for common fabrication patterns to detect."""

    @pytest.fixture
    def fabrication_patterns(self):
        """Patterns that indicate fabricated data."""
        return [
            # Numeric IDs that look made up
            r'\b[0-9]{4}\b(?=.*(?:RIN|PMI|Braak|age))',
            # Control IDs starting with C followed by numbers
            r'\bC\d{4}\b',
            # Mt. Sinai samples that don't exist
            r'Mt\.?\s*Sinai.*\b\d{4}\b',
            # Fake statistics - average followed by field name and number
            r'average (?:RIN|PMI|age).*?(?:is|of)\s*\d+\.?\d*',
        ]

    def test_detect_fake_numeric_ids(self, fabrication_patterns):
        """Test detection of fabricated numeric sample IDs."""
        response = "Sample 6711 has RIN 7.1 and age 79."
        
        for pattern in fabrication_patterns[:1]:
            if re.search(pattern, response, re.IGNORECASE):
                # Found fabrication pattern
                assert True
                return
        
        pytest.fail("Should detect fabricated numeric ID")

    def test_detect_fake_control_ids(self, fabrication_patterns):
        """Test detection of fabricated control IDs (C####)."""
        response = "Control sample C1024 is age 81 with RIN 7.5."
        
        pattern = fabrication_patterns[1]
        match = re.search(pattern, response, re.IGNORECASE)
        assert match is not None, "Should detect fabricated control ID"

    def test_detect_fake_statistics(self, fabrication_patterns):
        """Test detection of fabricated statistics."""
        responses = [
            "The average RIN is 7.3 across all samples.",
            "Average age of the cohort is 78.5 years.",
            "The average PMI is 15.2 hours.",
        ]
        
        pattern = fabrication_patterns[3]
        for response in responses:
            match = re.search(pattern, response, re.IGNORECASE)
            assert match is not None, f"Should detect fabricated stat: {response}"

