"""Sample matching algorithm for case-control studies."""

from dataclasses import dataclass, field
from typing import Any
import math
import random

from axon.matching.statistics import StatisticalReport, run_balance_tests


@dataclass
class CandidateSample:
    """A candidate sample for matching."""
    
    id: str
    age: int | None = None
    pmi: float | None = None
    rin: float | None = None
    sex: str | None = None
    diagnosis: str | None = None
    
    # Additional metadata
    source_bank: str | None = None
    brain_region: str | None = None
    external_id: str | None = None
    
    @property
    def is_valid(self) -> bool:
        """Check if sample has all required data for matching."""
        return (
            self.age is not None and
            self.pmi is not None and
            self.rin is not None
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for statistical functions."""
        return {
            "id": self.id,
            "age": self.age,
            "pmi": self.pmi,
            "rin": self.rin,
            "sex": self.sex,
            "diagnosis": self.diagnosis,
        }


@dataclass
class MatchResult:
    """Result of a matching operation."""
    
    cases: list[CandidateSample]
    controls: list[CandidateSample]
    statistical_report: StatisticalReport | None
    success: bool
    message: str
    suggestions: list[str] = field(default_factory=list)
    
    def to_summary(self) -> str:
        """Generate a summary of the match result."""
        lines = [f"Match Result: {'✅ Success' if self.success else '❌ Failed'}"]
        lines.append(self.message)
        lines.append(f"Cases selected: {len(self.cases)}")
        lines.append(f"Controls selected: {len(self.controls)}")
        
        if self.statistical_report:
            lines.append("")
            lines.append(self.statistical_report.to_summary())
        
        if self.suggestions:
            lines.append("")
            lines.append("Suggestions:")
            for s in self.suggestions:
                lines.append(f"  • {s}")
        
        return "\n".join(lines)


def calculate_distance(
    sample1: CandidateSample,
    sample2: CandidateSample,
    age_weight: float = 1.0,
    pmi_weight: float = 1.0,
    rin_weight: float = 1.0,
    age_scale: float = 10.0,  # Normalize: 10 years difference = 1 unit
    pmi_scale: float = 5.0,   # Normalize: 5 hours difference = 1 unit
    rin_scale: float = 2.0,   # Normalize: 2 RIN difference = 1 unit
) -> float:
    """Calculate distance between two samples based on matching variables.
    
    Uses weighted Euclidean distance with normalization.
    
    Args:
        sample1: First sample
        sample2: Second sample
        age_weight: Weight for age difference
        pmi_weight: Weight for PMI difference
        rin_weight: Weight for RIN difference
        age_scale: Scaling factor for age normalization
        pmi_scale: Scaling factor for PMI normalization
        rin_scale: Scaling factor for RIN normalization
        
    Returns:
        Distance score (lower is better match)
    """
    if not sample1.is_valid or not sample2.is_valid:
        return float('inf')
    
    # Calculate normalized differences
    age_diff = abs(sample1.age - sample2.age) / age_scale
    pmi_diff = abs(sample1.pmi - sample2.pmi) / pmi_scale
    rin_diff = abs(sample1.rin - sample2.rin) / rin_scale
    
    # Weighted Euclidean distance
    distance = math.sqrt(
        age_weight * (age_diff ** 2) +
        pmi_weight * (pmi_diff ** 2) +
        rin_weight * (rin_diff ** 2)
    )
    
    return distance


class SampleMatcher:
    """Optimal matching algorithm for case-control studies.
    
    Finds the best set of controls to match cases while ensuring
    no statistically significant difference in age, PMI, or RIN.
    """
    
    def __init__(
        self,
        p_threshold: float = 0.05,
        max_iterations: int = 1000,
        age_weight: float = 1.0,
        pmi_weight: float = 1.0,
        rin_weight: float = 1.0,
    ):
        """Initialize the matcher.
        
        Args:
            p_threshold: Significance threshold for balance tests
            max_iterations: Maximum optimization iterations
            age_weight: Weight for age in distance calculation
            pmi_weight: Weight for PMI in distance calculation
            rin_weight: Weight for RIN in distance calculation
        """
        self.p_threshold = p_threshold
        self.max_iterations = max_iterations
        self.age_weight = age_weight
        self.pmi_weight = pmi_weight
        self.rin_weight = rin_weight
    
    def filter_valid_candidates(
        self, candidates: list[CandidateSample]
    ) -> list[CandidateSample]:
        """Filter candidates to only those with complete data."""
        return [c for c in candidates if c.is_valid]
    
    def group_by_sex(
        self, candidates: list[CandidateSample]
    ) -> dict[str, list[CandidateSample]]:
        """Group candidates by sex."""
        groups: dict[str, list[CandidateSample]] = {}
        for c in candidates:
            sex = (c.sex or "unknown").lower()
            if sex not in groups:
                groups[sex] = []
            groups[sex].append(c)
        return groups
    
    def find_matched_sets(
        self,
        cases: list[CandidateSample],
        controls: list[CandidateSample],
        n_per_group: int | None = None,
        control_ratio: int = 1,
        exact_sex_match: bool = True,
    ) -> MatchResult:
        """Find optimally matched case and control sets.
        
        Args:
            cases: Available case samples
            controls: Available control samples
            n_per_group: Number of cases to select (None = use all valid cases)
            control_ratio: Number of controls per case (default 1:1)
            exact_sex_match: Whether to enforce exact sex matching
            
        Returns:
            MatchResult with selected samples and statistics
        """
        # Filter to valid candidates only
        valid_cases = self.filter_valid_candidates(cases)
        valid_controls = self.filter_valid_candidates(controls)
        
        if not valid_cases:
            return MatchResult(
                cases=[],
                controls=[],
                statistical_report=None,
                success=False,
                message="No valid cases available (missing age, PMI, or RIN data)",
            )
        
        if not valid_controls:
            return MatchResult(
                cases=[],
                controls=[],
                statistical_report=None,
                success=False,
                message="No valid controls available (missing age, PMI, or RIN data)",
            )
        
        # Determine number of cases to use
        n_cases = n_per_group or len(valid_cases)
        n_controls_needed = n_cases * control_ratio
        
        if exact_sex_match:
            return self._match_with_sex_balance(
                valid_cases, valid_controls, n_cases, control_ratio
            )
        else:
            return self._match_without_sex_constraint(
                valid_cases, valid_controls, n_cases, control_ratio
            )
    
    def _match_with_sex_balance(
        self,
        cases: list[CandidateSample],
        controls: list[CandidateSample],
        n_cases: int,
        control_ratio: int,
    ) -> MatchResult:
        """Match with exact sex balance between groups."""
        case_by_sex = self.group_by_sex(cases)
        control_by_sex = self.group_by_sex(controls)
        
        # Determine sex distribution from cases
        selected_cases: list[CandidateSample] = []
        selected_controls: list[CandidateSample] = []
        
        # If we need fewer cases than available, select best subset
        if n_cases < len(cases):
            # For now, take first n_cases maintaining sex ratio
            # TODO: Optimize case selection too
            cases = cases[:n_cases]
            case_by_sex = self.group_by_sex(cases)
        
        # Match each sex group separately
        for sex, sex_cases in case_by_sex.items():
            sex_controls = control_by_sex.get(sex, [])
            n_controls_needed = len(sex_cases) * control_ratio
            
            if len(sex_controls) < n_controls_needed:
                return MatchResult(
                    cases=[],
                    controls=[],
                    statistical_report=None,
                    success=False,
                    message=f"Not enough {sex} controls: need {n_controls_needed}, have {len(sex_controls)}",
                    suggestions=[
                        f"Reduce number of {sex} cases",
                        "Relax sex matching requirement",
                        f"Find more {sex} control samples",
                    ],
                )
            
            # Select best matching controls for this sex group
            matched_controls = self._select_best_controls(
                sex_cases, sex_controls, n_controls_needed
            )
            
            selected_cases.extend(sex_cases)
            selected_controls.extend(matched_controls)
        
        # Validate the match
        report = self._validate_match(selected_cases, selected_controls)
        
        if report.is_balanced:
            return MatchResult(
                cases=selected_cases,
                controls=selected_controls,
                statistical_report=report,
                success=True,
                message=f"Successfully matched {len(selected_cases)} cases with {len(selected_controls)} controls",
            )
        else:
            # Try to optimize
            optimized_cases, optimized_controls = self._optimize_selection(
                selected_cases, selected_controls, case_by_sex, control_by_sex, control_ratio
            )
            
            report = self._validate_match(optimized_cases, optimized_controls)
            
            if report.is_balanced:
                return MatchResult(
                    cases=optimized_cases,
                    controls=optimized_controls,
                    statistical_report=report,
                    success=True,
                    message=f"Successfully matched {len(optimized_cases)} cases with {len(optimized_controls)} controls (after optimization)",
                )
            else:
                imbalanced = ", ".join(report.imbalanced_variables)
                return MatchResult(
                    cases=optimized_cases,
                    controls=optimized_controls,
                    statistical_report=report,
                    success=False,
                    message=f"Could not achieve statistical balance on: {imbalanced}",
                    suggestions=self._generate_suggestions(report, selected_cases, selected_controls),
                )
    
    def _match_without_sex_constraint(
        self,
        cases: list[CandidateSample],
        controls: list[CandidateSample],
        n_cases: int,
        control_ratio: int,
    ) -> MatchResult:
        """Match without sex constraint."""
        # Limit cases if needed
        if n_cases < len(cases):
            cases = cases[:n_cases]
        
        n_controls_needed = len(cases) * control_ratio
        
        if len(controls) < n_controls_needed:
            return MatchResult(
                cases=[],
                controls=[],
                statistical_report=None,
                success=False,
                message=f"Not enough controls: need {n_controls_needed}, have {len(controls)}",
                suggestions=[
                    "Reduce number of cases",
                    "Reduce control ratio",
                ],
            )
        
        # Select best matching controls
        selected_controls = self._select_best_controls(cases, controls, n_controls_needed)
        
        # Validate
        report = self._validate_match(cases, selected_controls)
        
        if report.is_balanced:
            return MatchResult(
                cases=cases,
                controls=selected_controls,
                statistical_report=report,
                success=True,
                message=f"Successfully matched {len(cases)} cases with {len(selected_controls)} controls",
            )
        else:
            imbalanced = ", ".join(report.imbalanced_variables)
            return MatchResult(
                cases=cases,
                controls=selected_controls,
                statistical_report=report,
                success=False,
                message=f"Could not achieve statistical balance on: {imbalanced}",
                suggestions=self._generate_suggestions(report, cases, selected_controls),
            )
    
    def _select_best_controls(
        self,
        cases: list[CandidateSample],
        available_controls: list[CandidateSample],
        n_controls: int,
    ) -> list[CandidateSample]:
        """Select the best matching controls using greedy distance minimization."""
        if len(available_controls) <= n_controls:
            return available_controls.copy()
        
        # Calculate average case profile
        avg_age = sum(c.age for c in cases) / len(cases)
        avg_pmi = sum(c.pmi for c in cases) / len(cases)
        avg_rin = sum(c.rin for c in cases) / len(cases)
        
        # Create a "target" sample representing ideal control
        target = CandidateSample(
            id="target",
            age=int(avg_age),
            pmi=avg_pmi,
            rin=avg_rin,
        )
        
        # Score all controls by distance to target
        scored_controls = []
        for ctrl in available_controls:
            dist = calculate_distance(
                target, ctrl,
                age_weight=self.age_weight,
                pmi_weight=self.pmi_weight,
                rin_weight=self.rin_weight,
            )
            scored_controls.append((dist, ctrl))
        
        # Sort by distance and take the best n_controls
        scored_controls.sort(key=lambda x: x[0])
        selected = [ctrl for _, ctrl in scored_controls[:n_controls]]
        
        return selected
    
    def _validate_match(
        self,
        cases: list[CandidateSample],
        controls: list[CandidateSample],
    ) -> StatisticalReport:
        """Run statistical validation on matched groups."""
        case_dicts = [c.to_dict() for c in cases]
        control_dicts = [c.to_dict() for c in controls]
        
        return run_balance_tests(case_dicts, control_dicts, self.p_threshold)
    
    def _optimize_selection(
        self,
        cases: list[CandidateSample],
        controls: list[CandidateSample],
        case_by_sex: dict[str, list[CandidateSample]],
        control_by_sex: dict[str, list[CandidateSample]],
        control_ratio: int,
    ) -> tuple[list[CandidateSample], list[CandidateSample]]:
        """Try to optimize selection to achieve balance.
        
        Uses iterative replacement to improve balance.
        """
        best_cases = cases.copy()
        best_controls = controls.copy()
        best_report = self._validate_match(best_cases, best_controls)
        
        # Get all available controls by sex for swapping
        used_control_ids = {c.id for c in controls}
        
        for iteration in range(min(self.max_iterations, 100)):
            improved = False
            
            for sex, sex_controls_in_use in self._group_controls_by_sex(best_controls).items():
                available = [c for c in control_by_sex.get(sex, []) if c.id not in used_control_ids]
                
                if not available:
                    continue
                
                # Try swapping each control with available alternatives
                for i, ctrl in enumerate(sex_controls_in_use):
                    for alt in available:
                        # Try the swap
                        test_controls = best_controls.copy()
                        ctrl_idx = test_controls.index(ctrl)
                        test_controls[ctrl_idx] = alt
                        
                        test_report = self._validate_match(best_cases, test_controls)
                        
                        # Check if this is better
                        if self._is_better_match(test_report, best_report):
                            best_controls = test_controls
                            best_report = test_report
                            used_control_ids.remove(ctrl.id)
                            used_control_ids.add(alt.id)
                            improved = True
                            break
                    
                    if improved:
                        break
                
                if improved:
                    break
            
            if not improved or best_report.is_balanced:
                break
        
        return best_cases, best_controls
    
    def _group_controls_by_sex(
        self, controls: list[CandidateSample]
    ) -> dict[str, list[CandidateSample]]:
        """Group controls by sex."""
        groups: dict[str, list[CandidateSample]] = {}
        for c in controls:
            sex = (c.sex or "unknown").lower()
            if sex not in groups:
                groups[sex] = []
            groups[sex].append(c)
        return groups
    
    def _is_better_match(
        self, new_report: StatisticalReport, old_report: StatisticalReport
    ) -> bool:
        """Check if new match is better than old match."""
        if new_report.is_balanced and not old_report.is_balanced:
            return True
        
        if new_report.is_balanced == old_report.is_balanced:
            # Compare sum of p-values (higher is better)
            new_sum = sum(p for p in [new_report.age_pvalue, new_report.pmi_pvalue, new_report.rin_pvalue] if p)
            old_sum = sum(p for p in [old_report.age_pvalue, old_report.pmi_pvalue, old_report.rin_pvalue] if p)
            return new_sum > old_sum
        
        return False
    
    def _generate_suggestions(
        self,
        report: StatisticalReport,
        cases: list[CandidateSample],
        controls: list[CandidateSample],
    ) -> list[str]:
        """Generate suggestions for achieving balance."""
        suggestions = []
        
        if "age" in report.imbalanced_variables:
            age_diff = abs((report.case_age_mean or 0) - (report.control_age_mean or 0))
            suggestions.append(f"Age differs by ~{age_diff:.1f} years. Consider expanding age range for controls.")
        
        if "PMI" in report.imbalanced_variables:
            pmi_diff = abs((report.case_pmi_mean or 0) - (report.control_pmi_mean or 0))
            suggestions.append(f"PMI differs by ~{pmi_diff:.1f} hours. Consider relaxing PMI constraints.")
        
        if "RIN" in report.imbalanced_variables:
            rin_diff = abs((report.case_rin_mean or 0) - (report.control_rin_mean or 0))
            suggestions.append(f"RIN differs by ~{rin_diff:.1f}. Consider accepting lower/higher RIN controls.")
        
        suggestions.append("Reduce sample size to find better-matched subset")
        
        return suggestions

