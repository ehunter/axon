"""Tests for sample selection persistence in ConversationService.

These tests verify that sample selections (cases/controls) can be
persisted and restored when resuming conversations.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock

from sqlalchemy import select


class TestConversationServiceSampleMethods:
    """Tests for ConversationService sample persistence methods."""
    
    def test_service_has_save_sample_method(self):
        """ConversationService should have save_sample_to_selection method."""
        from axon.agent.persistence import ConversationService
        
        assert hasattr(ConversationService, 'save_sample_to_selection'), \
            "ConversationService should have save_sample_to_selection method"
    
    def test_service_has_remove_sample_method(self):
        """ConversationService should have remove_sample_from_selection method."""
        from axon.agent.persistence import ConversationService
        
        assert hasattr(ConversationService, 'remove_sample_from_selection'), \
            "ConversationService should have remove_sample_from_selection method"
    
    def test_service_has_load_selection_method(self):
        """ConversationService should have load_selection method."""
        from axon.agent.persistence import ConversationService
        
        assert hasattr(ConversationService, 'load_selection'), \
            "ConversationService should have load_selection method"
    
    def test_service_has_clear_selection_method(self):
        """ConversationService should have clear_selection method."""
        from axon.agent.persistence import ConversationService
        
        assert hasattr(ConversationService, 'clear_selection'), \
            "ConversationService should have clear_selection method"


class TestSaveSampleToSelection:
    """Tests for saving samples to selection."""
    
    @pytest.mark.asyncio
    async def test_save_case_sample(self, db_session):
        """Should be able to save a case sample to selection."""
        from axon.agent.persistence import ConversationService
        from axon.db.models import Conversation, ConversationSample
        
        service = ConversationService(db_session)
        
        # Create conversation
        conv_id = await service.create_conversation("Test")
        
        # Save a case sample
        result = await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",
            sample_group="case",
            diagnosis="Alzheimer's Disease",
            age=75,
            sex="Female",
            source_bank="NIH NeuroBioBank",
        )
        
        assert result is True
        
        # Verify it was saved
        query = select(ConversationSample).where(
            ConversationSample.conversation_id == conv_id
        )
        db_result = await db_session.execute(query)
        saved = db_result.scalar_one()
        
        assert saved.sample_external_id == "SAMPLE-001"
        assert saved.sample_group == "case"
        assert saved.diagnosis == "Alzheimer's Disease"
    
    @pytest.mark.asyncio
    async def test_save_control_sample(self, db_session):
        """Should be able to save a control sample to selection."""
        from axon.agent.persistence import ConversationService
        from axon.db.models import ConversationSample
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        result = await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="CTRL-001",
            sample_group="control",
            diagnosis="Control",
            age=70,
            sex="Male",
            source_bank="Harvard Brain Bank",
        )
        
        assert result is True
        
        # Verify it was saved as control
        query = select(ConversationSample).where(
            ConversationSample.conversation_id == conv_id,
            ConversationSample.sample_group == "control"
        )
        db_result = await db_session.execute(query)
        saved = db_result.scalar_one()
        
        assert saved.sample_external_id == "CTRL-001"
    
    @pytest.mark.asyncio
    async def test_save_duplicate_sample_fails(self, db_session):
        """Saving same sample twice should return False."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        # Save first time
        result1 = await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",
            sample_group="case",
        )
        assert result1 is True
        
        # Try to save again
        result2 = await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",
            sample_group="case",
        )
        assert result2 is False, "Duplicate sample should return False"


class TestRemoveSampleFromSelection:
    """Tests for removing samples from selection."""
    
    @pytest.mark.asyncio
    async def test_remove_existing_sample(self, db_session):
        """Should be able to remove a sample from selection."""
        from axon.agent.persistence import ConversationService
        from axon.db.models import ConversationSample
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        # Add sample
        await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",
            sample_group="case",
        )
        
        # Remove it
        result = await service.remove_sample_from_selection(
            conversation_id=conv_id,
            sample_external_id="SAMPLE-001",
        )
        
        assert result is True
        
        # Verify it's gone
        query = select(ConversationSample).where(
            ConversationSample.conversation_id == conv_id
        )
        db_result = await db_session.execute(query)
        samples = db_result.scalars().all()
        assert len(samples) == 0
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_sample_returns_false(self, db_session):
        """Removing non-existent sample should return False."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        result = await service.remove_sample_from_selection(
            conversation_id=conv_id,
            sample_external_id="DOES-NOT-EXIST",
        )
        
        assert result is False


class TestLoadSelection:
    """Tests for loading sample selection."""
    
    @pytest.mark.asyncio
    async def test_load_empty_selection(self, db_session):
        """Loading selection for conversation with no samples."""
        from axon.agent.persistence import ConversationService
        from axon.agent.tools import SampleSelection
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        selection = await service.load_selection(conv_id)
        
        assert isinstance(selection, SampleSelection)
        assert len(selection.cases) == 0
        assert len(selection.controls) == 0
    
    @pytest.mark.asyncio
    async def test_load_selection_with_samples(self, db_session):
        """Loading selection should restore cases and controls."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        # Add cases and controls
        await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="CASE-001",
            sample_group="case",
            diagnosis="Alzheimer's",
            age=75,
            sex="Female",
            source_bank="NIH",
        )
        await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="CASE-002",
            sample_group="case",
            diagnosis="Alzheimer's",
            age=80,
            sex="Male",
            source_bank="NIH",
        )
        await service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="CTRL-001",
            sample_group="control",
            diagnosis="Control",
            age=72,
            sex="Female",
            source_bank="Harvard",
        )
        
        # Load selection
        selection = await service.load_selection(conv_id)
        
        assert len(selection.cases) == 2
        assert len(selection.controls) == 1
        
        # Verify case details were restored
        case_ids = {s.external_id for s in selection.cases}
        assert "CASE-001" in case_ids
        assert "CASE-002" in case_ids
        
        # Verify control details
        assert selection.controls[0].external_id == "CTRL-001"
        assert selection.controls[0].diagnosis == "Control"
    
    @pytest.mark.asyncio
    async def test_load_selection_nonexistent_conversation(self, db_session):
        """Loading selection for non-existent conversation returns empty."""
        from axon.agent.persistence import ConversationService
        from axon.agent.tools import SampleSelection
        
        service = ConversationService(db_session)
        
        selection = await service.load_selection("nonexistent-id")
        
        assert isinstance(selection, SampleSelection)
        assert len(selection.cases) == 0
        assert len(selection.controls) == 0


class TestClearSelection:
    """Tests for clearing sample selection."""
    
    @pytest.mark.asyncio
    async def test_clear_selection(self, db_session):
        """Should be able to clear all samples from selection."""
        from axon.agent.persistence import ConversationService
        from axon.db.models import ConversationSample
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        # Add multiple samples
        for i in range(3):
            await service.save_sample_to_selection(
                conversation_id=conv_id,
                sample_external_id=f"SAMPLE-{i:03d}",
                sample_group="case",
            )
        
        # Clear selection
        result = await service.clear_selection(conv_id)
        assert result is True
        
        # Verify all samples are gone
        query = select(ConversationSample).where(
            ConversationSample.conversation_id == conv_id
        )
        db_result = await db_session.execute(query)
        samples = db_result.scalars().all()
        assert len(samples) == 0
    
    @pytest.mark.asyncio
    async def test_clear_selection_empty_is_ok(self, db_session):
        """Clearing empty selection should succeed."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        result = await service.clear_selection(conv_id)
        assert result is True


class TestGetSelectionSummary:
    """Tests for getting selection summary."""
    
    @pytest.mark.asyncio
    async def test_get_selection_summary(self, db_session):
        """Should be able to get a summary of selection counts."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(db_session)
        conv_id = await service.create_conversation("Test")
        
        # Add samples
        for i in range(3):
            await service.save_sample_to_selection(
                conversation_id=conv_id,
                sample_external_id=f"CASE-{i:03d}",
                sample_group="case",
            )
        for i in range(2):
            await service.save_sample_to_selection(
                conversation_id=conv_id,
                sample_external_id=f"CTRL-{i:03d}",
                sample_group="control",
            )
        
        summary = await service.get_selection_summary(conv_id)
        
        assert summary["case_count"] == 3
        assert summary["control_count"] == 2
        assert summary["total"] == 5






