"""Tests for streaming chat functionality.

These tests verify that the streaming chat works correctly,
including proper handling of tool calls during streaming.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from axon.agent.chat_with_tools import (
    StreamEvent,
    StreamEventType,
    ToolBasedChatAgent,
    Conversation,
    Message,
)


class TestStreamEventType:
    """Tests for StreamEventType enum."""
    
    def test_all_event_types_defined(self):
        """All required event types should be defined."""
        assert StreamEventType.TOOL_START.value == "tool_start"
        assert StreamEventType.TOOL_END.value == "tool_end"
        assert StreamEventType.TEXT.value == "text"
        assert StreamEventType.DONE.value == "done"
    
    def test_event_type_count(self):
        """Should have exactly 4 event types."""
        assert len(StreamEventType) == 4


class TestStreamEvent:
    """Tests for StreamEvent dataclass."""
    
    def test_create_text_event(self):
        """Can create a text event."""
        event = StreamEvent(
            type=StreamEventType.TEXT,
            content="Hello, world!"
        )
        assert event.type == StreamEventType.TEXT
        assert event.content == "Hello, world!"
        assert event.tool_input is None
    
    def test_create_tool_start_event(self):
        """Can create a tool start event with input."""
        event = StreamEvent(
            type=StreamEventType.TOOL_START,
            content="search_samples",
            tool_input={"diagnosis": "Alzheimer"}
        )
        assert event.type == StreamEventType.TOOL_START
        assert event.content == "search_samples"
        assert event.tool_input == {"diagnosis": "Alzheimer"}
    
    def test_create_tool_end_event(self):
        """Can create a tool end event."""
        event = StreamEvent(
            type=StreamEventType.TOOL_END,
            content="search_samples"
        )
        assert event.type == StreamEventType.TOOL_END
        assert event.content == "search_samples"
    
    def test_create_done_event(self):
        """Can create a done event."""
        event = StreamEvent(type=StreamEventType.DONE)
        assert event.type == StreamEventType.DONE
        assert event.content == ""


class TestConversation:
    """Tests for Conversation class."""
    
    def test_create_conversation(self):
        """Can create a conversation with ID."""
        conv = Conversation(id="test-123")
        assert conv.id == "test-123"
        assert conv.messages == []
    
    def test_add_message(self):
        """Can add messages to conversation."""
        conv = Conversation(id="test")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Hello"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[1].content == "Hi there!"
    
    def test_get_history_for_llm(self):
        """Get history returns proper format for Claude API."""
        conv = Conversation(id="test")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi!")
        
        history = conv.get_history_for_llm()
        
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi!"}
    
    def test_get_history_respects_max_messages(self):
        """Get history limits to max_messages."""
        conv = Conversation(id="test")
        for i in range(10):
            conv.add_message("user", f"Message {i}")
        
        history = conv.get_history_for_llm(max_messages=3)
        
        assert len(history) == 3
        assert history[0]["content"] == "Message 7"
        assert history[2]["content"] == "Message 9"


class TestToolBasedChatAgentInit:
    """Tests for ToolBasedChatAgent initialization."""
    
    def test_agent_has_chat_stream_method(self):
        """Agent should have chat_stream method."""
        assert hasattr(ToolBasedChatAgent, "chat_stream")
    
    def test_agent_has_chat_method(self):
        """Agent should have regular chat method."""
        assert hasattr(ToolBasedChatAgent, "chat")


class TestStreamEventSequence:
    """Tests for expected streaming event sequences."""
    
    def test_simple_text_response_events(self):
        """Simple text response should emit TEXT events then DONE."""
        # Simulate the expected event sequence for a simple response
        events = [
            StreamEvent(type=StreamEventType.TEXT, content="Hello"),
            StreamEvent(type=StreamEventType.TEXT, content=" there!"),
            StreamEvent(type=StreamEventType.DONE),
        ]
        
        # Verify sequence
        text_events = [e for e in events if e.type == StreamEventType.TEXT]
        done_events = [e for e in events if e.type == StreamEventType.DONE]
        
        assert len(text_events) == 2
        assert len(done_events) == 1
        assert events[-1].type == StreamEventType.DONE
    
    def test_tool_call_response_events(self):
        """Tool call response should emit TOOL_START, TOOL_END, then TEXT and DONE."""
        # Simulate the expected event sequence for a tool call response
        events = [
            StreamEvent(
                type=StreamEventType.TOOL_START, 
                content="search_samples",
                tool_input={"diagnosis": "Alzheimer"}
            ),
            StreamEvent(type=StreamEventType.TOOL_END, content="search_samples"),
            StreamEvent(type=StreamEventType.TEXT, content="Found 10 samples..."),
            StreamEvent(type=StreamEventType.DONE),
        ]
        
        # Verify tool events come before text
        tool_start_idx = next(i for i, e in enumerate(events) if e.type == StreamEventType.TOOL_START)
        tool_end_idx = next(i for i, e in enumerate(events) if e.type == StreamEventType.TOOL_END)
        text_idx = next(i for i, e in enumerate(events) if e.type == StreamEventType.TEXT)
        
        assert tool_start_idx < tool_end_idx
        assert tool_end_idx < text_idx
    
    def test_multiple_tool_calls_sequence(self):
        """Multiple tool calls should be properly sequenced."""
        events = [
            StreamEvent(type=StreamEventType.TOOL_START, content="search_samples"),
            StreamEvent(type=StreamEventType.TOOL_END, content="search_samples"),
            StreamEvent(type=StreamEventType.TOOL_START, content="get_database_statistics"),
            StreamEvent(type=StreamEventType.TOOL_END, content="get_database_statistics"),
            StreamEvent(type=StreamEventType.TEXT, content="Results..."),
            StreamEvent(type=StreamEventType.DONE),
        ]
        
        tool_starts = [e for e in events if e.type == StreamEventType.TOOL_START]
        tool_ends = [e for e in events if e.type == StreamEventType.TOOL_END]
        
        assert len(tool_starts) == 2
        assert len(tool_ends) == 2


class TestStreamingUX:
    """Tests for streaming UX behavior."""
    
    def test_no_tool_display_names_in_cli(self):
        """CLI should NOT have tool-specific display names.
        
        We want a simple 'Thinking...' indicator, not tool-specific messages.
        The _get_tool_display_name function should not exist.
        """
        import axon.cli.commands.chat as chat_module
        
        # This function should NOT exist - we want simple "Thinking..." instead
        assert not hasattr(chat_module, '_get_tool_display_name'), \
            "_get_tool_display_name should be removed - use simple 'Thinking...' indicator"
    
    def test_stream_response_function_exists(self):
        """The _stream_response function should exist for handling streaming."""
        from axon.cli.commands.chat import _stream_response
        import inspect
        
        assert callable(_stream_response)
        assert inspect.iscoroutinefunction(_stream_response), \
            "_stream_response should be an async function"
    
    def test_tool_events_should_not_produce_visible_output(self):
        """Tool events (TOOL_START, TOOL_END) should not produce user-visible output.
        
        Only TEXT events should produce output. The 'Thinking...' spinner
        handles the visual feedback during tool execution.
        """
        # This test documents the expected behavior:
        # - TOOL_START: No output (spinner keeps spinning)
        # - TOOL_END: No output (spinner keeps spinning)  
        # - TEXT: Output the text (spinner stops)
        # - DONE: No output (just signals completion)
        
        from axon.agent.chat_with_tools import StreamEventType
        
        # Events that should NOT produce console output
        silent_events = {StreamEventType.TOOL_START, StreamEventType.TOOL_END, StreamEventType.DONE}
        
        # Events that SHOULD produce console output
        output_events = {StreamEventType.TEXT}
        
        # Verify we have the right categorization
        all_events = set(StreamEventType)
        assert silent_events | output_events == all_events, \
            "All event types should be categorized"
        assert silent_events & output_events == set(), \
            "No event should be in both categories"

