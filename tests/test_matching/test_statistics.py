"""Tests for statistical validation of matched samples."""

import pytest
from axon.matching.statistics import (
    StatisticalReport,
    run_balance_tests,
    calculate_group_stats,
    ttest_or_mannwhitney,
)


class TestStatisticalReport:
    """Tests for StatisticalReport dataclass."""

    def test_report_creation(self):
        """Test creating a statistical report."""
        report = StatisticalReport(
            n_cases=14,
            n_controls=14,
            case_age_mean=78.2,
            case_age_sd=6.3,
            control_age_mean=76.8,
            control_age_sd=5.9,
            age_pvalue=0.54,
            case_pmi_mean=8.4,
            case_pmi_sd=3.2,
            control_pmi_mean=9.1,
            control_pmi_sd=2.8,
            pmi_pvalue=0.31,
            case_rin_mean=7.2,
            case_rin_sd=1.1,
            control_rin_mean=7.0,
            control_rin_sd=0.9,
            rin_pvalue=0.62,
        )
        
        assert report.n_cases == 14
        assert report.age_pvalue == 0.54
        assert report.is_balanced  # All p > 0.05

    def test_report_not_balanced(self):
        """Test report correctly identifies imbalanced groups."""
        report = StatisticalReport(
            n_cases=14,
            n_controls=14,
            case_age_mean=78.2,
            case_age_sd=6.3,
            control_age_mean=65.0,  # Much younger
            control_age_sd=5.9,
            age_pvalue=0.001,  # Significant difference
            case_pmi_mean=8.4,
            case_pmi_sd=3.2,
            control_pmi_mean=9.1,
            control_pmi_sd=2.8,
            pmi_pvalue=0.31,
            case_rin_mean=7.2,
            case_rin_sd=1.1,
            control_rin_mean=7.0,
            control_rin_sd=0.9,
            rin_pvalue=0.62,
        )
        
        assert not report.is_balanced  # Age p < 0.05

    def test_report_formatted_output(self):
        """Test report generates readable summary."""
        report = StatisticalReport(
            n_cases=14,
            n_controls=14,
            case_age_mean=78.2,
            case_age_sd=6.3,
            control_age_mean=76.8,
            control_age_sd=5.9,
            age_pvalue=0.54,
            case_pmi_mean=8.4,
            case_pmi_sd=3.2,
            control_pmi_mean=9.1,
            control_pmi_sd=2.8,
            pmi_pvalue=0.31,
            case_rin_mean=7.2,
            case_rin_sd=1.1,
            control_rin_mean=7.0,
            control_rin_sd=0.9,
            rin_pvalue=0.62,
        )
        
        summary = report.to_summary()
        assert "Age" in summary
        assert "PMI" in summary
        assert "RIN" in summary
        assert "78.2" in summary  # Case age mean


class TestGroupStats:
    """Tests for calculating group statistics."""

    def test_calculate_mean_and_sd(self):
        """Test basic mean and SD calculation."""
        values = [70, 75, 80, 85, 90]
        mean, sd = calculate_group_stats(values)
        
        assert mean == 80.0
        assert 6.0 < sd < 8.0  # Approximately 7.07

    def test_empty_list(self):
        """Test handling of empty list."""
        mean, sd = calculate_group_stats([])
        assert mean is None
        assert sd is None

    def test_single_value(self):
        """Test handling of single value (SD undefined)."""
        mean, sd = calculate_group_stats([75])
        assert mean == 75.0
        assert sd == 0.0  # Or could be None


class TestStatisticalTests:
    """Tests for statistical comparison functions."""

    def test_similar_groups_high_pvalue(self):
        """Test that similar groups produce high p-value."""
        group1 = [70, 72, 74, 76, 78, 80, 82, 84]
        group2 = [71, 73, 75, 77, 79, 81, 83, 85]
        
        pvalue = ttest_or_mannwhitney(group1, group2)
        assert pvalue > 0.05  # Not significantly different

    def test_different_groups_low_pvalue(self):
        """Test that different groups produce low p-value."""
        group1 = [70, 72, 74, 76, 78, 80, 82, 84]
        group2 = [40, 42, 44, 46, 48, 50, 52, 54]  # Much lower
        
        pvalue = ttest_or_mannwhitney(group1, group2)
        assert pvalue < 0.05  # Significantly different

    def test_handles_small_samples(self):
        """Test handling of small sample sizes."""
        group1 = [70, 75, 80]
        group2 = [72, 77, 82]
        
        pvalue = ttest_or_mannwhitney(group1, group2)
        assert 0 <= pvalue <= 1


class TestRunBalanceTests:
    """Tests for the main balance testing function."""

    def test_balanced_samples(self):
        """Test with well-balanced case and control samples."""
        # Mock sample data with similar distributions
        cases = [
            {"age": 75, "pmi": 8.0, "rin": 7.0},
            {"age": 78, "pmi": 9.0, "rin": 7.2},
            {"age": 80, "pmi": 7.5, "rin": 6.8},
            {"age": 77, "pmi": 8.5, "rin": 7.1},
        ]
        controls = [
            {"age": 76, "pmi": 8.2, "rin": 7.1},
            {"age": 79, "pmi": 8.8, "rin": 6.9},
            {"age": 78, "pmi": 7.8, "rin": 7.3},
            {"age": 75, "pmi": 8.3, "rin": 7.0},
        ]
        
        report = run_balance_tests(cases, controls)
        
        assert report.n_cases == 4
        assert report.n_controls == 4
        # With similar distributions, should be balanced
        assert report.age_pvalue > 0.05
        assert report.pmi_pvalue > 0.05
        assert report.rin_pvalue > 0.05

    def test_unbalanced_age(self):
        """Test detection of age imbalance."""
        cases = [
            {"age": 80, "pmi": 8.0, "rin": 7.0},
            {"age": 82, "pmi": 9.0, "rin": 7.2},
            {"age": 85, "pmi": 7.5, "rin": 6.8},
            {"age": 83, "pmi": 8.5, "rin": 7.1},
        ]
        controls = [
            {"age": 60, "pmi": 8.2, "rin": 7.1},  # Much younger
            {"age": 62, "pmi": 8.8, "rin": 6.9},
            {"age": 58, "pmi": 7.8, "rin": 7.3},
            {"age": 61, "pmi": 8.3, "rin": 7.0},
        ]
        
        report = run_balance_tests(cases, controls)
        
        assert report.age_pvalue < 0.05  # Significantly different
        assert not report.is_balanced

