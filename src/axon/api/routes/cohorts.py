"""Cohort API endpoints for saving and managing sample collections."""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from axon.api.dependencies import get_db
from axon.db.models import Cohort, CohortSample, Sample

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cohorts", tags=["cohorts"])


class SampleInput(BaseModel):
    """Input for a sample to add to cohort.
    
    IMPORTANT: source_bank is required to uniquely identify samples,
    as the same external_id may exist at multiple brain banks.
    """
    external_id: str
    source_bank: Optional[str] = None  # REQUIRED for unique identification
    sample_group: str  # 'case' or 'control'


class CreateCohortRequest(BaseModel):
    """Request body for creating a cohort."""
    name: str
    description: Optional[str] = None
    samples: list[SampleInput]
    source_conversation_id: Optional[str] = None


class CohortSampleResponse(BaseModel):
    """Response model for a sample in a cohort."""
    id: str
    external_id: str
    sample_group: str
    diagnosis: Optional[str]
    age: Optional[int]
    sex: Optional[str]
    source_bank: Optional[str]
    # Extended fields from Sample table
    race: Optional[str] = None
    braak_stage: Optional[str] = None
    rin: Optional[float] = None
    pmi: Optional[float] = None
    ph: Optional[float] = None
    diagnoses: list[str] = []


class CohortResponse(BaseModel):
    """Response model for a cohort."""
    id: str
    name: str
    description: Optional[str]
    sample_count: int
    case_count: int
    control_count: int
    created_at: datetime
    updated_at: datetime


class CohortDetailResponse(CohortResponse):
    """Detailed cohort response including samples."""
    samples: list[CohortSampleResponse]


@router.post("", response_model=CohortResponse)
async def create_cohort(
    request: CreateCohortRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new cohort with samples."""
    try:
        # Create the cohort
        cohort = Cohort(
            id=str(uuid4()),
            name=request.name,
            description=request.description,
            source_conversation_id=request.source_conversation_id,
        )
        db.add(cohort)
        await db.flush()  # Get the cohort ID

        # Look up sample details from the samples table
        case_count = 0
        control_count = 0
        
        for sample_input in request.samples:
            # Clean the external_id (strip backticks that might be in markdown)
            clean_external_id = sample_input.external_id.strip("`").strip()
            
            # Build query with BOTH external_id AND source_bank for unique identification
            query = select(Sample).where(Sample.external_id == clean_external_id)
            if sample_input.source_bank:
                query = query.where(Sample.source_bank.ilike(f"%{sample_input.source_bank}%"))
            
            result = await db.execute(query)
            sample = result.scalar_one_or_none()
            
            # Use neuropathology_diagnosis (primary) instead of clinical diagnosis
            diagnosis = sample.neuropathology_diagnosis if sample else None
            if not diagnosis and sample:
                diagnosis = sample.primary_diagnosis  # Fallback to clinical
            
            # Create cohort sample with cached info
            cohort_sample = CohortSample(
                id=str(uuid4()),
                cohort_id=cohort.id,
                sample_external_id=clean_external_id,
                sample_group=sample_input.sample_group,
                diagnosis=diagnosis,
                age=sample.donor_age if sample else None,
                sex=sample.donor_sex if sample else None,
                source_bank=sample.source_bank if sample else sample_input.source_bank,
            )
            db.add(cohort_sample)
            
            if sample_input.sample_group == "case":
                case_count += 1
            else:
                control_count += 1

        await db.commit()
        await db.refresh(cohort)

        return CohortResponse(
            id=cohort.id,
            name=cohort.name,
            description=cohort.description,
            sample_count=len(request.samples),
            case_count=case_count,
            control_count=control_count,
            created_at=cohort.created_at,
            updated_at=cohort.updated_at,
        )
    except Exception as e:
        logger.error(f"Error creating cohort: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[CohortResponse])
async def list_cohorts(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all cohorts."""
    try:
        result = await db.execute(
            select(Cohort).order_by(desc(Cohort.updated_at)).limit(limit)
        )
        cohorts = result.scalars().all()

        responses = []
        for cohort in cohorts:
            # Count samples by group
            samples_result = await db.execute(
                select(CohortSample).where(CohortSample.cohort_id == cohort.id)
            )
            samples = samples_result.scalars().all()
            
            case_count = sum(1 for s in samples if s.sample_group == "case")
            control_count = sum(1 for s in samples if s.sample_group == "control")
            
            responses.append(CohortResponse(
                id=cohort.id,
                name=cohort.name,
                description=cohort.description,
                sample_count=len(samples),
                case_count=case_count,
                control_count=control_count,
                created_at=cohort.created_at,
                updated_at=cohort.updated_at,
            ))

        return responses
    except Exception as e:
        logger.error(f"Error listing cohorts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cohort_id}", response_model=CohortDetailResponse)
async def get_cohort(
    cohort_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a cohort with all samples including full sample data."""
    try:
        result = await db.execute(
            select(Cohort).where(Cohort.id == cohort_id)
        )
        cohort = result.scalar_one_or_none()
        
        if not cohort:
            raise HTTPException(status_code=404, detail="Cohort not found")

        # Get cohort samples
        samples_result = await db.execute(
            select(CohortSample).where(CohortSample.cohort_id == cohort_id)
        )
        cohort_samples = samples_result.scalars().all()
        
        case_count = sum(1 for s in cohort_samples if s.sample_group == "case")
        control_count = sum(1 for s in cohort_samples if s.sample_group == "control")

        # Build response with full sample data
        sample_responses = []
        for cs in cohort_samples:
            # Clean the external_id (strip backticks that might have been stored)
            clean_external_id = cs.sample_external_id.strip("`").strip()
            
            # Look up full sample data - try to match by external_id
            # If source_bank is cached, use it to narrow down
            sample = None
            if cs.source_bank:
                sample_result = await db.execute(
                    select(Sample).where(
                        Sample.external_id == clean_external_id,
                        Sample.source_bank == cs.source_bank
                    )
                )
                sample = sample_result.scalar_one_or_none()
            
            # If not found with source_bank, try just external_id (get first match)
            if sample is None:
                sample_result = await db.execute(
                    select(Sample).where(Sample.external_id == clean_external_id).limit(1)
                )
                sample = sample_result.scalar_one_or_none()
            
            # Extract Braak stage from raw_data if available
            braak_stage = None
            diagnoses = []
            if sample and sample.raw_data:
                braak_stage = sample.raw_data.get("braak_stage")
                # Build diagnoses list from primary + secondary
                if sample.primary_diagnosis:
                    diagnoses.append(sample.primary_diagnosis)
                if sample.secondary_diagnoses:
                    for sd in sample.secondary_diagnoses:
                        if isinstance(sd, dict) and sd.get("diagnosis"):
                            diagnoses.append(sd["diagnosis"])
                        elif isinstance(sd, str):
                            diagnoses.append(sd)
            
            # Use neuropathology_diagnosis (primary), fallback to clinical
            diagnosis = None
            if sample:
                diagnosis = sample.neuropathology_diagnosis or sample.primary_diagnosis
            else:
                diagnosis = cs.diagnosis
            
            sample_responses.append(CohortSampleResponse(
                id=cs.id,
                external_id=clean_external_id,  # Use cleaned ID without backticks
                sample_group=cs.sample_group,
                diagnosis=diagnosis,
                age=sample.donor_age if sample else cs.age,
                sex=sample.donor_sex if sample else cs.sex,
                source_bank=sample.source_bank if sample else cs.source_bank,
                race=sample.donor_race if sample else None,
                braak_stage=braak_stage,
                rin=float(sample.rin_score) if sample and sample.rin_score else None,
                pmi=float(sample.postmortem_interval_hours) if sample and sample.postmortem_interval_hours else None,
                ph=float(sample.ph_level) if sample and sample.ph_level else None,
                diagnoses=diagnoses,
            ))

        return CohortDetailResponse(
            id=cohort.id,
            name=cohort.name,
            description=cohort.description,
            sample_count=len(cohort_samples),
            case_count=case_count,
            control_count=control_count,
            created_at=cohort.created_at,
            updated_at=cohort.updated_at,
            samples=sample_responses,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cohort: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{cohort_id}")
async def delete_cohort(
    cohort_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a cohort."""
    try:
        result = await db.execute(
            select(Cohort).where(Cohort.id == cohort_id)
        )
        cohort = result.scalar_one_or_none()
        
        if not cohort:
            raise HTTPException(status_code=404, detail="Cohort not found")

        await db.delete(cohort)
        await db.commit()

        return {"status": "deleted", "id": cohort_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cohort: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

