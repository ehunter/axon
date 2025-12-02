"""Tests for conversation persistence.

These tests verify that conversations are properly saved to and loaded from
the database, enabling users to resume previous sessions.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession


class TestConversationServiceExists:
    """Tests that the conversation service exists and has required methods."""
    
    def test_conversation_service_importable(self):
        """ConversationService should be importable from axon.agent."""
        from axon.agent.persistence import ConversationService
        assert ConversationService is not None
    
    def test_service_has_create_conversation(self):
        """Service should have create_conversation method."""
        from axon.agent.persistence import ConversationService
        assert hasattr(ConversationService, 'create_conversation')
    
    def test_service_has_add_message(self):
        """Service should have add_message method."""
        from axon.agent.persistence import ConversationService
        assert hasattr(ConversationService, 'add_message')
    
    def test_service_has_load_conversation(self):
        """Service should have load_conversation method."""
        from axon.agent.persistence import ConversationService
        assert hasattr(ConversationService, 'load_conversation')
    
    def test_service_has_list_conversations(self):
        """Service should have list_conversations method."""
        from axon.agent.persistence import ConversationService
        assert hasattr(ConversationService, 'list_conversations')
    
    def test_service_has_update_title(self):
        """Service should have update_title method."""
        from axon.agent.persistence import ConversationService
        assert hasattr(ConversationService, 'update_title')


class TestConversationServiceInit:
    """Tests for ConversationService initialization."""
    
    def test_init_with_session(self):
        """Service should initialize with a database session."""
        from axon.agent.persistence import ConversationService
        
        mock_session = MagicMock(spec=AsyncSession)
        service = ConversationService(mock_session)
        
        assert service.db_session == mock_session


class TestConversationDataClass:
    """Tests for the ConversationData dataclass."""
    
    def test_conversation_data_exists(self):
        """ConversationData dataclass should exist."""
        from axon.agent.persistence import ConversationData
        assert ConversationData is not None
    
    def test_conversation_data_has_required_fields(self):
        """ConversationData should have required fields."""
        from axon.agent.persistence import ConversationData
        
        # Create an instance to verify fields exist
        data = ConversationData(
            id="test-123",
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            message_count=5,
        )
        
        assert data.id == "test-123"
        assert data.title == "Test Conversation"
        assert data.message_count == 5


class TestMessageDataClass:
    """Tests for the MessageData dataclass."""
    
    def test_message_data_exists(self):
        """MessageData dataclass should exist."""
        from axon.agent.persistence import MessageData
        assert MessageData is not None
    
    def test_message_data_has_required_fields(self):
        """MessageData should have required fields."""
        from axon.agent.persistence import MessageData
        
        data = MessageData(
            id="msg-123",
            role="user",
            content="Hello, world!",
            created_at=datetime.now(),
        )
        
        assert data.id == "msg-123"
        assert data.role == "user"
        assert data.content == "Hello, world!"


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.refresh = AsyncMock()
    return session


class TestCreateConversation:
    """Tests for creating new conversations."""
    
    @pytest.mark.asyncio
    async def test_create_conversation_returns_id(self, mock_db_session):
        """create_conversation should return the new conversation ID."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        
        # Mock the add and refresh behavior
        mock_db_session.refresh = AsyncMock()
        
        conv_id = await service.create_conversation(title="My Research")
        
        assert conv_id is not None
        assert isinstance(conv_id, str)
        assert len(conv_id) > 0
    
    @pytest.mark.asyncio
    async def test_create_conversation_with_optional_title(self, mock_db_session):
        """create_conversation should work without a title."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        mock_db_session.refresh = AsyncMock()
        
        conv_id = await service.create_conversation()
        
        assert conv_id is not None


class TestAddMessage:
    """Tests for adding messages to conversations."""
    
    @pytest.mark.asyncio
    async def test_add_message_returns_id(self, mock_db_session):
        """add_message should return the new message ID."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        mock_db_session.refresh = AsyncMock()
        
        msg_id = await service.add_message(
            conversation_id="conv-123",
            role="user",
            content="Find Alzheimer's samples",
        )
        
        assert msg_id is not None
        assert isinstance(msg_id, str)
    
    @pytest.mark.asyncio
    async def test_add_message_with_role_user(self, mock_db_session):
        """add_message should accept 'user' role."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        mock_db_session.refresh = AsyncMock()
        
        msg_id = await service.add_message(
            conversation_id="conv-123",
            role="user",
            content="Hello",
        )
        
        assert msg_id is not None
    
    @pytest.mark.asyncio
    async def test_add_message_with_role_assistant(self, mock_db_session):
        """add_message should accept 'assistant' role."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        mock_db_session.refresh = AsyncMock()
        
        msg_id = await service.add_message(
            conversation_id="conv-123",
            role="assistant",
            content="I found 10 samples...",
        )
        
        assert msg_id is not None


class TestListConversations:
    """Tests for listing past conversations."""
    
    @pytest.mark.asyncio
    async def test_list_conversations_returns_list(self, mock_db_session):
        """list_conversations should return a list of ConversationData."""
        from axon.agent.persistence import ConversationService, ConversationData
        
        service = ConversationService(mock_db_session)
        
        # Mock returning empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        conversations = await service.list_conversations()
        
        assert isinstance(conversations, list)
    
    @pytest.mark.asyncio
    async def test_list_conversations_with_limit(self, mock_db_session):
        """list_conversations should support limit parameter."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        # Should not raise
        conversations = await service.list_conversations(limit=10)
        
        assert isinstance(conversations, list)


class TestLoadConversation:
    """Tests for loading a specific conversation."""
    
    @pytest.mark.asyncio
    async def test_load_conversation_returns_data(self, mock_db_session):
        """load_conversation should return conversation with messages."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        
        # Mock a conversation with messages
        mock_conv = MagicMock()
        mock_conv.id = "conv-123"
        mock_conv.title = "Test"
        mock_conv.created_at = datetime.now()
        mock_conv.updated_at = datetime.now()
        mock_conv.messages = []
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        mock_db_session.execute.return_value = mock_result
        
        result = await service.load_conversation("conv-123")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_load_conversation_not_found(self, mock_db_session):
        """load_conversation should return None for non-existent ID."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await service.load_conversation("non-existent-id")
        
        assert result is None


class TestUpdateTitle:
    """Tests for updating conversation titles."""
    
    @pytest.mark.asyncio
    async def test_update_title_success(self, mock_db_session):
        """update_title should update the conversation title."""
        from axon.agent.persistence import ConversationService
        
        service = ConversationService(mock_db_session)
        
        # Mock finding the conversation
        mock_conv = MagicMock()
        mock_conv.id = "conv-123"
        mock_conv.title = "Old Title"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv
        mock_db_session.execute.return_value = mock_result
        
        success = await service.update_title("conv-123", "New Title")
        
        assert success is True


class TestTitleGeneration:
    """Tests for auto-generating conversation titles."""
    
    def test_generate_title_from_first_message(self):
        """Should generate a title from the first user message."""
        from axon.agent.persistence import generate_title_from_message
        
        title = generate_title_from_message("I need 12 Alzheimer's samples with RIN > 7")
        
        assert title is not None
        assert len(title) <= 100  # Reasonable max length
        assert len(title) > 0
    
    def test_generate_title_truncates_long_messages(self):
        """Should truncate very long messages."""
        from axon.agent.persistence import generate_title_from_message
        
        long_message = "I need samples " * 100
        title = generate_title_from_message(long_message)
        
        assert len(title) <= 100
    
    def test_generate_title_handles_empty_message(self):
        """Should handle empty messages gracefully."""
        from axon.agent.persistence import generate_title_from_message
        
        title = generate_title_from_message("")
        
        assert title is not None  # Should return a default title


class TestAgentIntegration:
    """Tests for agent integration with persistence."""
    
    def test_agent_accepts_persistence_service(self):
        """ToolBasedChatAgent should accept optional persistence_service parameter."""
        from axon.agent.chat_with_tools import ToolBasedChatAgent
        import inspect
        
        sig = inspect.signature(ToolBasedChatAgent.__init__)
        params = list(sig.parameters.keys())
        
        assert 'persistence_service' in params, \
            "ToolBasedChatAgent.__init__ should accept persistence_service parameter"
    
    def test_agent_has_conversation_id_property(self):
        """Agent should expose current conversation ID."""
        from axon.agent.chat_with_tools import ToolBasedChatAgent
        
        assert hasattr(ToolBasedChatAgent, 'conversation_id'), \
            "Agent should have conversation_id property"
    
    def test_agent_has_load_conversation_method(self):
        """Agent should have method to load an existing conversation."""
        from axon.agent.chat_with_tools import ToolBasedChatAgent
        
        assert hasattr(ToolBasedChatAgent, 'load_conversation'), \
            "Agent should have load_conversation method"


class TestCLICommands:
    """Tests for CLI command handlers."""
    
    def test_handle_history_command_exists(self):
        """CLI should have a handler for the history command."""
        from axon.cli.commands.chat import _handle_history
        import inspect
        
        assert callable(_handle_history)
        assert inspect.iscoroutinefunction(_handle_history)
    
    def test_handle_resume_command_exists(self):
        """CLI should have a handler for the resume command."""
        from axon.cli.commands.chat import _handle_resume
        import inspect
        
        assert callable(_handle_resume)
        assert inspect.iscoroutinefunction(_handle_resume)

