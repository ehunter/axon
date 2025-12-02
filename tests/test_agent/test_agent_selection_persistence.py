"""Tests for agent-level sample selection persistence.

These tests verify that the ToolBasedChatAgent properly persists
sample selections when tools are called.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4


class TestToolHandlerPersistence:
    """Tests for ToolHandler persistence integration."""
    
    def test_tool_handler_accepts_persistence_service(self):
        """ToolHandler should accept a persistence_service parameter."""
        from axon.agent.tools import ToolHandler
        import inspect
        
        sig = inspect.signature(ToolHandler.__init__)
        params = list(sig.parameters.keys())
        
        assert 'persistence_service' in params, \
            "ToolHandler should accept persistence_service parameter"
    
    def test_tool_handler_accepts_conversation_id(self):
        """ToolHandler should accept a conversation_id parameter."""
        from axon.agent.tools import ToolHandler
        import inspect
        
        sig = inspect.signature(ToolHandler.__init__)
        params = list(sig.parameters.keys())
        
        assert 'conversation_id' in params, \
            "ToolHandler should accept conversation_id parameter"


class TestAddToSelectionPersistence:
    """Tests for persisting samples when added to selection."""
    
    @pytest.mark.asyncio
    async def test_add_to_selection_persists_to_db(self, db_session):
        """Adding a sample to selection should persist it to the database."""
        from axon.agent.tools import ToolHandler
        from axon.agent.persistence import ConversationService
        from axon.db.models import Sample, ConversationSample
        
        # Create a real sample in the database
        sample = Sample(
            id=str(uuid4()),
            source_bank="NIH NeuroBioBank",
            external_id="TEST-SAMPLE-001",
            primary_diagnosis="Alzheimer's Disease",
            donor_age=75,
            donor_sex="Female",
            raw_data={},
        )
        db_session.add(sample)
        await db_session.commit()
        
        # Create conversation
        persistence_service = ConversationService(db_session)
        conv_id = await persistence_service.create_conversation("Test")
        
        # Create handler with persistence
        handler = ToolHandler(
            db_session=db_session,
            persistence_service=persistence_service,
            conversation_id=conv_id,
        )
        
        # Add sample to selection (group is "cases" not "case")
        result = await handler.handle_tool_call("add_to_selection", {
            "sample_id": "TEST-SAMPLE-001",
            "group": "cases",
        })
        
        # Verify it was persisted
        from sqlalchemy import select
        query = select(ConversationSample).where(
            ConversationSample.conversation_id == conv_id,
            ConversationSample.sample_external_id == "TEST-SAMPLE-001",
        )
        db_result = await db_session.execute(query)
        persisted = db_result.scalar_one_or_none()
        
        assert persisted is not None, "Sample should be persisted to database"
        assert persisted.sample_group == "case"
        assert persisted.diagnosis == "Alzheimer's Disease"


class TestRemoveFromSelectionPersistence:
    """Tests for persisting removal when sample removed from selection."""
    
    @pytest.mark.asyncio
    async def test_remove_from_selection_removes_from_db(self, db_session):
        """Removing a sample from selection should remove it from database."""
        from axon.agent.tools import ToolHandler
        from axon.agent.persistence import ConversationService
        from axon.db.models import Sample, ConversationSample
        
        # Create sample
        sample = Sample(
            id=str(uuid4()),
            source_bank="NIH NeuroBioBank",
            external_id="TEST-SAMPLE-002",
            primary_diagnosis="Control",
            donor_age=70,
            donor_sex="Male",
            raw_data={},
        )
        db_session.add(sample)
        await db_session.commit()
        
        # Create conversation and add sample
        persistence_service = ConversationService(db_session)
        conv_id = await persistence_service.create_conversation("Test")
        
        handler = ToolHandler(
            db_session=db_session,
            persistence_service=persistence_service,
            conversation_id=conv_id,
        )
        
        # Add then remove
        await handler.handle_tool_call("add_to_selection", {
            "sample_id": "TEST-SAMPLE-002",
            "group": "control",
        })
        await handler.handle_tool_call("remove_from_selection", {
            "sample_id": "TEST-SAMPLE-002",
        })
        
        # Verify it was removed from DB
        from sqlalchemy import select
        query = select(ConversationSample).where(
            ConversationSample.conversation_id == conv_id,
        )
        db_result = await db_session.execute(query)
        samples = db_result.scalars().all()
        
        assert len(samples) == 0, "Sample should be removed from database"


class TestClearSelectionPersistence:
    """Tests for persisting clear when selection cleared."""
    
    @pytest.mark.asyncio
    async def test_clear_selection_clears_from_db(self, db_session):
        """Clearing selection should remove all samples from database."""
        from axon.agent.tools import ToolHandler
        from axon.agent.persistence import ConversationService
        from axon.db.models import Sample, ConversationSample
        
        # Create samples
        for i in range(3):
            sample = Sample(
                id=str(uuid4()),
                source_bank="NIH",
                external_id=f"CLEAR-TEST-{i:03d}",
                primary_diagnosis="AD" if i < 2 else "Control",
                raw_data={},
            )
            db_session.add(sample)
        await db_session.commit()
        
        # Create conversation and add samples
        persistence_service = ConversationService(db_session)
        conv_id = await persistence_service.create_conversation("Test")
        
        handler = ToolHandler(
            db_session=db_session,
            persistence_service=persistence_service,
            conversation_id=conv_id,
        )
        
        # Add samples
        for i in range(3):
            await handler.handle_tool_call("add_to_selection", {
                "sample_id": f"CLEAR-TEST-{i:03d}",
                "group": "case" if i < 2 else "control",
            })
        
        # Clear selection
        await handler.handle_tool_call("clear_selection", {})
        
        # Verify DB is cleared
        from sqlalchemy import select
        query = select(ConversationSample).where(
            ConversationSample.conversation_id == conv_id,
        )
        db_result = await db_session.execute(query)
        samples = db_result.scalars().all()
        
        assert len(samples) == 0, "All samples should be removed from database"


class TestLoadConversationRestoresSelection:
    """Tests for restoring selection when loading a conversation."""
    
    @pytest.mark.asyncio
    async def test_load_conversation_restores_selection(self, db_session):
        """Loading a conversation should restore the sample selection."""
        from axon.agent.tools import ToolHandler
        from axon.agent.persistence import ConversationService
        from axon.db.models import Sample
        
        # Create samples
        sample = Sample(
            id=str(uuid4()),
            source_bank="NIH",
            external_id="RESTORE-TEST-001",
            primary_diagnosis="AD",
            donor_age=80,
            raw_data={},
        )
        db_session.add(sample)
        await db_session.commit()
        
        # Create conversation and add sample
        persistence_service = ConversationService(db_session)
        conv_id = await persistence_service.create_conversation("Test")
        
        # Save sample to selection via persistence service directly
        await persistence_service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="RESTORE-TEST-001",
            sample_group="case",
            diagnosis="AD",
            age=80,
        )
        
        # Create a NEW handler and load the selection
        handler = ToolHandler(
            db_session=db_session,
            persistence_service=persistence_service,
            conversation_id=conv_id,
        )
        
        # Load selection from DB
        await handler.load_selection_from_db()
        
        # Verify selection was restored
        assert len(handler.selection.cases) == 1
        assert handler.selection.cases[0].external_id == "RESTORE-TEST-001"
    
    def test_tool_handler_has_load_selection_from_db_method(self):
        """ToolHandler should have load_selection_from_db method."""
        from axon.agent.tools import ToolHandler
        
        assert hasattr(ToolHandler, 'load_selection_from_db'), \
            "ToolHandler should have load_selection_from_db method"


class TestAgentRestoresSelectionOnResume:
    """Tests for ToolBasedChatAgent restoring selection on resume."""
    
    @pytest.mark.asyncio
    async def test_agent_restores_selection_on_load_conversation(self, db_session):
        """Agent should restore selection when loading a conversation."""
        from axon.agent.chat_with_tools import ToolBasedChatAgent
        from axon.agent.persistence import ConversationService
        from axon.db.models import Sample
        
        # Create a sample
        sample = Sample(
            id=str(uuid4()),
            source_bank="NIH",
            external_id="AGENT-RESTORE-001",
            primary_diagnosis="PD",
            raw_data={},
        )
        db_session.add(sample)
        await db_session.commit()
        
        # Create conversation with persisted sample
        persistence_service = ConversationService(db_session)
        conv_id = await persistence_service.create_conversation("Test")
        await persistence_service.save_sample_to_selection(
            conversation_id=conv_id,
            sample_external_id="AGENT-RESTORE-001",
            sample_group="case",
            diagnosis="PD",
        )
        
        # Create agent with mocked Anthropic client
        with patch('axon.agent.chat_with_tools.AsyncAnthropic'):
            agent = ToolBasedChatAgent(
                db_session=db_session,
                anthropic_api_key="test-key",
                persistence_service=persistence_service,
            )
            
            # Load the conversation
            result = await agent.load_conversation(conv_id)
            
            assert result is True
            
            # Verify selection was restored
            selection = agent.get_current_selection()
            assert "AGENT-RESTORE-001" in selection

