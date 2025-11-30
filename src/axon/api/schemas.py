"""Pydantic schemas for API request/response models."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class SampleBase(BaseModel):
    """Base sample schema with common fields."""
    
    source_bank: str
    external_id: str
    source_url: str | None = None
    donor_age: int | None = None
    donor_age_range: str | None = None
    donor_sex: str | None = None
    donor_race: str | None = None
    donor_ethnicity: str | None = None
    primary_diagnosis: str | None = None
    primary_diagnosis_code: str | None = None
    brain_region: str | None = None
    brain_region_code: str | None = None
    tissue_type: str | None = None
    hemisphere: str | None = None
    preservation_method: str | None = None
    postmortem_interval_hours: Decimal | None = None
    rin_score: Decimal | None = None
    is_available: bool = True


class SampleResponse(SampleBase):
    """Sample response schema with all fields."""
    
    model_config = {"from_attributes": True}
    
    id: str
    secondary_diagnoses: list[dict[str, Any]] | None = None
    cause_of_death: str | None = None
    manner_of_death: str | None = None
    ph_level: Decimal | None = None
    quality_metrics: dict[str, Any] | None = None
    quantity_available: str | None = None
    raw_data: dict[str, Any] | None = None
    extended_data: dict[str, Any] | None = None


class SampleListResponse(BaseModel):
    """Paginated list of samples."""
    
    items: list[SampleResponse]
    total: int
    limit: int
    offset: int


class SearchRequest(BaseModel):
    """Search request with filter criteria."""
    
    # Text search
    query: str | None = None
    diagnosis: str | None = None
    brain_region: str | None = None
    
    # Exact match filters
    source_bank: str | None = None
    sex: str | None = None
    
    # Range filters
    min_age: int | None = None
    max_age: int | None = None
    min_rin: float | None = None
    max_pmi: float | None = None
    
    # Pagination
    limit: int = Field(default=50, le=500)
    offset: int = Field(default=0, ge=0)


class SourceCount(BaseModel):
    """Count of samples by source."""
    
    source_bank: str
    count: int


class DiagnosisCount(BaseModel):
    """Count of samples by diagnosis."""
    
    diagnosis: str
    count: int


class StatsResponse(BaseModel):
    """Sample statistics response."""
    
    total_samples: int
    by_source: list[SourceCount]
    by_diagnosis: list[DiagnosisCount]


class FiltersResponse(BaseModel):
    """Available filter options."""
    
    source_banks: list[str]
    diagnoses: list[str]
    brain_regions: list[str]
    sexes: list[str]


class SemanticSearchRequest(BaseModel):
    """Semantic search request using natural language."""
    
    # Natural language query
    query: str = Field(..., min_length=3, description="Natural language search query")
    
    # Optional filters to combine with semantic search
    source_bank: str | None = None
    diagnosis: str | None = None
    brain_region: str | None = None
    sex: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_rin: float | None = None
    max_pmi: float | None = None
    
    # Results
    limit: int = Field(default=10, le=100)


class SemanticSearchResult(BaseModel):
    """A single semantic search result with similarity score."""
    
    model_config = {"from_attributes": True}
    
    sample: SampleResponse
    score: float = Field(..., description="Similarity score (0-1, higher is better)")


class SemanticSearchResponse(BaseModel):
    """Semantic search response with ranked results."""
    
    query: str
    results: list[SemanticSearchResult]
    total: int

