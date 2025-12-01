"""Database queries to find candidate samples for matching."""

from typing import Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import Sample
from axon.matching.matcher import CandidateSample


async def find_case_candidates(
    session: AsyncSession,
    diagnosis: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    sex: str | None = None,
    brain_region: str | None = None,
    min_rin: float | None = None,
    max_pmi: float | None = None,
    exclude_co_pathologies: bool = False,
    source_bank: str | None = None,
    limit: int = 500,
) -> list[CandidateSample]:
    """Find candidate case samples matching the given criteria.
    
    Args:
        session: Database session
        diagnosis: Primary diagnosis to match (e.g., "Alzheimer")
        min_age: Minimum donor age
        max_age: Maximum donor age
        sex: Donor sex filter ("male" or "female")
        brain_region: Required brain region
        min_rin: Minimum RIN score
        max_pmi: Maximum postmortem interval in hours
        exclude_co_pathologies: Whether to exclude samples with co-pathologies
        source_bank: Filter by source bank
        limit: Maximum candidates to return
        
    Returns:
        List of CandidateSample objects
    """
    query = select(Sample).where(
        # Must have required matching fields
        Sample.donor_age.isnot(None),
        Sample.postmortem_interval_hours.isnot(None),
        Sample.rin_score.isnot(None),
    )
    
    # Apply filters
    if diagnosis:
        query = query.where(Sample.primary_diagnosis.ilike(f"%{diagnosis}%"))
    
    if min_age is not None:
        query = query.where(Sample.donor_age >= min_age)
    
    if max_age is not None:
        query = query.where(Sample.donor_age <= max_age)
    
    if sex:
        query = query.where(Sample.donor_sex.ilike(f"%{sex}%"))
    
    if brain_region:
        query = query.where(Sample.brain_region.ilike(f"%{brain_region}%"))
    
    if min_rin is not None:
        query = query.where(Sample.rin_score >= min_rin)
    
    if max_pmi is not None:
        query = query.where(Sample.postmortem_interval_hours <= max_pmi)
    
    if source_bank:
        query = query.where(Sample.source_bank.ilike(f"%{source_bank}%"))
    
    # TODO: Implement co-pathology exclusion based on extended_data
    
    query = query.limit(limit)
    
    result = await session.execute(query)
    samples = result.scalars().all()
    
    return [_sample_to_candidate(s) for s in samples]


async def find_control_candidates(
    session: AsyncSession,
    min_age: int | None = None,
    max_age: int | None = None,
    sex: str | None = None,
    brain_region: str | None = None,
    min_rin: float | None = None,
    max_pmi: float | None = None,
    exclude_pathology: bool = True,
    source_bank: str | None = None,
    limit: int = 1000,
) -> list[CandidateSample]:
    """Find candidate control samples (no neurodegenerative diagnosis).
    
    Args:
        session: Database session
        min_age: Minimum donor age
        max_age: Maximum donor age
        sex: Donor sex filter ("male" or "female")
        brain_region: Required brain region
        min_rin: Minimum RIN score
        max_pmi: Maximum postmortem interval in hours
        exclude_pathology: Whether to exclude samples with any pathology
        source_bank: Filter by source bank
        limit: Maximum candidates to return
        
    Returns:
        List of CandidateSample objects
    """
    query = select(Sample).where(
        # Must have required matching fields
        Sample.donor_age.isnot(None),
        Sample.postmortem_interval_hours.isnot(None),
        Sample.rin_score.isnot(None),
    )
    
    # Control samples: look for "control", "normal", or no clinical diagnosis
    control_patterns = [
        Sample.primary_diagnosis.ilike("%control%"),
        Sample.primary_diagnosis.ilike("%normal%"),
        Sample.primary_diagnosis.ilike("%no clinical brain diagnosis%"),
        Sample.primary_diagnosis.ilike("%neurologically normal%"),
    ]
    
    if exclude_pathology:
        query = query.where(or_(*control_patterns))
    
    # Apply filters
    if min_age is not None:
        query = query.where(Sample.donor_age >= min_age)
    
    if max_age is not None:
        query = query.where(Sample.donor_age <= max_age)
    
    if sex:
        query = query.where(Sample.donor_sex.ilike(f"%{sex}%"))
    
    if brain_region:
        query = query.where(Sample.brain_region.ilike(f"%{brain_region}%"))
    
    if min_rin is not None:
        query = query.where(Sample.rin_score >= min_rin)
    
    if max_pmi is not None:
        query = query.where(Sample.postmortem_interval_hours <= max_pmi)
    
    if source_bank:
        query = query.where(Sample.source_bank.ilike(f"%{source_bank}%"))
    
    query = query.limit(limit)
    
    result = await session.execute(query)
    samples = result.scalars().all()
    
    return [_sample_to_candidate(s) for s in samples]


async def get_available_counts(
    session: AsyncSession,
    diagnosis: str | None = None,
    is_control: bool = False,
) -> dict[str, int]:
    """Get counts of available samples by sex.
    
    Args:
        session: Database session
        diagnosis: Filter by diagnosis (for cases)
        is_control: Whether to count control samples
        
    Returns:
        Dict with counts by sex
    """
    query = select(
        Sample.donor_sex,
        func.count(Sample.id).label("count")
    ).where(
        Sample.donor_age.isnot(None),
        Sample.postmortem_interval_hours.isnot(None),
        Sample.rin_score.isnot(None),
    )
    
    if is_control:
        query = query.where(or_(
            Sample.primary_diagnosis.ilike("%control%"),
            Sample.primary_diagnosis.ilike("%normal%"),
            Sample.primary_diagnosis.ilike("%no clinical brain diagnosis%"),
        ))
    elif diagnosis:
        query = query.where(Sample.primary_diagnosis.ilike(f"%{diagnosis}%"))
    
    query = query.group_by(Sample.donor_sex)
    
    result = await session.execute(query)
    
    counts = {}
    for row in result:
        sex = (row.donor_sex or "unknown").lower()
        counts[sex] = row.count
    
    return counts


def _sample_to_candidate(sample: Sample) -> CandidateSample:
    """Convert a Sample model to a CandidateSample."""
    return CandidateSample(
        id=sample.id,
        age=sample.donor_age,
        pmi=float(sample.postmortem_interval_hours) if sample.postmortem_interval_hours else None,
        rin=float(sample.rin_score) if sample.rin_score else None,
        sex=(sample.donor_sex or "").lower(),
        diagnosis=sample.primary_diagnosis,
        source_bank=sample.source_bank,
        brain_region=sample.brain_region,
        external_id=sample.external_id,
    )

