"""Tests for sample matching algorithm."""

import pytest
from axon.matching.matcher import (
    SampleMatcher,
    MatchResult,
    CandidateSample,
    calculate_distance,
)


class TestCandidateSample:
    """Tests for CandidateSample dataclass."""

    def test_candidate_creation(self):
        """Test creating a candidate sample."""
        candidate = CandidateSample(
            id="sample-123",
            age=75,
            pmi=8.5,
            rin=7.2,
            sex="female",
            diagnosis="Alzheimer's disease",
        )
        
        assert candidate.id == "sample-123"
        assert candidate.age == 75
        assert candidate.is_valid  # Has all required fields

    def test_candidate_missing_data_invalid(self):
        """Test that missing PMI or RIN makes candidate invalid."""
        candidate = CandidateSample(
            id="sample-123",
            age=75,
            pmi=None,  # Missing
            rin=7.2,
            sex="female",
            diagnosis="Alzheimer's disease",
        )
        
        assert not candidate.is_valid

    def test_candidate_missing_rin_invalid(self):
        """Test that missing RIN makes candidate invalid."""
        candidate = CandidateSample(
            id="sample-123",
            age=75,
            pmi=8.5,
            rin=None,  # Missing
            sex="female",
            diagnosis="Alzheimer's disease",
        )
        
        assert not candidate.is_valid


class TestDistanceCalculation:
    """Tests for distance calculation between samples."""

    def test_identical_samples_zero_distance(self):
        """Test that identical samples have zero distance."""
        sample1 = CandidateSample(id="1", age=75, pmi=8.0, rin=7.0, sex="female")
        sample2 = CandidateSample(id="2", age=75, pmi=8.0, rin=7.0, sex="female")
        
        distance = calculate_distance(sample1, sample2)
        assert distance == 0.0

    def test_age_difference_increases_distance(self):
        """Test that age difference increases distance."""
        sample1 = CandidateSample(id="1", age=75, pmi=8.0, rin=7.0, sex="female")
        sample2 = CandidateSample(id="2", age=85, pmi=8.0, rin=7.0, sex="female")
        
        distance = calculate_distance(sample1, sample2)
        assert distance > 0

    def test_pmi_difference_increases_distance(self):
        """Test that PMI difference increases distance."""
        sample1 = CandidateSample(id="1", age=75, pmi=8.0, rin=7.0, sex="female")
        sample2 = CandidateSample(id="2", age=75, pmi=12.0, rin=7.0, sex="female")
        
        distance = calculate_distance(sample1, sample2)
        assert distance > 0

    def test_rin_difference_increases_distance(self):
        """Test that RIN difference increases distance."""
        sample1 = CandidateSample(id="1", age=75, pmi=8.0, rin=7.0, sex="female")
        sample2 = CandidateSample(id="2", age=75, pmi=8.0, rin=5.0, sex="female")
        
        distance = calculate_distance(sample1, sample2)
        assert distance > 0

    def test_custom_weights(self):
        """Test distance calculation with custom weights."""
        sample1 = CandidateSample(id="1", age=75, pmi=8.0, rin=7.0, sex="female")
        sample2 = CandidateSample(id="2", age=85, pmi=8.0, rin=7.0, sex="female")
        
        # Higher age weight should increase distance for age difference
        distance_normal = calculate_distance(sample1, sample2, age_weight=1.0)
        distance_weighted = calculate_distance(sample1, sample2, age_weight=2.0)
        
        assert distance_weighted > distance_normal


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_match_result_creation(self):
        """Test creating a match result."""
        result = MatchResult(
            cases=[],
            controls=[],
            statistical_report=None,
            success=True,
            message="Matching successful",
        )
        
        assert result.success
        assert result.message == "Matching successful"

    def test_match_result_failure(self):
        """Test match result for failed matching."""
        result = MatchResult(
            cases=[],
            controls=[],
            statistical_report=None,
            success=False,
            message="Could not find balanced match",
            suggestions=["Relax PMI constraint", "Reduce sample size"],
        )
        
        assert not result.success
        assert len(result.suggestions) == 2


class TestSampleMatcher:
    """Tests for the main SampleMatcher class."""

    @pytest.fixture
    def matcher(self):
        """Create a SampleMatcher instance."""
        return SampleMatcher()

    @pytest.fixture
    def case_candidates(self):
        """Create sample case candidates (Alzheimer's)."""
        return [
            CandidateSample(id="ad1", age=75, pmi=8.0, rin=7.0, sex="female", diagnosis="Alzheimer's"),
            CandidateSample(id="ad2", age=78, pmi=9.0, rin=7.2, sex="female", diagnosis="Alzheimer's"),
            CandidateSample(id="ad3", age=80, pmi=7.5, rin=6.8, sex="male", diagnosis="Alzheimer's"),
            CandidateSample(id="ad4", age=77, pmi=8.5, rin=7.1, sex="male", diagnosis="Alzheimer's"),
            CandidateSample(id="ad5", age=82, pmi=8.2, rin=6.9, sex="female", diagnosis="Alzheimer's"),
            CandidateSample(id="ad6", age=76, pmi=7.8, rin=7.3, sex="male", diagnosis="Alzheimer's"),
        ]

    @pytest.fixture
    def control_candidates(self):
        """Create sample control candidates (no diagnosis)."""
        return [
            CandidateSample(id="ctrl1", age=74, pmi=8.2, rin=7.1, sex="female", diagnosis="Control"),
            CandidateSample(id="ctrl2", age=79, pmi=8.8, rin=6.9, sex="female", diagnosis="Control"),
            CandidateSample(id="ctrl3", age=78, pmi=7.8, rin=7.3, sex="male", diagnosis="Control"),
            CandidateSample(id="ctrl4", age=75, pmi=8.3, rin=7.0, sex="male", diagnosis="Control"),
            CandidateSample(id="ctrl5", age=81, pmi=8.1, rin=7.2, sex="female", diagnosis="Control"),
            CandidateSample(id="ctrl6", age=77, pmi=7.9, rin=7.0, sex="male", diagnosis="Control"),
            CandidateSample(id="ctrl7", age=76, pmi=8.4, rin=6.8, sex="female", diagnosis="Control"),
            CandidateSample(id="ctrl8", age=80, pmi=8.0, rin=7.1, sex="male", diagnosis="Control"),
        ]

    def test_filter_valid_candidates(self, matcher):
        """Test filtering out candidates with missing data."""
        candidates = [
            CandidateSample(id="1", age=75, pmi=8.0, rin=7.0, sex="female"),
            CandidateSample(id="2", age=78, pmi=None, rin=7.2, sex="female"),  # Invalid
            CandidateSample(id="3", age=80, pmi=7.5, rin=None, sex="male"),  # Invalid
            CandidateSample(id="4", age=77, pmi=8.5, rin=7.1, sex="male"),
        ]
        
        valid = matcher.filter_valid_candidates(candidates)
        assert len(valid) == 2
        assert all(c.is_valid for c in valid)

    def test_group_by_sex(self, matcher, control_candidates):
        """Test grouping candidates by sex."""
        groups = matcher.group_by_sex(control_candidates)
        
        assert "female" in groups
        assert "male" in groups
        assert len(groups["female"]) == 4
        assert len(groups["male"]) == 4

    def test_match_with_sex_balance(self, matcher, case_candidates, control_candidates):
        """Test matching maintains sex balance."""
        result = matcher.find_matched_sets(
            cases=case_candidates[:4],  # 2 female, 2 male
            controls=control_candidates,
            n_per_group=4,
            exact_sex_match=True,
        )
        
        assert result.success
        
        # Check sex distribution matches
        case_females = sum(1 for c in result.cases if c.sex == "female")
        control_females = sum(1 for c in result.controls if c.sex == "female")
        assert case_females == control_females

    def test_match_produces_balanced_groups(self, matcher, case_candidates, control_candidates):
        """Test that matching produces statistically balanced groups."""
        result = matcher.find_matched_sets(
            cases=case_candidates[:4],
            controls=control_candidates,
            n_per_group=4,
            exact_sex_match=True,
        )
        
        assert result.success
        assert result.statistical_report is not None
        assert result.statistical_report.is_balanced

    def test_match_insufficient_controls(self, matcher, case_candidates):
        """Test handling when not enough controls available."""
        few_controls = [
            CandidateSample(id="ctrl1", age=74, pmi=8.2, rin=7.1, sex="female", diagnosis="Control"),
        ]
        
        result = matcher.find_matched_sets(
            cases=case_candidates,
            controls=few_controls,
            n_per_group=6,
            exact_sex_match=True,
        )
        
        assert not result.success
        assert "insufficient" in result.message.lower() or "not enough" in result.message.lower()

    def test_match_with_ratio(self, matcher, case_candidates, control_candidates):
        """Test matching with 1:2 case:control ratio."""
        result = matcher.find_matched_sets(
            cases=case_candidates[:3],
            controls=control_candidates,
            n_per_group=3,
            control_ratio=2,  # 2 controls per case
            exact_sex_match=False,  # Relax for this test
        )
        
        assert result.success
        assert len(result.cases) == 3
        assert len(result.controls) == 6  # 3 * 2

