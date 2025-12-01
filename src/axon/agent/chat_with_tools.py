"""Tool-based chat agent for brain bank discovery.

This agent uses Anthropic's tool calling feature to ensure
Claude can ONLY access data through verified database queries.
This architectural constraint prevents hallucination.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.tools import TOOL_DEFINITIONS, ToolHandler


SYSTEM_PROMPT = """You are Axon, an expert brain bank research assistant. Your role is to help researchers find optimal brain tissue samples for their studies.

## CRITICAL: You Can ONLY Access Data Through Tools

You have access to tools that query the actual database. You MUST use these tools to access any sample data:

- **search_samples**: Search for samples with specific criteria
- **get_current_selection**: See what samples are currently selected
- **add_to_selection**: Add a verified sample to the selection
- **remove_from_selection**: Remove a sample from the selection
- **get_selection_statistics**: Get statistical comparison of cases vs controls
- **get_sample_details**: Get details for a specific sample
- **get_database_statistics**: Get aggregate database statistics

## ABSOLUTE RULES

1. **NEVER invent sample IDs** - Only use IDs returned by the search_samples tool
2. **NEVER invent values** - Only use RIN, PMI, age, Braak values from tool results
3. **If data is not available**, say "This information is not available in the dataset"
4. **Always use tools** to access sample data - do not make up any values

## Conversation Flow

1. Ask clarifying questions ONE AT A TIME:
   - "Do you also need controls?"
   - "What brain region would you like?"
   - "What will you use the tissue for?"

2. When you have enough criteria, use search_samples to find matching samples

3. Present ONLY the samples returned by the tool

4. Use add_to_selection to build the researcher's sample set

5. Use get_selection_statistics to show the statistical summary

## When Presenting Samples

- List samples with their EXACT IDs from the search results
- Include EXACT values (age, RIN, PMI) from the results
- If a field is not in the results, say "Not available"
- Summarize the cohort and list matching samples

## Example

Researcher: "I need Alzheimer's samples"
You: "Do you also need controls?"
Researcher: "Yes"
You: [Use search_samples tool with diagnosis="Alzheimer"]
You: "I found X samples matching your criteria. Here are the top matches: [exact data from tool results]"

Remember: You cannot present ANY sample data without first calling a tool to retrieve it."""


@dataclass
class Message:
    """A message in the conversation."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    """A conversation with message history."""
    id: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))
    
    def get_history_for_llm(self, max_messages: int = 20) -> list[dict]:
        """Get conversation history formatted for Claude API."""
        recent = self.messages[-max_messages:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
        ]


class ToolBasedChatAgent:
    """Chat agent that uses tools for all data access.
    
    This ensures Claude can ONLY present data that exists in the database.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        anthropic_api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the tool-based chat agent.
        
        Args:
            db_session: Database session
            anthropic_api_key: Anthropic API key for Claude
            model: Claude model to use
        """
        self.db_session = db_session
        self.client = AsyncAnthropic(api_key=anthropic_api_key)
        self.model = model
        self.conversation = Conversation(id="default")
        self.tool_handler = ToolHandler(db_session)
    
    def new_conversation(self) -> None:
        """Start a new conversation."""
        self.conversation = Conversation(
            id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        # Reset tool handler selection
        self.tool_handler.selection.clear()
    
    async def chat(self, message: str) -> str:
        """Send a message and get a response.
        
        Uses tool calling to ensure all data comes from the database.
        
        Args:
            message: User's message
            
        Returns:
            Assistant's response
        """
        # Add user message to history
        self.conversation.add_message("user", message)
        
        # Build messages for Claude
        messages = self.conversation.get_history_for_llm()
        
        # Call Claude with tools
        response = await self._call_with_tools(messages)
        
        # Add assistant response to history
        self.conversation.add_message("assistant", response)
        
        return response
    
    async def _call_with_tools(self, messages: list[dict], max_iterations: int = 10) -> str:
        """Call Claude with tool support, handling tool calls iteratively.
        
        Args:
            messages: Conversation messages
            max_iterations: Maximum tool call iterations to prevent infinite loops
            
        Returns:
            Final text response
        """
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Call Claude
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
            
            # Check if we need to handle tool calls
            if response.stop_reason == "tool_use":
                # Process all tool calls in this response
                tool_results = []
                assistant_content = []
                
                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({
                            "type": "text",
                            "text": block.text
                        })
                    elif block.type == "tool_use":
                        # Execute the tool
                        tool_result = await self.tool_handler.handle_tool_call(
                            block.name,
                            block.input
                        )
                        
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result
                        })
                
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                
                # Add tool results
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
            
            else:
                # No more tool calls, extract final text response
                text_parts = []
                for block in response.content:
                    if block.type == "text":
                        text_parts.append(block.text)
                
                return "\n".join(text_parts) if text_parts else "I apologize, but I couldn't generate a response."
        
        return "I apologize, but I reached the maximum number of tool calls. Please try simplifying your request."
    
    def get_current_selection(self) -> str:
        """Get the current sample selection summary."""
        return self.tool_handler.selection.to_summary()
    
    def get_selection_ids(self) -> dict[str, list[str]]:
        """Get the IDs of currently selected samples."""
        return {
            "cases": [s.external_id for s in self.tool_handler.selection.cases],
            "controls": [s.external_id for s in self.tool_handler.selection.controls],
        }

