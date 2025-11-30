"""Sample API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from axon.api.dependencies import get_db
from axon.api.schemas import (
    DiagnosisCount,
    FiltersResponse,
    SampleListResponse,
    SampleResponse,
    SearchRequest,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
    SourceCount,
    StatsResponse,
)
from axon.config import get_settings
from axon.db.models import Sample

router = APIRouter(prefix="/samples", tags=["samples"])


@router.get("", response_model=SampleListResponse)
async def list_samples(
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    source_bank: str | None = None,
    diagnosis: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> SampleListResponse:
    """List samples with optional filters and pagination."""
    # Build query
    query = select(Sample)
    count_query = select(func.count(Sample.id))
    
    # Apply filters
    if source_bank:
        query = query.where(Sample.source_bank == source_bank)
        count_query = count_query.where(Sample.source_bank == source_bank)
    
    if diagnosis:
        query = query.where(Sample.primary_diagnosis.ilike(f"%{diagnosis}%"))
        count_query = count_query.where(Sample.primary_diagnosis.ilike(f"%{diagnosis}%"))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    samples = result.scalars().all()
    
    return SampleListResponse(
        items=[SampleResponse.model_validate(s) for s in samples],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    """Get sample statistics."""
    # Total count
    total_result = await db.execute(select(func.count(Sample.id)))
    total = total_result.scalar() or 0
    
    # By source
    source_query = (
        select(Sample.source_bank, func.count(Sample.id).label("count"))
        .group_by(Sample.source_bank)
        .order_by(func.count(Sample.id).desc())
    )
    source_result = await db.execute(source_query)
    by_source = [
        SourceCount(source_bank=row.source_bank, count=row.count)
        for row in source_result
    ]
    
    # By diagnosis (top 20)
    diagnosis_query = (
        select(Sample.primary_diagnosis, func.count(Sample.id).label("count"))
        .where(Sample.primary_diagnosis.isnot(None))
        .group_by(Sample.primary_diagnosis)
        .order_by(func.count(Sample.id).desc())
        .limit(20)
    )
    diagnosis_result = await db.execute(diagnosis_query)
    by_diagnosis = [
        DiagnosisCount(diagnosis=row.primary_diagnosis, count=row.count)
        for row in diagnosis_result
    ]
    
    return StatsResponse(
        total_samples=total,
        by_source=by_source,
        by_diagnosis=by_diagnosis,
    )


@router.get("/filters", response_model=FiltersResponse)
async def get_filters(
    db: AsyncSession = Depends(get_db),
) -> FiltersResponse:
    """Get available filter options."""
    # Get unique source banks
    source_result = await db.execute(
        select(Sample.source_bank).distinct().order_by(Sample.source_bank)
    )
    source_banks = [r for r, in source_result if r]
    
    # Get unique diagnoses (top 100 by count)
    diagnosis_result = await db.execute(
        select(Sample.primary_diagnosis)
        .where(Sample.primary_diagnosis.isnot(None))
        .group_by(Sample.primary_diagnosis)
        .order_by(func.count(Sample.id).desc())
        .limit(100)
    )
    diagnoses = [r for r, in diagnosis_result if r]
    
    # Get unique brain regions
    region_result = await db.execute(
        select(Sample.brain_region)
        .where(Sample.brain_region.isnot(None))
        .group_by(Sample.brain_region)
        .order_by(func.count(Sample.id).desc())
        .limit(100)
    )
    brain_regions = [r for r, in region_result if r]
    
    # Get unique sexes
    sex_result = await db.execute(
        select(Sample.donor_sex).distinct().order_by(Sample.donor_sex)
    )
    sexes = [r for r, in sex_result if r]
    
    return FiltersResponse(
        source_banks=source_banks,
        diagnoses=diagnoses,
        brain_regions=brain_regions,
        sexes=sexes,
    )


@router.get("/{sample_id}", response_model=SampleResponse)
async def get_sample(
    sample_id: str,
    db: AsyncSession = Depends(get_db),
) -> SampleResponse:
    """Get a single sample by ID."""
    result = await db.execute(select(Sample).where(Sample.id == sample_id))
    sample = result.scalar_one_or_none()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    return SampleResponse.model_validate(sample)


@router.post("/search", response_model=SampleListResponse)
async def search_samples(
    search: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SampleListResponse:
    """Search samples with multiple criteria."""
    query = select(Sample)
    count_query = select(func.count(Sample.id))
    
    # Text search on diagnosis
    if search.diagnosis:
        query = query.where(Sample.primary_diagnosis.ilike(f"%{search.diagnosis}%"))
        count_query = count_query.where(Sample.primary_diagnosis.ilike(f"%{search.diagnosis}%"))
    
    # Text search on brain region
    if search.brain_region:
        query = query.where(Sample.brain_region.ilike(f"%{search.brain_region}%"))
        count_query = count_query.where(Sample.brain_region.ilike(f"%{search.brain_region}%"))
    
    # Exact match on source bank
    if search.source_bank:
        query = query.where(Sample.source_bank == search.source_bank)
        count_query = count_query.where(Sample.source_bank == search.source_bank)
    
    # Exact match on sex
    if search.sex:
        query = query.where(Sample.donor_sex.ilike(search.sex))
        count_query = count_query.where(Sample.donor_sex.ilike(search.sex))
    
    # Age range
    if search.min_age is not None:
        query = query.where(Sample.donor_age >= search.min_age)
        count_query = count_query.where(Sample.donor_age >= search.min_age)
    
    if search.max_age is not None:
        query = query.where(Sample.donor_age <= search.max_age)
        count_query = count_query.where(Sample.donor_age <= search.max_age)
    
    # RIN score filter
    if search.min_rin is not None:
        query = query.where(Sample.rin_score >= search.min_rin)
        count_query = count_query.where(Sample.rin_score >= search.min_rin)
    
    # PMI filter
    if search.max_pmi is not None:
        query = query.where(Sample.postmortem_interval_hours <= search.max_pmi)
        count_query = count_query.where(Sample.postmortem_interval_hours <= search.max_pmi)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    query = query.offset(search.offset).limit(search.limit)
    result = await db.execute(query)
    samples = result.scalars().all()
    
    return SampleListResponse(
        items=[SampleResponse.model_validate(s) for s in samples],
        total=total,
        limit=search.limit,
        offset=search.offset,
    )


@router.post("/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SemanticSearchResponse:
    """Search samples using natural language and vector similarity.
    
    Uses semantic understanding to find relevant samples based on meaning,
    not just keyword matching. Optionally combine with filters.
    """
    from axon.rag.embeddings import EmbeddingService
    
    settings = get_settings()
    
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Semantic search unavailable: OpenAI API key not configured"
        )
    
    # Generate embedding for the query
    embedding_service = EmbeddingService(api_key=settings.openai_api_key)
    query_embedding = await embedding_service.embed_query(request.query)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    # Build SQL query with vector similarity
    sql = """
        SELECT 
            id, source_bank, external_id, source_url,
            donor_age, donor_age_range, donor_sex, donor_race, donor_ethnicity,
            primary_diagnosis, primary_diagnosis_code, secondary_diagnoses,
            cause_of_death, manner_of_death,
            brain_region, brain_region_code, tissue_type, hemisphere, preservation_method,
            postmortem_interval_hours, ph_level, rin_score, quality_metrics,
            quantity_available, is_available, raw_data, extended_data,
            1 - (embedding <=> $1::vector) as similarity
        FROM samples
        WHERE embedding IS NOT NULL
    """
    
    params = [embedding_str]
    param_idx = 2
    
    # Add filters
    if request.source_bank:
        sql += f" AND source_bank = ${param_idx}"
        params.append(request.source_bank)
        param_idx += 1
    
    if request.diagnosis:
        sql += f" AND primary_diagnosis ILIKE ${param_idx}"
        params.append(f"%{request.diagnosis}%")
        param_idx += 1
    
    if request.brain_region:
        sql += f" AND brain_region ILIKE ${param_idx}"
        params.append(f"%{request.brain_region}%")
        param_idx += 1
    
    if request.sex:
        sql += f" AND donor_sex ILIKE ${param_idx}"
        params.append(request.sex)
        param_idx += 1
    
    if request.min_age is not None:
        sql += f" AND donor_age >= ${param_idx}"
        params.append(request.min_age)
        param_idx += 1
    
    if request.max_age is not None:
        sql += f" AND donor_age <= ${param_idx}"
        params.append(request.max_age)
        param_idx += 1
    
    if request.min_rin is not None:
        sql += f" AND rin_score >= ${param_idx}"
        params.append(request.min_rin)
        param_idx += 1
    
    if request.max_pmi is not None:
        sql += f" AND postmortem_interval_hours <= ${param_idx}"
        params.append(request.max_pmi)
        param_idx += 1
    
    # Order by similarity and limit
    sql += f" ORDER BY embedding <=> $1::vector LIMIT ${param_idx}"
    params.append(request.limit)
    
    # Execute using raw asyncpg connection
    conn = await db.connection()
    raw_conn = await conn.get_raw_connection()
    asyncpg_conn = raw_conn.driver_connection
    
    rows = await asyncpg_conn.fetch(sql, *params)
    
    # Build response
    results = []
    for row in rows:
        sample = SampleResponse(
            id=row["id"],
            source_bank=row["source_bank"],
            external_id=row["external_id"],
            source_url=row["source_url"],
            donor_age=row["donor_age"],
            donor_age_range=row["donor_age_range"],
            donor_sex=row["donor_sex"],
            donor_race=row["donor_race"],
            donor_ethnicity=row["donor_ethnicity"],
            primary_diagnosis=row["primary_diagnosis"],
            primary_diagnosis_code=row["primary_diagnosis_code"],
            secondary_diagnoses=row["secondary_diagnoses"],
            cause_of_death=row["cause_of_death"],
            manner_of_death=row["manner_of_death"],
            brain_region=row["brain_region"],
            brain_region_code=row["brain_region_code"],
            tissue_type=row["tissue_type"],
            hemisphere=row["hemisphere"],
            preservation_method=row["preservation_method"],
            postmortem_interval_hours=row["postmortem_interval_hours"],
            ph_level=row["ph_level"],
            rin_score=row["rin_score"],
            quality_metrics=row["quality_metrics"],
            quantity_available=row["quantity_available"],
            is_available=row["is_available"],
            raw_data=row["raw_data"],
            extended_data=row["extended_data"],
        )
        
        results.append(SemanticSearchResult(
            sample=sample,
            score=max(0.0, min(1.0, row["similarity"]))
        ))
    
    return SemanticSearchResponse(
        query=request.query,
        results=results,
        total=len(results),
    )

