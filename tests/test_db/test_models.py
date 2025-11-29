"""Tests for database models.

These tests define the expected behavior of our SQLAlchemy models.
Following TDD: tests written first, then implementation.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from axon.db.models import (
    Base,
    Conversation,
    DataSource,
    Message,
    Paper,
    PaperChunk,
    Sample,
    SourceCharacteristic,
)


class TestDataSource:
    """Tests for the DataSource model."""

    @pytest.mark.asyncio
    async def test_create_data_source(self, db_session):
        """Should create a data source with required fields."""
        source = DataSource(
            name="NIH",
            display_name="NIH NeuroBioBank",
            description="National Institutes of Health brain bank",
        )
        db_session.add(source)
        await db_session.commit()
        
        assert source.id is not None
        assert source.name == "NIH"
        assert source.is_active is True
        assert source.created_at is not None

    @pytest.mark.asyncio
    async def test_data_source_unique_name(self, db_session):
        """Should enforce unique constraint on name."""
        source1 = DataSource(name="NIH", display_name="NIH Bank")
        source2 = DataSource(name="NIH", display_name="Duplicate")
        
        db_session.add(source1)
        await db_session.commit()
        
        db_session.add(source2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_data_source_characteristics_relationship(self, db_session):
        """Should have relationship to source characteristics."""
        source = DataSource(name="Banner", display_name="Banner Sun Health")
        db_session.add(source)
        await db_session.commit()
        
        characteristic = SourceCharacteristic(
            source_id=source.id,
            category="quality",
            characteristic="Rapid autopsy program with PMI under 4 hours",
        )
        db_session.add(characteristic)
        await db_session.commit()
        
        # Refresh to load relationship (must specify attribute for async)
        await db_session.refresh(source, ["characteristics"])
        assert len(source.characteristics) == 1
        assert source.characteristics[0].category == "quality"


class TestSample:
    """Tests for the Sample model."""

    @pytest.mark.asyncio
    async def test_create_sample_minimal(self, db_session):
        """Should create a sample with minimal required fields."""
        sample = Sample(
            source_bank="NIH",
            external_id="NIH-12345",
            raw_data={"original": "data"},
        )
        db_session.add(sample)
        await db_session.commit()
        
        assert sample.id is not None
        assert sample.source_bank == "NIH"
        assert sample.external_id == "NIH-12345"
        assert sample.is_available is True

    @pytest.mark.asyncio
    async def test_create_sample_full(self, db_session):
        """Should create a sample with all fields."""
        sample = Sample(
            source_bank="NIH",
            external_id="NIH-67890",
            source_url="https://neurobiobank.nih.gov/sample/67890",
            donor_age=72,
            donor_sex="male",
            donor_race="White",
            donor_ethnicity="Non-Hispanic",
            primary_diagnosis="Alzheimer's Disease",
            primary_diagnosis_code="G30.9",
            secondary_diagnoses=[{"diagnosis": "Hypertension", "code": "I10"}],
            cause_of_death="Alzheimer's Disease",
            brain_region="Hippocampus",
            brain_region_code="UBERON:0001954",
            tissue_type="fresh-frozen",
            hemisphere="left",
            preservation_method="Flash frozen",
            postmortem_interval_hours=12.5,
            ph_level=6.8,
            rin_score=7.2,
            quality_metrics={"additional": "metrics"},
            quantity_available="50mg",
            raw_data={"full": "original_record"},
            extended_data={"parsed": "source_specific"},
            searchable_text="72yo male Alzheimer's hippocampus",
        )
        db_session.add(sample)
        await db_session.commit()
        
        assert sample.donor_age == 72
        assert sample.rin_score == 7.2
        assert sample.quality_metrics == {"additional": "metrics"}

    @pytest.mark.asyncio
    async def test_sample_unique_constraint(self, db_session):
        """Should enforce unique constraint on (source_bank, external_id)."""
        sample1 = Sample(
            source_bank="NIH",
            external_id="NIH-DUPE",
            raw_data={},
        )
        sample2 = Sample(
            source_bank="NIH",
            external_id="NIH-DUPE",
            raw_data={},
        )
        
        db_session.add(sample1)
        await db_session.commit()
        
        db_session.add(sample2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_sample_same_id_different_source(self, db_session):
        """Should allow same external_id from different sources."""
        sample1 = Sample(
            source_bank="NIH",
            external_id="12345",
            raw_data={},
        )
        sample2 = Sample(
            source_bank="Harvard",
            external_id="12345",
            raw_data={},
        )
        
        db_session.add_all([sample1, sample2])
        await db_session.commit()
        
        # Both should exist
        result = await db_session.execute(select(Sample))
        samples = result.scalars().all()
        assert len(samples) == 2


class TestConversation:
    """Tests for the Conversation model."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session):
        """Should create a conversation."""
        conv = Conversation(
            title="Finding ALS samples",
            user_id="user-123",
        )
        db_session.add(conv)
        await db_session.commit()
        
        assert conv.id is not None
        assert conv.title == "Finding ALS samples"
        assert conv.created_at is not None

    @pytest.mark.asyncio
    async def test_conversation_messages_relationship(self, db_session):
        """Should have relationship to messages."""
        conv = Conversation(title="Test conversation")
        db_session.add(conv)
        await db_session.commit()
        
        msg1 = Message(
            conversation_id=conv.id,
            role="user",
            content="I need ALS samples",
        )
        msg2 = Message(
            conversation_id=conv.id,
            role="assistant",
            content="I found 15 ALS samples...",
        )
        db_session.add_all([msg1, msg2])
        await db_session.commit()
        
        # Refresh to load relationship (must specify attribute for async)
        await db_session.refresh(conv, ["messages"])
        assert len(conv.messages) == 2

    @pytest.mark.asyncio
    async def test_message_cascade_delete(self, db_session):
        """Should delete messages when conversation is deleted."""
        conv = Conversation(title="To be deleted")
        db_session.add(conv)
        await db_session.commit()
        
        msg = Message(
            conversation_id=conv.id,
            role="user",
            content="Test message",
        )
        db_session.add(msg)
        await db_session.commit()
        
        msg_id = msg.id
        
        await db_session.delete(conv)
        await db_session.commit()
        
        # Message should be deleted
        result = await db_session.execute(
            select(Message).where(Message.id == msg_id)
        )
        assert result.scalar_one_or_none() is None


class TestMessage:
    """Tests for the Message model."""

    @pytest.mark.asyncio
    async def test_create_message(self, db_session):
        """Should create a message with required fields."""
        conv = Conversation(title="Test")
        db_session.add(conv)
        await db_session.commit()
        
        msg = Message(
            conversation_id=conv.id,
            role="user",
            content="Hello, I need brain samples",
        )
        db_session.add(msg)
        await db_session.commit()
        
        assert msg.id is not None
        assert msg.role == "user"
        assert msg.created_at is not None

    @pytest.mark.asyncio
    async def test_message_with_retrieval_context(self, db_session):
        """Should store retrieved sample and chunk IDs."""
        conv = Conversation(title="Test")
        db_session.add(conv)
        await db_session.commit()
        
        sample_ids = [uuid.uuid4(), uuid.uuid4()]
        chunk_ids = [uuid.uuid4()]
        
        msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Based on your requirements...",
            retrieved_sample_ids=[str(sid) for sid in sample_ids],
            retrieved_chunk_ids=[str(cid) for cid in chunk_ids],
            tokens_used=150,
        )
        db_session.add(msg)
        await db_session.commit()
        
        assert len(msg.retrieved_sample_ids) == 2
        assert msg.tokens_used == 150


class TestPaper:
    """Tests for the Paper model."""

    @pytest.mark.asyncio
    async def test_create_paper(self, db_session):
        """Should create a paper with required fields."""
        paper = Paper(
            title="Tau pathology in Alzheimer's disease",
            authors=["Smith, J.", "Jones, A."],
            abstract="This paper explores...",
            doi="10.1234/example.2024",
        )
        db_session.add(paper)
        await db_session.commit()
        
        assert paper.id is not None
        assert paper.processing_status == "pending"

    @pytest.mark.asyncio
    async def test_paper_unique_doi(self, db_session):
        """Should enforce unique constraint on DOI."""
        paper1 = Paper(
            title="Paper 1",
            doi="10.1234/unique",
        )
        paper2 = Paper(
            title="Paper 2",
            doi="10.1234/unique",
        )
        
        db_session.add(paper1)
        await db_session.commit()
        
        db_session.add(paper2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_paper_chunks_relationship(self, db_session):
        """Should have relationship to paper chunks."""
        paper = Paper(
            title="Test Paper",
            doi="10.1234/test",
        )
        db_session.add(paper)
        await db_session.commit()
        
        chunk1 = PaperChunk(
            paper_id=paper.id,
            chunk_index=0,
            content="Introduction section...",
            section_title="Introduction",
        )
        chunk2 = PaperChunk(
            paper_id=paper.id,
            chunk_index=1,
            content="Methods section...",
            section_title="Methods",
        )
        db_session.add_all([chunk1, chunk2])
        await db_session.commit()
        
        # Refresh to load relationship (must specify attribute for async)
        await db_session.refresh(paper, ["chunks"])
        assert len(paper.chunks) == 2


class TestPaperChunk:
    """Tests for the PaperChunk model."""

    @pytest.mark.asyncio
    async def test_create_paper_chunk(self, db_session):
        """Should create a paper chunk."""
        paper = Paper(title="Test", doi="10.1234/chunk-test")
        db_session.add(paper)
        await db_session.commit()
        
        chunk = PaperChunk(
            paper_id=paper.id,
            chunk_index=0,
            content="This is the chunk content for embedding.",
            section_title="Results",
            page_number=5,
        )
        db_session.add(chunk)
        await db_session.commit()
        
        assert chunk.id is not None
        assert chunk.chunk_index == 0

    @pytest.mark.asyncio
    async def test_chunk_cascade_delete(self, db_session):
        """Should delete chunks when paper is deleted."""
        paper = Paper(title="To delete", doi="10.1234/delete-me")
        db_session.add(paper)
        await db_session.commit()
        
        chunk = PaperChunk(
            paper_id=paper.id,
            chunk_index=0,
            content="Content",
        )
        db_session.add(chunk)
        await db_session.commit()
        
        chunk_id = chunk.id
        
        await db_session.delete(paper)
        await db_session.commit()
        
        result = await db_session.execute(
            select(PaperChunk).where(PaperChunk.id == chunk_id)
        )
        assert result.scalar_one_or_none() is None

