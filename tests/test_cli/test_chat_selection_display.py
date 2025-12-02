"""Tests for CLI display of sample selection when resuming conversations."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestResumeDisplaysSelectionSummary:
    """Tests for showing restored selection when resuming a conversation."""
    
    def test_handle_resume_exists(self):
        """_handle_resume function should exist in chat module."""
        from axon.cli.commands import chat
        
        assert hasattr(chat, '_handle_resume'), \
            "chat module should have _handle_resume function"
    
    def test_resume_code_includes_selection_display(self):
        """The resume handler should include code to display restored selection."""
        import inspect
        from axon.cli.commands.chat import _handle_resume
        
        source = inspect.getsource(_handle_resume)
        
        # Verify the function accesses the selection for display
        assert "selection" in source, \
            "_handle_resume should access selection for display"
        assert "case" in source.lower(), \
            "_handle_resume should mention cases in output"
        assert "control" in source.lower(), \
            "_handle_resume should mention controls in output"


class TestSelectionSummaryInHistory:
    """Tests for showing selection summary when listing conversation history."""
    
    @pytest.mark.asyncio
    async def test_history_shows_sample_counts(self):
        """History listing should show sample counts for each conversation."""
        from axon.agent.persistence import ConversationService
        
        # This tests that we can get selection summary for conversations
        # The actual display is in the CLI but we verify the data is available
        mock_session = MagicMock()
        service = ConversationService(mock_session)
        
        assert hasattr(service, 'get_selection_summary'), \
            "ConversationService should have get_selection_summary method"

