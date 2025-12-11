"""Core importer module for loading samples into the database.

This module provides the SampleImporter class that handles inserting
and updating samples in the database. It can be used by both CLI
commands and API endpoints.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import DataSource, Sample


@dataclass
class ImportResult:
    """Tracks results of an import operation."""

    created: int = 0
    updated: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total successfully processed (created + updated)."""
        return self.created + self.updated

    def __add__(self, other: "ImportResult") -> "ImportResult":
        """Add two ImportResults together."""
        return ImportResult(
            created=self.created + other.created,
            updated=self.updated + other.updated,
            errors=self.errors + other.errors,
            error_messages=self.error_messages + other.error_messages,
        )


class SampleImporter:
    """Imports sample data into the database.
    
    Handles both creating new samples and updating existing ones
    based on the (source_bank, external_id) unique constraint.
    
    Args:
        session: SQLAlchemy async session
        auto_create_sources: If True, automatically create DataSource 
            records for new source banks
    """

    def __init__(
        self,
        session: AsyncSession,
        auto_create_sources: bool = False,
    ):
        self.session = session
        self.auto_create_sources = auto_create_sources
        self._source_cache: dict[str, DataSource] = {}

    async def _get_or_create_source(self, source_bank: str) -> DataSource | None:
        """Get or create a DataSource record."""
        if not self.auto_create_sources:
            return None

        # Check cache first
        if source_bank in self._source_cache:
            return self._source_cache[source_bank]

        # Check database
        query = select(DataSource).where(DataSource.name == source_bank)
        result = await self.session.execute(query)
        source = result.scalar_one_or_none()

        if source is None:
            # Create new source
            source = DataSource(
                name=source_bank,
                display_name=source_bank,
                total_samples=0,
            )
            self.session.add(source)
            await self.session.flush()

        self._source_cache[source_bank] = source
        return source

    async def _find_existing_sample(
        self, source_bank: str, external_id: str
    ) -> Sample | None:
        """Find an existing sample by source_bank and external_id."""
        query = select(Sample).where(
            Sample.source_bank == source_bank,
            Sample.external_id == external_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    def _validate_sample_data(self, data: dict[str, Any]) -> list[str]:
        """Validate sample data and return list of errors."""
        errors = []

        if not data.get("source_bank"):
            errors.append("Missing required field: source_bank")

        if not data.get("external_id"):
            errors.append("Missing required field: external_id")

        return errors

    def _create_sample_from_data(self, data: dict[str, Any]) -> Sample:
        """Create a Sample model instance from data dict."""
        return Sample(
            source_bank=data.get("source_bank"),
            external_id=data.get("external_id"),
            source_url=data.get("source_url"),
            donor_age=data.get("donor_age"),
            donor_age_range=data.get("donor_age_range"),
            donor_sex=data.get("donor_sex"),
            donor_race=data.get("donor_race"),
            donor_ethnicity=data.get("donor_ethnicity"),
            primary_diagnosis=data.get("primary_diagnosis"),
            primary_diagnosis_code=data.get("primary_diagnosis_code"),
            neuropathology_diagnosis=data.get("neuropathology_diagnosis"),
            neuropathology_diagnosis_code=data.get("neuropathology_diagnosis_code"),
            secondary_diagnoses=data.get("secondary_diagnoses"),
            cause_of_death=data.get("cause_of_death"),
            manner_of_death=data.get("manner_of_death"),
            brain_region=data.get("brain_region"),
            brain_region_code=data.get("brain_region_code"),
            tissue_type=data.get("tissue_type"),
            hemisphere=data.get("hemisphere"),
            preservation_method=data.get("preservation_method"),
            postmortem_interval_hours=data.get("postmortem_interval_hours"),
            ph_level=data.get("ph_level"),
            rin_score=data.get("rin_score"),
            quality_metrics=data.get("quality_metrics"),
            quantity_available=data.get("quantity_available"),
            is_available=data.get("is_available", True),
            raw_data=data.get("raw_data", {}),
            extended_data=data.get("extended_data"),
            searchable_text=data.get("searchable_text"),
        )

    def _update_sample_from_data(self, sample: Sample, data: dict[str, Any]) -> None:
        """Update an existing Sample with new data."""
        # Update all fields that are present in data
        updatable_fields = [
            "source_url",
            "donor_age",
            "donor_age_range",
            "donor_sex",
            "donor_race",
            "donor_ethnicity",
            "primary_diagnosis",
            "primary_diagnosis_code",
            "neuropathology_diagnosis",
            "neuropathology_diagnosis_code",
            "secondary_diagnoses",
            "cause_of_death",
            "manner_of_death",
            "brain_region",
            "brain_region_code",
            "tissue_type",
            "hemisphere",
            "preservation_method",
            "postmortem_interval_hours",
            "ph_level",
            "rin_score",
            "quality_metrics",
            "quantity_available",
            "is_available",
            "raw_data",
            "extended_data",
            "searchable_text",
        ]

        for field_name in updatable_fields:
            if field_name in data:
                setattr(sample, field_name, data[field_name])

        sample.updated_at = datetime.utcnow()

    async def import_sample(self, data: dict[str, Any]) -> ImportResult:
        """Import a single sample.
        
        Args:
            data: Sample data dict (e.g., from NIHAdapter.to_sample_dict())
            
        Returns:
            ImportResult with counts
        """
        result = ImportResult()

        # Validate
        errors = self._validate_sample_data(data)
        if errors:
            result.errors = 1
            result.error_messages = errors
            return result

        source_bank = data["source_bank"]
        external_id = data["external_id"]

        # Get or create data source
        if self.auto_create_sources:
            await self._get_or_create_source(source_bank)

        # Check for existing sample
        existing = await self._find_existing_sample(source_bank, external_id)

        if existing:
            # Update existing
            self._update_sample_from_data(existing, data)
            result.updated = 1
        else:
            # Create new
            sample = self._create_sample_from_data(data)
            self.session.add(sample)
            result.created = 1

        await self.session.flush()

        # Update source count for single imports
        if self.auto_create_sources and (result.created > 0 or result.updated > 0):
            await self._update_source_counts()

        return result

    async def import_batch(
        self,
        samples: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> ImportResult:
        """Import multiple samples efficiently.
        
        Args:
            samples: List of sample data dicts
            batch_size: Number of samples to process before flushing
            
        Returns:
            Combined ImportResult for all samples
        """
        total_result = ImportResult()

        for i, sample_data in enumerate(samples):
            result = await self.import_sample(sample_data)
            total_result = total_result + result

            # Flush periodically for efficiency
            if (i + 1) % batch_size == 0:
                await self.session.flush()

        # Final flush
        await self.session.flush()

        # Update source sample counts
        if self.auto_create_sources:
            await self._update_source_counts()

        return total_result

    async def _update_source_counts(self) -> None:
        """Update total_samples count for all cached sources."""
        for source_bank, source in self._source_cache.items():
            # Count samples for this source
            query = select(Sample).where(Sample.source_bank == source_bank)
            result = await self.session.execute(query)
            count = len(result.scalars().all())
            source.total_samples = count

