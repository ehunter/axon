"""Database query functions for aggregate statistics."""

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import Sample


async def get_sample_count_by_race(session: AsyncSession) -> dict[str, int]:
    """Get count of samples by donor race."""
    query = (
        select(Sample.donor_race, func.count(Sample.id).label("count"))
        .where(Sample.donor_race.isnot(None))
        .group_by(Sample.donor_race)
        .order_by(func.count(Sample.id).desc())
    )
    result = await session.execute(query)
    return {row.donor_race: row.count for row in result}


async def get_sample_count_by_diagnosis(session: AsyncSession, limit: int = 50) -> dict[str, int]:
    """Get count of samples by primary diagnosis."""
    query = (
        select(Sample.primary_diagnosis, func.count(Sample.id).label("count"))
        .where(Sample.primary_diagnosis.isnot(None))
        .group_by(Sample.primary_diagnosis)
        .order_by(func.count(Sample.id).desc())
        .limit(limit)
    )
    result = await session.execute(query)
    return {row.primary_diagnosis: row.count for row in result}


async def get_sample_count_by_source(session: AsyncSession) -> dict[str, int]:
    """Get count of samples by source bank."""
    query = (
        select(Sample.source_bank, func.count(Sample.id).label("count"))
        .group_by(Sample.source_bank)
        .order_by(func.count(Sample.id).desc())
    )
    result = await session.execute(query)
    return {row.source_bank: row.count for row in result}


async def get_sample_count_by_sex(session: AsyncSession) -> dict[str, int]:
    """Get count of samples by donor sex."""
    query = (
        select(Sample.donor_sex, func.count(Sample.id).label("count"))
        .where(Sample.donor_sex.isnot(None))
        .group_by(Sample.donor_sex)
        .order_by(func.count(Sample.id).desc())
    )
    result = await session.execute(query)
    return {row.donor_sex: row.count for row in result}


async def get_total_sample_count(session: AsyncSession) -> int:
    """Get total number of samples."""
    result = await session.execute(select(func.count(Sample.id)))
    return result.scalar() or 0


async def count_samples_with_filter(
    session: AsyncSession,
    race: str | None = None,
    sex: str | None = None,
    diagnosis: str | None = None,
    source_bank: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_rin: float | None = None,
    max_pmi: float | None = None,
    braak_stage: str | None = None,
) -> int:
    """Count samples matching specific filters."""
    query = select(func.count(Sample.id))
    
    if race:
        query = query.where(Sample.donor_race.ilike(f"%{race}%"))
    
    if sex:
        query = query.where(Sample.donor_sex.ilike(f"%{sex}%"))
    
    if diagnosis:
        query = query.where(Sample.primary_diagnosis.ilike(f"%{diagnosis}%"))
    
    if source_bank:
        query = query.where(Sample.source_bank.ilike(f"%{source_bank}%"))
    
    if min_age is not None:
        query = query.where(Sample.donor_age >= min_age)
    
    if max_age is not None:
        query = query.where(Sample.donor_age <= max_age)
    
    if min_rin is not None:
        query = query.where(Sample.rin_score >= min_rin)
    
    if max_pmi is not None:
        query = query.where(Sample.postmortem_interval_hours <= max_pmi)
    
    if braak_stage:
        # Search in extended_data JSON
        query = query.where(
            text("extended_data->'neuropathology_scores'->>'braak_nft_stage' ILIKE :braak")
        ).params(braak=f"%{braak_stage}%")
    
    result = await session.execute(query)
    return result.scalar() or 0


async def get_database_summary(session: AsyncSession) -> dict:
    """Get a comprehensive summary of the database."""
    total = await get_total_sample_count(session)
    by_source = await get_sample_count_by_source(session)
    by_race = await get_sample_count_by_race(session)
    by_sex = await get_sample_count_by_sex(session)
    by_diagnosis = await get_sample_count_by_diagnosis(session, limit=20)
    
    return {
        "total_samples": total,
        "by_source": by_source,
        "by_race": by_race,
        "by_sex": by_sex,
        "top_diagnoses": by_diagnosis,
    }


async def get_race_breakdown_detailed(session: AsyncSession) -> str:
    """Get a formatted breakdown of samples by race."""
    counts = await get_sample_count_by_race(session)
    total = sum(counts.values())
    
    lines = ["**Sample Counts by Donor Race:**\n"]
    for race, count in sorted(counts.items(), key=lambda x: -x[1]):
        pct = (count / total) * 100 if total > 0 else 0
        lines.append(f"- {race}: **{count:,}** ({pct:.1f}%)")
    
    lines.append(f"\n**Total with race data:** {total:,}")
    return "\n".join(lines)


async def get_sample_count_by_ethnicity(session: AsyncSession) -> dict[str, int]:
    """Get count of samples by donor ethnicity."""
    query = (
        select(Sample.donor_ethnicity, func.count(Sample.id).label("count"))
        .where(Sample.donor_ethnicity.isnot(None))
        .group_by(Sample.donor_ethnicity)
        .order_by(func.count(Sample.id).desc())
    )
    result = await session.execute(query)
    return {row.donor_ethnicity: row.count for row in result}


async def get_ethnicity_breakdown(session: AsyncSession) -> str:
    """Get a formatted breakdown of samples by ethnicity."""
    counts = await get_sample_count_by_ethnicity(session)
    total = sum(counts.values())
    
    lines = ["**Sample Counts by Donor Ethnicity:**\n"]
    for ethnicity, count in sorted(counts.items(), key=lambda x: -x[1]):
        pct = (count / total) * 100 if total > 0 else 0
        lines.append(f"- {ethnicity}: **{count:,}** ({pct:.1f}%)")
    
    lines.append(f"\n**Total with ethnicity data:** {total:,}")
    return "\n".join(lines)


async def count_samples_with_demographics(
    session: AsyncSession,
    sex: str | None = None,
    race: str | None = None,
    ethnicity: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
) -> int:
    """Count samples with specific demographic filters."""
    query = select(func.count(Sample.id))
    
    if sex:
        query = query.where(Sample.donor_sex.ilike(f"%{sex}%"))
    
    if race:
        query = query.where(Sample.donor_race.ilike(f"%{race}%"))
    
    if ethnicity:
        # Use exact match for Hispanic to avoid "Not Hispanic or Latino"
        if ethnicity.lower() == "hispanic":
            query = query.where(Sample.donor_ethnicity == "Hispanic or Latino")
        else:
            query = query.where(Sample.donor_ethnicity.ilike(f"%{ethnicity}%"))
    
    if min_age is not None:
        query = query.where(Sample.donor_age >= min_age)
    
    if max_age is not None:
        query = query.where(Sample.donor_age <= max_age)
    
    result = await session.execute(query)
    return result.scalar() or 0


async def get_diagnosis_breakdown(session: AsyncSession, search_term: str | None = None) -> str:
    """Get a formatted breakdown of samples by diagnosis."""
    if search_term:
        # Count samples matching a specific diagnosis
        count = await count_samples_with_filter(session, diagnosis=search_term)
        return f"**Samples matching '{search_term}':** {count:,}"
    else:
        counts = await get_sample_count_by_diagnosis(session, limit=20)
        lines = ["**Top 20 Diagnoses:**\n"]
        for diagnosis, count in counts.items():
            lines.append(f"- {diagnosis}: **{count:,}**")
        return "\n".join(lines)


async def get_neuropathology_by_demographics(
    session: AsyncSession,
    min_age: int | None = None,
    max_age: int | None = None,
    sex: str | None = None,
    race: str | None = None,
    ethnicity: str | None = None,
    limit: int = 10,
) -> dict[str, int]:
    """Get neuropathology diagnosis breakdown filtered by demographics."""
    query = (
        select(Sample.primary_diagnosis, func.count(Sample.id).label("count"))
        .where(Sample.primary_diagnosis.isnot(None))
    )
    
    if min_age is not None:
        query = query.where(Sample.donor_age >= min_age)
    
    if max_age is not None:
        query = query.where(Sample.donor_age <= max_age)
    
    if sex:
        query = query.where(Sample.donor_sex.ilike(f"%{sex}%"))
    
    if race:
        query = query.where(Sample.donor_race.ilike(f"%{race}%"))
    
    if ethnicity:
        # Use exact match to avoid matching "Not Hispanic or Latino" when searching for "Hispanic"
        if ethnicity.lower() == "hispanic":
            query = query.where(Sample.donor_ethnicity == "Hispanic or Latino")
        else:
            query = query.where(Sample.donor_ethnicity.ilike(f"%{ethnicity}%"))
    
    query = (
        query.group_by(Sample.primary_diagnosis)
        .order_by(func.count(Sample.id).desc())
        .limit(limit)
    )
    
    result = await session.execute(query)
    return {row.primary_diagnosis: row.count for row in result}


async def compare_demographics_neuropathology(
    session: AsyncSession,
    group1_filters: dict,
    group2_filters: dict,
    group1_label: str = "Group 1",
    group2_label: str = "Group 2",
    limit: int = 10,
) -> str:
    """Compare neuropathology between two demographic groups."""
    
    # Get counts for both groups
    group1_counts = await get_neuropathology_by_demographics(session, **group1_filters, limit=limit)
    group2_counts = await get_neuropathology_by_demographics(session, **group2_filters, limit=limit)
    
    group1_total = sum(group1_counts.values())
    group2_total = sum(group2_counts.values())
    
    lines = [f"**Neuropathology Comparison:**\n"]
    lines.append(f"**{group1_label}** (n={group1_total:,}):\n")
    
    for diagnosis, count in list(group1_counts.items())[:5]:
        pct = (count / group1_total * 100) if group1_total > 0 else 0
        lines.append(f"  - {diagnosis}: {count:,} ({pct:.1f}%)")
    
    lines.append(f"\n**{group2_label}** (n={group2_total:,}):\n")
    
    for diagnosis, count in list(group2_counts.items())[:5]:
        pct = (count / group2_total * 100) if group2_total > 0 else 0
        lines.append(f"  - {diagnosis}: {count:,} ({pct:.1f}%)")
    
    return "\n".join(lines)


async def get_complex_stats(
    session: AsyncSession,
    min_age: int | None = None,
    max_age: int | None = None,
    sex: str | None = None,
    race: str | None = None,
    ethnicity: str | None = None,
) -> str:
    """Get statistics for a specific demographic slice."""
    
    # Build filter description
    filters = []
    if min_age is not None:
        filters.append(f"age ≥ {min_age}")
    if max_age is not None:
        filters.append(f"age ≤ {max_age}")
    if sex:
        filters.append(f"sex: {sex}")
    if race:
        filters.append(f"race: {race}")
    if ethnicity:
        filters.append(f"ethnicity: {ethnicity}")
    
    filter_desc = ", ".join(filters) if filters else "all samples"
    
    # Get total count
    total = await count_samples_with_filter(
        session, 
        race=race,
        sex=sex,
        min_age=min_age,
        max_age=max_age,
    )
    
    # Get diagnosis breakdown
    diagnoses = await get_neuropathology_by_demographics(
        session,
        min_age=min_age,
        max_age=max_age,
        sex=sex,
        race=race,
        ethnicity=ethnicity,
        limit=10,
    )
    
    lines = [f"**Statistics for {filter_desc}:**\n"]
    lines.append(f"**Total samples:** {total:,}\n")
    lines.append("**Top diagnoses:**")
    
    for diagnosis, count in diagnoses.items():
        pct = (count / total * 100) if total > 0 else 0
        lines.append(f"  - {diagnosis}: {count:,} ({pct:.1f}%)")
    
    return "\n".join(lines)

