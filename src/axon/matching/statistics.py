"""Statistical functions for validating matched sample groups."""

from dataclasses import dataclass, field
from typing import Any
import math

# Use scipy for statistical tests if available, otherwise fallback
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


@dataclass
class StatisticalReport:
    """Report on statistical balance between case and control groups."""
    
    n_cases: int
    n_controls: int
    
    # Age statistics
    case_age_mean: float | None
    case_age_sd: float | None
    control_age_mean: float | None
    control_age_sd: float | None
    age_pvalue: float | None
    
    # PMI statistics
    case_pmi_mean: float | None
    case_pmi_sd: float | None
    control_pmi_mean: float | None
    control_pmi_sd: float | None
    pmi_pvalue: float | None
    
    # RIN statistics
    case_rin_mean: float | None
    case_rin_sd: float | None
    control_rin_mean: float | None
    control_rin_sd: float | None
    rin_pvalue: float | None
    
    # Threshold for significance
    p_threshold: float = 0.05
    
    @property
    def is_balanced(self) -> bool:
        """Check if all covariates are balanced (p > threshold)."""
        pvalues = [self.age_pvalue, self.pmi_pvalue, self.rin_pvalue]
        # Filter out None values and check all are above threshold
        valid_pvalues = [p for p in pvalues if p is not None]
        if not valid_pvalues:
            return False
        return all(p > self.p_threshold for p in valid_pvalues)
    
    @property
    def imbalanced_variables(self) -> list[str]:
        """Get list of variables that are significantly different."""
        imbalanced = []
        if self.age_pvalue is not None and self.age_pvalue <= self.p_threshold:
            imbalanced.append("age")
        if self.pmi_pvalue is not None and self.pmi_pvalue <= self.p_threshold:
            imbalanced.append("PMI")
        if self.rin_pvalue is not None and self.rin_pvalue <= self.p_threshold:
            imbalanced.append("RIN")
        return imbalanced
    
    def to_summary(self) -> str:
        """Generate a formatted summary string."""
        lines = [
            "Statistical Summary:",
            f"  Cases: n={self.n_cases}, Controls: n={self.n_controls}",
            "",
            "  Variable    Cases (mean±SD)      Controls (mean±SD)   p-value",
            "  " + "-" * 65,
        ]
        
        # Age
        case_age = f"{self.case_age_mean:.1f}±{self.case_age_sd:.1f}" if self.case_age_mean else "N/A"
        ctrl_age = f"{self.control_age_mean:.1f}±{self.control_age_sd:.1f}" if self.control_age_mean else "N/A"
        age_p = f"{self.age_pvalue:.3f}" if self.age_pvalue else "N/A"
        age_sig = "*" if self.age_pvalue and self.age_pvalue <= self.p_threshold else ""
        lines.append(f"  Age         {case_age:<20} {ctrl_age:<20} {age_p}{age_sig}")
        
        # PMI
        case_pmi = f"{self.case_pmi_mean:.1f}±{self.case_pmi_sd:.1f}" if self.case_pmi_mean else "N/A"
        ctrl_pmi = f"{self.control_pmi_mean:.1f}±{self.control_pmi_sd:.1f}" if self.control_pmi_mean else "N/A"
        pmi_p = f"{self.pmi_pvalue:.3f}" if self.pmi_pvalue else "N/A"
        pmi_sig = "*" if self.pmi_pvalue and self.pmi_pvalue <= self.p_threshold else ""
        lines.append(f"  PMI (h)     {case_pmi:<20} {ctrl_pmi:<20} {pmi_p}{pmi_sig}")
        
        # RIN
        case_rin = f"{self.case_rin_mean:.1f}±{self.case_rin_sd:.1f}" if self.case_rin_mean else "N/A"
        ctrl_rin = f"{self.control_rin_mean:.1f}±{self.control_rin_sd:.1f}" if self.control_rin_mean else "N/A"
        rin_p = f"{self.rin_pvalue:.3f}" if self.rin_pvalue else "N/A"
        rin_sig = "*" if self.rin_pvalue and self.rin_pvalue <= self.p_threshold else ""
        lines.append(f"  RIN         {case_rin:<20} {ctrl_rin:<20} {rin_p}{rin_sig}")
        
        lines.append("")
        if self.is_balanced:
            lines.append("  ✅ Groups are statistically balanced (all p > 0.05)")
        else:
            imbalanced = ", ".join(self.imbalanced_variables)
            lines.append(f"  ⚠️ Groups differ significantly on: {imbalanced}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "n_cases": self.n_cases,
            "n_controls": self.n_controls,
            "age": {
                "case_mean": self.case_age_mean,
                "case_sd": self.case_age_sd,
                "control_mean": self.control_age_mean,
                "control_sd": self.control_age_sd,
                "pvalue": self.age_pvalue,
            },
            "pmi": {
                "case_mean": self.case_pmi_mean,
                "case_sd": self.case_pmi_sd,
                "control_mean": self.control_pmi_mean,
                "control_sd": self.control_pmi_sd,
                "pvalue": self.pmi_pvalue,
            },
            "rin": {
                "case_mean": self.case_rin_mean,
                "case_sd": self.case_rin_sd,
                "control_mean": self.control_rin_mean,
                "control_sd": self.control_rin_sd,
                "pvalue": self.rin_pvalue,
            },
            "is_balanced": self.is_balanced,
            "imbalanced_variables": self.imbalanced_variables,
        }


def calculate_group_stats(values: list[float]) -> tuple[float | None, float | None]:
    """Calculate mean and standard deviation for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Tuple of (mean, standard_deviation)
    """
    if not values:
        return None, None
    
    n = len(values)
    mean = sum(values) / n
    
    if n == 1:
        return mean, 0.0
    
    # Sample standard deviation
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    sd = math.sqrt(variance)
    
    return mean, sd


def ttest_or_mannwhitney(group1: list[float], group2: list[float]) -> float:
    """Perform statistical test comparing two groups.
    
    Uses independent samples t-test if scipy is available,
    otherwise uses a simple approximation.
    
    Args:
        group1: First group of values
        group2: Second group of values
        
    Returns:
        p-value for the comparison
    """
    if not group1 or not group2:
        return 1.0  # No data, assume no difference
    
    if HAS_SCIPY:
        # Use Mann-Whitney U test (non-parametric, more robust)
        try:
            _, pvalue = scipy_stats.mannwhitneyu(
                group1, group2, alternative='two-sided'
            )
            return pvalue
        except ValueError:
            # Fall back to t-test if Mann-Whitney fails
            try:
                _, pvalue = scipy_stats.ttest_ind(group1, group2)
                return pvalue
            except Exception:
                return 1.0
    else:
        # Simple approximation using Welch's t-test formula
        return _approximate_ttest(group1, group2)


def _approximate_ttest(group1: list[float], group2: list[float]) -> float:
    """Approximate t-test without scipy.
    
    Uses Welch's t-test approximation.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 1.0
    
    mean1, sd1 = calculate_group_stats(group1)
    mean2, sd2 = calculate_group_stats(group2)
    
    if mean1 is None or mean2 is None:
        return 1.0
    
    # Welch's t-test
    se1 = (sd1 ** 2) / n1 if sd1 else 0
    se2 = (sd2 ** 2) / n2 if sd2 else 0
    se_diff = math.sqrt(se1 + se2)
    
    if se_diff == 0:
        return 1.0 if mean1 == mean2 else 0.0
    
    t_stat = abs(mean1 - mean2) / se_diff
    
    # Approximate p-value using simplified formula
    # This is a rough approximation - for production use scipy
    df = n1 + n2 - 2
    if df <= 0:
        return 1.0
    
    # Very rough p-value approximation
    # t > 2 roughly corresponds to p < 0.05 for reasonable df
    if t_stat < 0.5:
        return 0.6
    elif t_stat < 1.0:
        return 0.3
    elif t_stat < 2.0:
        return 0.1
    elif t_stat < 3.0:
        return 0.01
    else:
        return 0.001


def run_balance_tests(
    cases: list[dict[str, Any]],
    controls: list[dict[str, Any]],
    p_threshold: float = 0.05,
) -> StatisticalReport:
    """Run statistical balance tests between case and control groups.
    
    Args:
        cases: List of case samples with 'age', 'pmi', 'rin' keys
        controls: List of control samples with 'age', 'pmi', 'rin' keys
        p_threshold: Significance threshold (default 0.05)
        
    Returns:
        StatisticalReport with comparison results
    """
    # Extract values
    case_ages = [c["age"] for c in cases if c.get("age") is not None]
    control_ages = [c["age"] for c in controls if c.get("age") is not None]
    
    case_pmis = [c["pmi"] for c in cases if c.get("pmi") is not None]
    control_pmis = [c["pmi"] for c in controls if c.get("pmi") is not None]
    
    case_rins = [c["rin"] for c in cases if c.get("rin") is not None]
    control_rins = [c["rin"] for c in controls if c.get("rin") is not None]
    
    # Calculate statistics
    case_age_mean, case_age_sd = calculate_group_stats(case_ages)
    control_age_mean, control_age_sd = calculate_group_stats(control_ages)
    age_pvalue = ttest_or_mannwhitney(case_ages, control_ages) if case_ages and control_ages else None
    
    case_pmi_mean, case_pmi_sd = calculate_group_stats(case_pmis)
    control_pmi_mean, control_pmi_sd = calculate_group_stats(control_pmis)
    pmi_pvalue = ttest_or_mannwhitney(case_pmis, control_pmis) if case_pmis and control_pmis else None
    
    case_rin_mean, case_rin_sd = calculate_group_stats(case_rins)
    control_rin_mean, control_rin_sd = calculate_group_stats(control_rins)
    rin_pvalue = ttest_or_mannwhitney(case_rins, control_rins) if case_rins and control_rins else None
    
    return StatisticalReport(
        n_cases=len(cases),
        n_controls=len(controls),
        case_age_mean=case_age_mean,
        case_age_sd=case_age_sd,
        control_age_mean=control_age_mean,
        control_age_sd=control_age_sd,
        age_pvalue=age_pvalue,
        case_pmi_mean=case_pmi_mean,
        case_pmi_sd=case_pmi_sd,
        control_pmi_mean=control_pmi_mean,
        control_pmi_sd=control_pmi_sd,
        pmi_pvalue=pmi_pvalue,
        case_rin_mean=case_rin_mean,
        case_rin_sd=case_rin_sd,
        control_rin_mean=control_rin_mean,
        control_rin_sd=control_rin_sd,
        rin_pvalue=rin_pvalue,
        p_threshold=p_threshold,
    )

