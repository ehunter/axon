"""Tests for ConversationSample model - sample selection persistence.

These tests verify that we can persist the samples selected/recommended
during a conversation session.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select


class TestConversationSampleModel:
    """Tests for the ConversationSample database model."""
    
    def test_model_exists(self):
        """ConversationSample model should exist."""
        from axon.db.models import ConversationSample
        assert ConversationSample is not None
    
    def test_model_has_required_fields(self):
        """ConversationSample should have all required fields."""
        from axon.db.models import ConversationSample
        
        # Check that the model has the expected columns
        mapper = ConversationSample.__mapper__
        column_names = [c.key for c in mapper.columns]
        
        required_fields = [
            'id',
            'conversation_id',
            'sample_external_id',
            'sample_group',  # 'case' or 'control'
            'added_at',
        ]
        
        for field in required_fields:
            assert field in column_names, f"Missing required field: {field}"
    
    def test_model_has_cached_sample_info(self):
        """ConversationSample should cache basic sample info for display."""
        from axon.db.models import ConversationSample
        
        mapper = ConversationSample.__mapper__
        column_names = [c.key for c in mapper.columns]
        
        # Cached fields for displaying without re-querying samples table
        cached_fields = [
            'diagnosis',
            'age',
            'sex',
            'source_bank',
        ]
        
        for field in cached_fields:
            assert field in column_names, f"Missing cached field: {field}"
    
    @pytest.mark.asyncio
    async def test_create_conversation_sample(self, db_session):
        """Should be able to create a ConversationSample record."""
        from axon.db.models import Conversation, ConversationSample
        
        # Create a conversation first
        conversation = Conversation(
            id=str(uuid4()),
            title="Test Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        
        # Create a conversation sample
        sample = ConversationSample(
            id=str(uuid4()),
            conversation_id=conversation.id,
            sample_external_id="SAMPLE-001",
            sample_group="case",
            diagnosis="Alzheimer's Disease",
            age=75,
            sex="Female",
            source_bank="NIH NeuroBioBank",
        )
        db_session.add(sample)
        await db_session.commit()
        
        # Verify it was saved
        result = await db_session.execute(
            select(ConversationSample).where(
                ConversationSample.conversation_id == conversation.id
            )
        )
        saved = result.scalar_one()
        
        assert saved.sample_external_id == "SAMPLE-001"
        assert saved.sample_group == "case"
        assert saved.diagnosis == "Alzheimer's Disease"
        assert saved.age == 75
        assert saved.sex == "Female"
        assert saved.source_bank == "NIH NeuroBioBank"
        assert saved.added_at is not None
    
    @pytest.mark.asyncio
    async def test_conversation_has_samples_relationship(self, db_session):
        """Conversation should have a 'samples' relationship."""
        from axon.db.models import Conversation, ConversationSample
        from sqlalchemy.orm import selectinload
        
        # Create conversation with samples
        conv_id = str(uuid4())
        conversation = Conversation(
            id=conv_id,
            title="Test Conversation",
        )
        db_session.add(conversation)
        await db_session.commit()
        
        # Add samples
        for i, group in enumerate(["case", "case", "control"]):
            sample = ConversationSample(
                id=str(uuid4()),
                conversation_id=conv_id,
                sample_external_id=f"SAMPLE-{i:03d}",
                sample_group=group,
            )
            db_session.add(sample)
        await db_session.commit()
        
        # Reload conversation with samples eagerly loaded
        result = await db_session.execute(
            select(Conversation)
            .where(Conversation.id == conv_id)
            .options(selectinload(Conversation.samples))
        )
        loaded_conversation = result.scalar_one()
        
        # The conversation should have samples loaded
        assert len(loaded_conversation.samples) == 3, \
            "Conversation should have 3 samples via relationship"
    
    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session):
        """Deleting conversation should delete associated samples."""
        from axon.db.models import Conversation, ConversationSample
        
        # Create conversation with sample
        conv_id = str(uuid4())
        conversation = Conversation(id=conv_id, title="Test")
        db_session.add(conversation)
        await db_session.commit()
        
        sample = ConversationSample(
            id=str(uuid4()),
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",
            sample_group="case",
        )
        db_session.add(sample)
        await db_session.commit()
        
        # Delete conversation
        await db_session.delete(conversation)
        await db_session.commit()
        
        # Verify sample was cascade deleted
        result = await db_session.execute(
            select(ConversationSample).where(
                ConversationSample.conversation_id == conv_id
            )
        )
        samples = result.scalars().all()
        assert len(samples) == 0, "Samples should be cascade deleted"
    
    @pytest.mark.asyncio
    async def test_unique_sample_per_conversation(self, db_session):
        """Same sample shouldn't be added twice to same conversation."""
        from axon.db.models import Conversation, ConversationSample
        from sqlalchemy.exc import IntegrityError
        
        # Create conversation
        conv_id = str(uuid4())
        conversation = Conversation(id=conv_id, title="Test")
        db_session.add(conversation)
        await db_session.commit()
        
        # Add sample
        sample1 = ConversationSample(
            id=str(uuid4()),
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",
            sample_group="case",
        )
        db_session.add(sample1)
        await db_session.commit()
        
        # Try to add same sample again - should fail
        sample2 = ConversationSample(
            id=str(uuid4()),
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",  # Same external ID
            sample_group="case",
        )
        db_session.add(sample2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestConversationSampleGroups:
    """Tests for case/control grouping."""
    
    @pytest.mark.asyncio
    async def test_filter_by_group(self, db_session):
        """Should be able to filter samples by group."""
        from axon.db.models import Conversation, ConversationSample
        
        # Create conversation with mixed samples
        conv_id = str(uuid4())
        conversation = Conversation(id=conv_id, title="Test")
        db_session.add(conversation)
        await db_session.commit()
        
        # Add 3 cases and 2 controls
        for i in range(3):
            db_session.add(ConversationSample(
                id=str(uuid4()),
                conversation_id=conv_id,
                sample_external_id=f"CASE-{i:03d}",
                sample_group="case",
            ))
        for i in range(2):
            db_session.add(ConversationSample(
                id=str(uuid4()),
                conversation_id=conv_id,
                sample_external_id=f"CTRL-{i:03d}",
                sample_group="control",
            ))
        await db_session.commit()
        
        # Query cases only
        result = await db_session.execute(
            select(ConversationSample).where(
                ConversationSample.conversation_id == conv_id,
                ConversationSample.sample_group == "case",
            )
        )
        cases = result.scalars().all()
        assert len(cases) == 3
        
        # Query controls only
        result = await db_session.execute(
            select(ConversationSample).where(
                ConversationSample.conversation_id == conv_id,
                ConversationSample.sample_group == "control",
            )
        )
        controls = result.scalars().all()
        assert len(controls) == 2

