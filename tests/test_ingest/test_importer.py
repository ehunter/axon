"""Tests for the core importer module.

These tests define the expected behavior of the sample importer.
Following TDD: tests written first, then implementation.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from axon.db.models import DataSource, Sample
from axon.ingest.importer import SampleImporter, ImportResult


class TestSampleImporter:
    """Tests for the SampleImporter class."""

    @pytest.mark.asyncio
    async def test_import_single_sample(self, db_session):
        """Should import a single sample into the database."""
        importer = SampleImporter(db_session)
        
        sample_data = {
            "source_bank": "NIH Miami",
            "external_id": "NIH1000",
            "donor_age": 65,
            "donor_sex": "female",
            "donor_race": "White",
            "primary_diagnosis": "Alzheimer's disease",
            "brain_region": "Hippocampus, Frontal cortex",
            "rin_score": Decimal("7.2"),
            "postmortem_interval_hours": Decimal("12.5"),
            "raw_data": {"original": "data"},
        }
        
        result = await importer.import_sample(sample_data)
        
        assert result.created == 1
        assert result.updated == 0
        assert result.errors == 0
        
        # Verify in database
        query = select(Sample).where(Sample.external_id == "NIH1000")
        db_result = await db_session.execute(query)
        sample = db_result.scalar_one()
        
        assert sample.source_bank == "NIH Miami"
        assert sample.donor_age == 65

    @pytest.mark.asyncio
    async def test_import_updates_existing_sample(self, db_session):
        """Should update existing sample on duplicate (source_bank, external_id)."""
        importer = SampleImporter(db_session)
        
        # Import initial sample
        sample_data = {
            "source_bank": "NIH Miami",
            "external_id": "NIH1001",
            "donor_age": 70,
            "donor_sex": "male",
            "raw_data": {"version": 1},
        }
        await importer.import_sample(sample_data)
        
        # Import updated version
        updated_data = {
            "source_bank": "NIH Miami",
            "external_id": "NIH1001",
            "donor_age": 70,
            "donor_sex": "male",
            "rin_score": Decimal("8.0"),  # New field
            "raw_data": {"version": 2},
        }
        result = await importer.import_sample(updated_data)
        
        assert result.created == 0
        assert result.updated == 1
        
        # Verify update
        query = select(Sample).where(Sample.external_id == "NIH1001")
        db_result = await db_session.execute(query)
        sample = db_result.scalar_one()
        
        assert sample.rin_score == Decimal("8.0")
        assert sample.raw_data == {"version": 2}

    @pytest.mark.asyncio
    async def test_import_batch(self, db_session):
        """Should import multiple samples efficiently."""
        importer = SampleImporter(db_session)
        
        samples = [
            {
                "source_bank": "NIH Miami",
                "external_id": f"NIH{i}",
                "donor_age": 50 + i,
                "raw_data": {"id": i},
            }
            for i in range(10)
        ]
        
        result = await importer.import_batch(samples)
        
        assert result.created == 10
        assert result.updated == 0
        assert result.total == 10

    @pytest.mark.asyncio
    async def test_import_batch_with_duplicates(self, db_session):
        """Should handle mix of new and existing samples in batch."""
        importer = SampleImporter(db_session)
        
        # Import initial batch
        initial = [
            {"source_bank": "Harvard", "external_id": "H1", "donor_age": 60, "raw_data": {}},
            {"source_bank": "Harvard", "external_id": "H2", "donor_age": 65, "raw_data": {}},
        ]
        await importer.import_batch(initial)
        
        # Import mixed batch (2 updates, 2 new)
        mixed = [
            {"source_bank": "Harvard", "external_id": "H1", "donor_age": 60, "rin_score": Decimal("7.0"), "raw_data": {}},
            {"source_bank": "Harvard", "external_id": "H2", "donor_age": 65, "rin_score": Decimal("7.5"), "raw_data": {}},
            {"source_bank": "Harvard", "external_id": "H3", "donor_age": 70, "raw_data": {}},
            {"source_bank": "Harvard", "external_id": "H4", "donor_age": 75, "raw_data": {}},
        ]
        result = await importer.import_batch(mixed)
        
        assert result.created == 2
        assert result.updated == 2
        assert result.total == 4

    @pytest.mark.asyncio
    async def test_import_creates_data_source(self, db_session):
        """Should create DataSource record if it doesn't exist."""
        importer = SampleImporter(db_session, auto_create_sources=True)
        
        sample_data = {
            "source_bank": "New Bank",
            "external_id": "NB001",
            "raw_data": {},
        }
        
        await importer.import_sample(sample_data)
        
        # Verify DataSource was created
        query = select(DataSource).where(DataSource.name == "New Bank")
        db_result = await db_session.execute(query)
        source = db_result.scalar_one_or_none()
        
        assert source is not None
        assert source.name == "New Bank"
        assert source.total_samples == 1

    @pytest.mark.asyncio
    async def test_import_updates_source_sample_count(self, db_session):
        """Should update DataSource.total_samples after import."""
        importer = SampleImporter(db_session, auto_create_sources=True)
        
        samples = [
            {"source_bank": "Test Bank", "external_id": f"TB{i}", "raw_data": {}}
            for i in range(5)
        ]
        
        await importer.import_batch(samples)
        
        query = select(DataSource).where(DataSource.name == "Test Bank")
        db_result = await db_session.execute(query)
        source = db_result.scalar_one()
        
        assert source.total_samples == 5

    @pytest.mark.asyncio
    async def test_import_with_invalid_data(self, db_session):
        """Should track errors for invalid data."""
        importer = SampleImporter(db_session)
        
        # Missing required field (source_bank)
        invalid_sample = {
            "external_id": "TEST001",
            "raw_data": {},
        }
        
        result = await importer.import_sample(invalid_sample)
        
        assert result.errors == 1
        assert result.created == 0


class TestImportResult:
    """Tests for ImportResult tracking."""

    def test_import_result_total(self):
        """Should calculate total correctly."""
        result = ImportResult(created=10, updated=5, errors=2)
        assert result.total == 15  # created + updated

    def test_import_result_add(self):
        """Should add results together."""
        r1 = ImportResult(created=5, updated=2, errors=1)
        r2 = ImportResult(created=3, updated=1, errors=0)
        
        combined = r1 + r2
        
        assert combined.created == 8
        assert combined.updated == 3
        assert combined.errors == 1


class TestImporterWithAdapter:
    """Integration tests with NIH adapter."""

    @pytest.mark.asyncio
    async def test_import_from_adapter(self, db_session, tmp_path):
        """Should import samples directly from adapter output."""
        from axon.ingest.adapters.nih import NIHAdapter
        
        # Create test CSV
        csv_content = '''"Subject ID","Repository","Subject Age","Subject Sex","Race","Ethnicity","Clinical Brain Diagnosis (Basis for Clinical Diagnosis)","ICD for Clinical Brain Diagnosis","Neuropathology Diagnosis","Brain Region","Brain Hemisphere","PMI (hours)","RIN","Preparation","Manner of Death","Tissue Source"
"NIH9001","Miami","65","Female","White","Not Hispanic or Latino","Alzheimer's disease (Confirmed Diagnosis)","G30.9","Alzheimer's disease","Hippocampus","Left, Right","12.5","7.2","Left - Frozen, Right - Frozen","Natural","None"
"NIH9002","Harvard","70","Male","White","Not Hispanic or Latino","Parkinson's disease (Confirmed Diagnosis)","G20","Parkinson's disease","Substantia nigra","Left","18.0","6.8","Left - Frozen","Natural","None"
'''
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        # Process with adapter
        adapter = NIHAdapter()
        samples = list(adapter.process_csv(str(csv_file)))
        
        # Import
        importer = SampleImporter(db_session, auto_create_sources=True)
        result = await importer.import_batch(samples)
        
        assert result.created == 2
        assert result.errors == 0
        
        # Verify data
        query = select(Sample).where(Sample.external_id == "NIH9001")
        db_result = await db_session.execute(query)
        sample = db_result.scalar_one()
        
        assert sample.source_bank == "NIH Miami"
        assert sample.donor_age == 65
        assert sample.primary_diagnosis == "Alzheimer's disease"

