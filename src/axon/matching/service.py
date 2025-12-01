"""High-level matching service for the chat agent."""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from axon.matching.matcher import SampleMatcher, MatchResult, CandidateSample
from axon.matching.candidates import (
    find_case_candidates,
    find_control_candidates,
    get_available_counts,
)


@dataclass
class MatchingCriteria:
    """Criteria gathered from conversation for matching."""
    
    # Case criteria
    diagnosis: str | None = None
    n_cases: int = 0
    
    # Control criteria
    needs_controls: bool = False
    n_controls: int = 0
    age_matched: bool = True
    
    # Shared criteria
    min_age: int | None = None
    max_age: int | None = None
    brain_region: str | None = None
    min_rin: float | None = None
    max_pmi: float | None = None
    
    # Exclusions
    exclude_co_pathologies: bool = False
    exclude_controls_with_pathology: bool = True
    
    # Matching settings
    exact_sex_match: bool = True
    control_ratio: int = 1  # 1:1 by default
    
    def is_complete_for_matching(self) -> bool:
        """Check if we have enough criteria to attempt matching."""
        has_cases = self.diagnosis is not None and self.n_cases > 0
        
        if not self.needs_controls:
            return has_cases
        
        return has_cases and self.n_controls > 0
    
    def to_summary(self) -> str:
        """Generate a summary of the criteria."""
        lines = ["**Current Criteria:**"]
        
        if self.diagnosis:
            lines.append(f"- Diagnosis: {self.diagnosis}")
        if self.n_cases:
            lines.append(f"- Number of cases: {self.n_cases}")
        if self.needs_controls:
            lines.append(f"- Controls needed: {self.n_controls}")
            lines.append(f"- Age-matched: {'Yes' if self.age_matched else 'No'}")
        if self.brain_region:
            lines.append(f"- Brain region: {self.brain_region}")
        if self.min_rin:
            lines.append(f"- Minimum RIN: {self.min_rin}")
        if self.max_pmi:
            lines.append(f"- Maximum PMI: {self.max_pmi} hours")
        if self.exclude_co_pathologies:
            lines.append("- Excluding co-pathologies")
        
        return "\n".join(lines)


class MatchingService:
    """Service for finding matched case-control samples."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the matching service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.matcher = SampleMatcher()
    
    async def find_matched_samples(
        self,
        criteria: MatchingCriteria,
    ) -> MatchResult:
        """Find matched case and control samples based on criteria.
        
        Args:
            criteria: Matching criteria from conversation
            
        Returns:
            MatchResult with selected samples and statistics
        """
        # Find case candidates
        case_candidates = await find_case_candidates(
            self.session,
            diagnosis=criteria.diagnosis,
            min_age=criteria.min_age,
            max_age=criteria.max_age,
            brain_region=criteria.brain_region,
            min_rin=criteria.min_rin,
            max_pmi=criteria.max_pmi,
            exclude_co_pathologies=criteria.exclude_co_pathologies,
        )
        
        if not case_candidates:
            return MatchResult(
                cases=[],
                controls=[],
                statistical_report=None,
                success=False,
                message=f"No {criteria.diagnosis} samples found matching your criteria",
                suggestions=[
                    "Relax RIN or PMI constraints",
                    "Expand age range",
                    "Try a different brain region",
                ],
            )
        
        if len(case_candidates) < criteria.n_cases:
            return MatchResult(
                cases=[],
                controls=[],
                statistical_report=None,
                success=False,
                message=f"Only {len(case_candidates)} {criteria.diagnosis} samples available, but {criteria.n_cases} requested",
                suggestions=[
                    f"Reduce number of cases to {len(case_candidates)} or fewer",
                    "Relax your criteria to find more samples",
                ],
            )
        
        # If no controls needed, just select cases
        if not criteria.needs_controls:
            selected_cases = case_candidates[:criteria.n_cases]
            return MatchResult(
                cases=selected_cases,
                controls=[],
                statistical_report=None,
                success=True,
                message=f"Found {len(selected_cases)} {criteria.diagnosis} samples",
            )
        
        # Find control candidates
        control_candidates = await find_control_candidates(
            self.session,
            min_age=criteria.min_age if criteria.age_matched else None,
            max_age=criteria.max_age if criteria.age_matched else None,
            brain_region=criteria.brain_region,
            min_rin=criteria.min_rin,
            max_pmi=criteria.max_pmi,
            exclude_pathology=criteria.exclude_controls_with_pathology,
        )
        
        if not control_candidates:
            return MatchResult(
                cases=[],
                controls=[],
                statistical_report=None,
                success=False,
                message="No control samples found matching your criteria",
                suggestions=[
                    "Relax age matching requirement",
                    "Allow controls with some pathology",
                    "Expand age or quality constraints",
                ],
            )
        
        # Run the matching algorithm
        result = self.matcher.find_matched_sets(
            cases=case_candidates[:criteria.n_cases * 2],  # Get more candidates for optimization
            controls=control_candidates,
            n_per_group=criteria.n_cases,
            control_ratio=criteria.control_ratio,
            exact_sex_match=criteria.exact_sex_match,
        )
        
        return result
    
    async def check_availability(
        self,
        diagnosis: str | None = None,
        is_control: bool = False,
    ) -> dict[str, Any]:
        """Check how many samples are available.
        
        Args:
            diagnosis: Diagnosis to check (for cases)
            is_control: Whether checking control availability
            
        Returns:
            Dict with availability information
        """
        counts = await get_available_counts(
            self.session,
            diagnosis=diagnosis,
            is_control=is_control,
        )
        
        total = sum(counts.values())
        
        return {
            "total": total,
            "by_sex": counts,
            "diagnosis": diagnosis,
            "is_control": is_control,
        }
    
    async def get_matching_preview(
        self,
        criteria: MatchingCriteria,
    ) -> str:
        """Get a preview of what matching would produce.
        
        Args:
            criteria: Current matching criteria
            
        Returns:
            Formatted preview string
        """
        # Check case availability
        case_avail = await self.check_availability(
            diagnosis=criteria.diagnosis,
            is_control=False,
        )
        
        lines = [
            f"**Available {criteria.diagnosis} samples:** {case_avail['total']}",
        ]
        
        if case_avail['by_sex']:
            for sex, count in case_avail['by_sex'].items():
                lines.append(f"  - {sex}: {count}")
        
        if criteria.needs_controls:
            ctrl_avail = await self.check_availability(is_control=True)
            lines.append(f"\n**Available control samples:** {ctrl_avail['total']}")
            
            if ctrl_avail['by_sex']:
                for sex, count in ctrl_avail['by_sex'].items():
                    lines.append(f"  - {sex}: {count}")
        
        # Check if request is feasible
        if case_avail['total'] < criteria.n_cases:
            lines.append(f"\n⚠️ Only {case_avail['total']} cases available, but {criteria.n_cases} requested")
        
        return "\n".join(lines)


def format_match_result_for_agent(result: MatchResult) -> str:
    """Format a MatchResult for display by the agent.
    
    Args:
        result: The matching result
        
    Returns:
        Formatted string for agent response
    """
    if not result.success:
        lines = [f"❌ **Matching Failed**\n\n{result.message}"]
        
        if result.suggestions:
            lines.append("\n**Suggestions:**")
            for s in result.suggestions:
                lines.append(f"- {s}")
        
        return "\n".join(lines)
    
    lines = [
        f"✅ **Successfully Matched Samples**\n",
        f"- Cases: {len(result.cases)}",
        f"- Controls: {len(result.controls)}",
    ]
    
    if result.statistical_report:
        lines.append("\n" + result.statistical_report.to_summary())
    
    # Show sample IDs
    if result.cases:
        lines.append("\n**Case Sample IDs:**")
        case_ids = [f"{c.external_id} ({c.source_bank})" for c in result.cases[:10]]
        lines.append(", ".join(case_ids))
        if len(result.cases) > 10:
            lines.append(f"... and {len(result.cases) - 10} more")
    
    if result.controls:
        lines.append("\n**Control Sample IDs:**")
        ctrl_ids = [f"{c.external_id} ({c.source_bank})" for c in result.controls[:10]]
        lines.append(", ".join(ctrl_ids))
        if len(result.controls) > 10:
            lines.append(f"... and {len(result.controls) - 10} more")
    
    return "\n".join(lines)

