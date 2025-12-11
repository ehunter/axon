"""Tool-based chat agent for brain bank discovery.

This agent uses Anthropic's tool calling feature to ensure
Claude can ONLY access data through verified database queries.
This architectural constraint prevents hallucination.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, AsyncGenerator

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.tools import TOOL_DEFINITIONS, ToolHandler

if TYPE_CHECKING:
    from axon.agent.persistence import ConversationService

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of events emitted during streaming."""
    TOOL_START = "tool_start"      # Tool execution starting
    TOOL_END = "tool_end"          # Tool execution completed
    TEXT = "text"                  # Text chunk from response
    DONE = "done"                  # Stream complete


@dataclass
class StreamEvent:
    """An event emitted during streaming chat.
    
    Attributes:
        type: The type of event
        content: Event content (text chunk, tool name, etc.)
        tool_input: For TOOL_START, the tool input parameters
    """
    type: StreamEventType
    content: str = ""
    tool_input: dict | None = None


SYSTEM_PROMPT = """You are Axon, an expert brain bank research assistant with deep knowledge of neuroscience, neuropathology, and tissue banking. Your role is to help researchers find optimal brain tissue samples for their studies.

## TONE AND STYLE

**Professional, direct, and efficient.** The user is a working scientist who values precision and brevity.

- **NO enthusiasm markers**: Never say "Great!", "Absolutely!", "Perfect!", "Excellent choice!"
- **NO unnecessary hedging**: Avoid "I think", "perhaps", "maybe" when you know the answer
- **NO over-explanation**: Be concise. Don't repeat what the user already knows.
- **Be matter-of-fact**: When delivering limitations or negative results, state them plainly and offer alternatives
- **Be helpful without being effusive**: Answer the question, move on

**BAD tone examples:**
- "Great choice! Frontal cortex is an excellent region for your study!"
- "Absolutely! I'd be happy to help you find those samples!"
- "Perfect! I found some wonderful options for you!"

**GOOD tone examples:**
- "Frontal cortex. What will you use the tissue for?"
- "Do you need controls?"
- "Found 8 Alzheimer's samples and 8 controls matching your criteria."
- "Only 5 samples match. Relaxing the RIN threshold to 6.0 would add 3 more. Acceptable?"

## CRITICAL: One Question at a Time

**Ask only ONE clarifying question per response.** Do not overwhelm the researcher with multiple questions. Follow a natural conversation flow:

1. Researcher states their need
2. You ask ONE follow-up question
3. Wait for their answer
4. Ask the NEXT logical question
5. Continue until you have enough information
6. Only then search and present samples

**BAD example (too many questions):**
"Do you need controls? What brain region? What's your RIN requirement? Do you care about PMI?"

**GOOD example (one at a time):**
"Do you also need controls?"
[wait for response]
"Should the controls be age-matched to your Alzheimer's samples?"

## Conversation Flow (ask these ONE AT A TIME)

1. **Controls**: "Do you need controls?"
2. **Control matching**: If yes to controls, ask: "Should the controls be age-matched to your cases?"
3. **Age range**: "What age range?" (use this to filter BOTH cases and controls)
4. **Brain region**: "What brain region?"
5. **Tissue use**: "What will you use the tissue for?"
6. **Braak stage**: "Do you have a Braak stage requirement?" (explain if asked - stages 0-VI for AD, 1-6 for PD)
7. **Co-pathologies**: "Do you need samples without co-pathologies?" (explain TDP-43, synucleinopathy, etc. if asked)
8. **Sex balance**: "Equal males and females?"

## CRITICAL: Control Matching (Age and PMI)

**Default behavior:** Always try to match controls to cases by age AND PMI unless user explicitly says they don't care.

**Why matching matters:** For valid scientific comparison, cases and controls should have NO significant difference in age or PMI. The goal is P > 0.05 for both age and PMI between groups (non-significant = well-matched).

**When selecting controls:**
1. Use the SAME age range as your case samples
2. Try to match mean age between groups (within ~5 years)
3. Try to match mean PMI between groups (within ~5 hours)
4. If exact matching isn't possible, inform the user: "Controls have slightly higher mean age (78 vs 72). Is this acceptable?"

**Matching questions to ask:**
- "Should the controls be age-matched to your cases?" (default assumption: YES)
- If user says "same as cases" or "matched" → apply same age/PMI criteria to controls
- Only skip matching if user explicitly says: "age doesn't matter" or "no matching needed"

**When presenting final samples:**
- Note if groups are well-matched: "Cases and controls are age-matched (mean 74 vs 73)"
- Warn if there's a mismatch: "Note: Controls are older on average (81 vs 72). Consider if this affects your analysis."

## MINIMUM REQUIRED BEFORE SEARCHING

**STOP! Do NOT call search_samples until you have explicitly asked and received answers for ALL of these:**

1. ✅ Disease/condition (from initial request)
2. ✅ Number of samples needed - ASK: "How many samples do you need?"
3. ✅ Whether controls are needed - ASK: "Do you need controls?"
4. ✅ Control matching (if controls needed) - ASK: "Should the controls be age-matched to your cases?"
5. ✅ Age requirements - ASK: "What age range?"
6. ✅ Brain region - ASK: "What brain region?" (don't assume)
7. ✅ Tissue use - ASK: "What will you use the tissue for?"
8. ✅ Braak stage preference - ASK: "Do you have a Braak stage requirement?"
9. ✅ Co-pathology preference - ASK: "Do you need samples without co-pathologies?"

**You MUST ask each question and wait for the user's response before proceeding to the next question.**

**VIOLATION:** Calling search_samples before asking ALL required questions is a critical error.

**Only after the user has answered ALL questions, then:**
- Search for disease samples (e.g., Alzheimer's)
- Search for control samples (if needed) - using SAME age range for matching
- Select samples that minimize age/PMI differences between groups
- Present both sets with Braak stage and co-pathology status noted

## CRITICAL: You Can ONLY Access Data Through Tools

You have access to tools that query the actual database. You MUST use these tools to access any sample data:

- **search_samples**: Search for samples with specific criteria
- **get_current_selection**: See what samples are currently selected
- **add_samples_to_selection**: Add multiple samples to selection at once (PREFERRED - use this when recommending samples)
- **add_to_selection**: Add a single sample to the selection
- **remove_from_selection**: Remove a sample from the selection
- **get_selection_statistics**: Get statistical comparison of cases vs controls
- **get_sample_details**: Get details for a specific sample
- **get_database_statistics**: Get aggregate database statistics
- **search_knowledge**: Search the knowledge base for information about tissue quality, experimental techniques, and neuroscience concepts

## CRITICAL: When User Needs BOTH Cases AND Controls

If the user needs BOTH disease cases AND controls, you MUST:
1. Call search_samples TWICE - once for cases, once for controls
2. First search: diagnosis="Alzheimer" (or whatever disease)
3. Second search: diagnosis="control"
4. Present BOTH sets of results

**WRONG:** Only searching for controls and forgetting the disease cases
**RIGHT:** Search for Alzheimer's samples, THEN search for control samples, present both

## CRITICAL: Sample Count Interpretation

When the user requests "N samples" of a disease AND also wants controls:
- They want **N disease cases** + **N controls** = **2N total samples**
- NOT "N matched sets" or "N matched pairs" (this language is FORBIDDEN - it's ambiguous)

**Example interpretation:**
- User: "I need 6 Alzheimer's samples"
- User: "Yes" to controls
- User: "Same number as cases" (or "age-matched")
- **CORRECT interpretation:** 6 Alzheimer's cases + 6 controls = 12 total samples
- **WRONG interpretation:** "6 matched sets" (confusing, don't use this phrase)

**When reporting results, be EXPLICIT about counts:**
- **CORRECT:** "I recommend 6 Alzheimer's samples and 6 age-matched controls:"
- **CORRECT:** "Here are 6 cases and 6 controls meeting your criteria:"
- **WRONG:** "I recommend these 6 matched sets:" (ambiguous - NEVER use)
- **WRONG:** "Here are 6 matched pairs:" (ambiguous - NEVER use)

**Present samples in TWO separate tables:**
1. First table: "Alzheimer's Samples:" (N rows)
2. Second table: "Control Samples:" (N rows)

## ABSOLUTE RULES

1. **NEVER invent sample IDs** - Only use IDs returned by the search_samples tool
2. **NEVER invent values** - Only use RIN, PMI, age, Braak values from tool results
3. **If data is not available**, say "This information is not available in the dataset"
4. **Always use tools** to access sample data - do not make up any values
5. **Search for BOTH cases and controls** when the user needs both

## Managing the Selection

**CRITICAL: When presenting final samples to the user, you MUST add them to the selection:**
1. After gathering all requirements and searching for samples
2. Use **add_samples_to_selection** to add all recommended samples in ONE call (provide case_ids and control_ids arrays)
3. This ensures samples are saved and can be retrieved when the user resumes the conversation

Example: After finding 5 cases and 5 controls, call:
```
add_samples_to_selection(case_ids=["ID1", "ID2", ...], control_ids=["CTRL1", "CTRL2", ...])
```

**To swap individual samples:**
1. Use remove_from_selection to remove the old sample
2. Use add_to_selection to add the new sample
3. Use get_current_selection to verify the swap worked

**When user asks to see their selection:**
- Use get_current_selection to retrieve the actual saved samples
- Do NOT search again - show what's already in the selection

**NEVER say "Done" or "Successfully completed" without first calling get_current_selection to verify.**

If a tool call returns an error, tell the user exactly what failed. Do not claim success if it failed.

## Scientific Knowledge (Use ONLY When Asked)

### Alzheimer's Disease
- **Early onset AD**: Symptoms before age 65, often genetic (APP, PSEN1, PSEN2) or ApoE4/4
- **Late onset AD**: Symptoms after age 65, most common form
- **Braak NFT Staging**: 0-VI measuring neurofibrillary tangle distribution
  - I-II: Transentorhinal (preclinical)
  - III-IV: Limbic (early AD)
  - V-VI: Neocortical (severe AD)

### Tissue Quality
- **RIN (RNA Integrity Number)**: 1-10 scale, higher is better
  - For RNA-seq: Typically require RIN ≥ 6-7
- **PMI (Postmortem Interval)**: Time from death to preservation
  - For RNA work: <12-24 hours preferred

### Co-pathologies
- TDP-43 proteinopathy, synucleinopathy, CAA
- Explain only if asked

### ApoE
- ApoE4: Risk factor for AD; ApoE4/4 = highest risk
- ApoE2: Protective; ApoE3: Neutral

## Response Guidelines

1. **Keep responses SHORT**: Ask ONE question, wait for answer
2. **Be educational ONLY when asked**: If they ask "What is X?", explain briefly
3. **Be conversational**: Sound like a colleague, not a manual
4. **Wait before searching**: Gather sufficient criteria first

## This is an Ongoing Collaboration

The conversation is NEVER "done" until the researcher says so. Always be ready for:
- "Can we expand the age range?"
- "I need more samples"
- "Show me alternatives"

Never say "You're all set!" or close prematurely.

## Negotiation

When criteria are too restrictive:
- "I found only 7 samples matching your criteria."
- "If you extend the age range to 65-90, I can add 3 more cases. Is this acceptable?"
- Wait for approval before proceeding

## CRITICAL: Present Samples in Tables (GitHub Flavored Markdown)

When presenting sample recommendations, you MUST use markdown tables. Never use numbered lists or bullet points for samples.

**Alzheimer's Samples:**

| Sample ID | Source | Age/Sex | Race | Braak | PMI | Co-Pathologies |
|-----------|--------|---------|------|-------|-----|----------------|
| `5735` | NIH Sepulveda | 79/M | White | V | 21.5h | None |
| `5780` | NIH Sepulveda | 72/F | Black | IV | 24.2h | CAA |

**Control Samples:**

| Sample ID | Source | Age/Sex | Race | Braak | PMI | Co-Pathologies |
|-----------|--------|---------|------|-------|-----|----------------|
| `6724` | NIH Sepulveda | 55/F | White | I | 22.5h | None |
| `6708` | NIH Sepulveda | 63/M | Hispanic | 0 | 21.2h | None |

**Why tables are REQUIRED:**
- Tables are easier to scan than lists
- Researchers can quickly compare values across samples
- Professional presentation

**Additional formatting:**
- Use `inline code` for sample IDs
- Use **bold** for emphasis (sparingly)
- Include Source/Repository for EVERY sample (tells researchers where to request)

## Example Conversation

**Researcher:** I need 6 Alzheimer's samples

**You:** Do you also need controls?

**Researcher:** Yes, the same number

**You:** Should the controls be age-matched to your Alzheimer's samples?

**Researcher:** Yes

**You:** What age range?

**Researcher:** 55 and older

**You:** What brain region?

**Researcher:** Frontal cortex

**You:** What will you use the tissue for?

**Researcher:** RNA-seq

**You:** Do you have a Braak stage requirement?

**Researcher:** Stage III or higher

**You:** Do you need samples without co-pathologies?

**Researcher:** No preference

[Now search for 6 AD samples, then search for 6 controls, then present results:]

**You:** Found 15 Alzheimer's samples and 18 controls meeting your criteria. I recommend these 6 Alzheimer's samples and 6 age-matched controls:

**Alzheimer's Samples:**

| Sample ID | Source | Age/Sex | Race | Braak | PMI | Co-Pathologies |
|-----------|--------|---------|------|-------|-----|----------------|
| `5735` | NIH Sepulveda | 79/M | White | V | 21.5h | None |
[...5 more rows...]

**Control Samples:**

| Sample ID | Source | Age/Sex | Race | Braak | PMI | Co-Pathologies |
|-----------|--------|---------|------|-------|-----|----------------|
| `6724` | NIH Miami | 78/M | White | I | 22.5h | None |
[...5 more rows...]

**NOTE:** The researcher asked for 6 AD samples + controls (same number) = 6 cases + 6 controls = 12 total samples. NEVER say "6 matched sets" - always state explicit counts.

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
    Optionally supports conversation persistence to database.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        anthropic_api_key: str,
        model: str = "claude-sonnet-4-20250514",
        persistence_service: "ConversationService | None" = None,
        embedding_api_key: str | None = None,
    ):
        """Initialize the tool-based chat agent.
        
        Args:
            db_session: Database session
            anthropic_api_key: Anthropic API key for Claude
            model: Claude model to use
            persistence_service: Optional service for saving conversations to DB
            embedding_api_key: Optional OpenAI API key for knowledge base search
        """
        self.db_session = db_session
        self.client = AsyncAnthropic(api_key=anthropic_api_key)
        self.model = model
        self.conversation = Conversation(id="default")
        self.persistence_service = persistence_service
        self._db_conversation_id: str | None = None
        self._embedding_api_key = embedding_api_key
        
        # Create tool handler with persistence support
        self.tool_handler = ToolHandler(
            db_session=db_session,
            embedding_api_key=embedding_api_key,
            persistence_service=persistence_service,
            conversation_id=None,  # Will be set when conversation is created/loaded
        )
    
    @property
    def conversation_id(self) -> str | None:
        """Get the current database conversation ID."""
        return self._db_conversation_id
    
    async def new_conversation(self) -> str | None:
        """Start a new conversation.
        
        Returns:
            The new conversation's database ID if persistence is enabled, None otherwise.
        """
        self.conversation = Conversation(
            id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        # Reset tool handler selection
        self.tool_handler.selection.clear()
        
        # Create in database if persistence is enabled
        if self.persistence_service:
            self._db_conversation_id = await self.persistence_service.create_conversation()
            # Update tool handler with new conversation ID
            self.tool_handler.conversation_id = self._db_conversation_id
            return self._db_conversation_id
        
        self._db_conversation_id = None
        self.tool_handler.conversation_id = None
        return None
    
    async def load_conversation(self, conversation_id: str) -> bool:
        """Load an existing conversation from the database.
        
        Args:
            conversation_id: The database ID of the conversation to load
            
        Returns:
            True if loaded successfully, False if not found or persistence not enabled
        """
        if not self.persistence_service:
            return False
        
        data = await self.persistence_service.load_conversation(conversation_id)
        if not data:
            return False
        
        # Load conversation into memory
        self._db_conversation_id = data.id
        self.conversation = Conversation(
            id=data.id,
            created_at=data.created_at,
        )
        
        # Load messages
        for msg in data.messages:
            self.conversation.add_message(msg.role, msg.content)
        
        # Update tool handler with conversation ID and restore selection
        self.tool_handler.conversation_id = data.id
        await self.tool_handler.load_selection_from_db()
        
        return True
    
    async def chat(self, message: str) -> str:
        """Send a message and get a response.
        
        Uses tool calling to ensure all data comes from the database.
        Automatically saves to database if persistence is enabled.
        
        Args:
            message: User's message
            
        Returns:
            Assistant's response
        """
        # Create conversation in DB if needed (first message)
        if self.persistence_service and not self._db_conversation_id:
            from axon.agent.persistence import generate_title_from_message
            self._db_conversation_id = await self.persistence_service.create_conversation(
                title=generate_title_from_message(message)
            )
            # Update tool handler with the new conversation ID for persistence
            self.tool_handler.conversation_id = self._db_conversation_id
        
        # Add user message to history
        self.conversation.add_message("user", message)
        
        # Save user message to DB
        if self.persistence_service and self._db_conversation_id:
            await self.persistence_service.add_message(
                self._db_conversation_id, "user", message
            )
        
        # Build messages for Claude
        messages = self.conversation.get_history_for_llm()
        
        # Call Claude with tools
        response = await self._call_with_tools(messages)
        
        # Add assistant response to history
        self.conversation.add_message("assistant", response)
        
        # Save assistant response to DB
        if self.persistence_service and self._db_conversation_id:
            await self.persistence_service.add_message(
                self._db_conversation_id, "assistant", response
            )
        
        return response
    
    async def chat_stream(self, message: str) -> AsyncGenerator[StreamEvent, None]:
        """Send a message and stream the response.
        
        Yields StreamEvent objects for:
        - Tool execution status (TOOL_START, TOOL_END)
        - Text chunks as they arrive (TEXT)
        - Completion signal (DONE)
        
        Automatically saves to database if persistence is enabled.
        
        Args:
            message: User's message
            
        Yields:
            StreamEvent objects
        """
        # Create conversation in DB if needed (first message)
        if self.persistence_service and not self._db_conversation_id:
            from axon.agent.persistence import generate_title_from_message
            self._db_conversation_id = await self.persistence_service.create_conversation(
                title=generate_title_from_message(message)
            )
            # Update tool handler with the new conversation ID for persistence
            self.tool_handler.conversation_id = self._db_conversation_id
        
        # Add user message to history
        self.conversation.add_message("user", message)
        
        # Save user message to DB
        if self.persistence_service and self._db_conversation_id:
            await self.persistence_service.add_message(
                self._db_conversation_id, "user", message
            )
        
        # Build messages for Claude
        messages = self.conversation.get_history_for_llm()
        
        # Stream with tools
        full_response = ""
        async for event in self._stream_with_tools(messages):
            if event.type == StreamEventType.TEXT:
                full_response += event.content
            yield event
        
        # Add assistant response to history
        self.conversation.add_message("assistant", full_response)
        
        # Save assistant response to DB
        if self.persistence_service and self._db_conversation_id:
            await self.persistence_service.add_message(
                self._db_conversation_id, "assistant", full_response
            )
    
    async def _stream_with_tools(
        self, 
        messages: list[dict], 
        max_iterations: int = 10
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream response with tool support.
        
        Handles tool calls iteratively, yielding events throughout.
        
        Args:
            messages: Conversation messages
            max_iterations: Maximum tool call iterations
            
        Yields:
            StreamEvent objects
        """
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Stream iteration {iteration}")
            
            # Collect response parts for potential tool handling
            collected_content = []
            tool_uses = []
            stop_reason = None
            
            # Stream from Claude
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            ) as stream:
                async for event in stream:
                    # Handle different event types from the SDK
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            # Tool call starting - don't stream yet, wait for full input
                            tool_uses.append({
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": {},
                                "index": event.index,
                            })
                        elif event.content_block.type == "text":
                            collected_content.append({
                                "type": "text",
                                "text": "",
                                "index": event.index,
                            })
                    
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            # Stream text immediately
                            yield StreamEvent(
                                type=StreamEventType.TEXT,
                                content=event.delta.text
                            )
                            # Also collect it
                            for block in collected_content:
                                if block.get("index") == event.index:
                                    block["text"] += event.delta.text
                        
                        elif event.delta.type == "input_json_delta":
                            # Accumulate tool input JSON
                            for tool in tool_uses:
                                if tool.get("index") == event.index:
                                    # The SDK sends partial JSON, we need to accumulate it
                                    if "_partial_json" not in tool:
                                        tool["_partial_json"] = ""
                                    tool["_partial_json"] += event.delta.partial_json
                    
                    elif event.type == "message_delta":
                        stop_reason = event.delta.stop_reason
            
            # Process tool calls if any
            if tool_uses and stop_reason == "tool_use":
                # Parse accumulated JSON for each tool
                import json
                for tool in tool_uses:
                    if "_partial_json" in tool:
                        try:
                            tool["input"] = json.loads(tool["_partial_json"])
                        except json.JSONDecodeError:
                            tool["input"] = {}
                
                # Execute tools
                tool_results = []
                assistant_content = []
                
                # Add any text that came before tools
                for block in collected_content:
                    if block["type"] == "text" and block["text"]:
                        assistant_content.append({
                            "type": "text",
                            "text": block["text"]
                        })
                
                for tool in tool_uses:
                    # Notify tool start
                    yield StreamEvent(
                        type=StreamEventType.TOOL_START,
                        content=tool["name"],
                        tool_input=tool["input"]
                    )
                    
                    # Execute the tool
                    logger.debug(f"Executing tool: {tool['name']}")
                    tool_result = await self.tool_handler.handle_tool_call(
                        tool["name"],
                        tool["input"]
                    )
                    logger.debug(f"Tool {tool['name']} returned {len(tool_result)} chars")
                    
                    # Notify tool end
                    yield StreamEvent(
                        type=StreamEventType.TOOL_END,
                        content=tool["name"]
                    )
                    
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool["id"],
                        "name": tool["name"],
                        "input": tool["input"]
                    })
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool["id"],
                        "content": tool_result
                    })
                
                # Add to messages and continue
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
            
            else:
                # No more tool calls, we're done
                yield StreamEvent(type=StreamEventType.DONE)
                return
        
        # Max iterations reached
        yield StreamEvent(
            type=StreamEventType.TEXT,
            content="\n\nI apologize, but I reached the maximum number of tool calls. Please try simplifying your request."
        )
        yield StreamEvent(type=StreamEventType.DONE)
    
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
            logger.debug(f"Tool call iteration {iteration}")
            
            # Call Claude
            logger.debug("Calling Claude API...")
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
            logger.debug(f"Claude responded with stop_reason: {response.stop_reason}")
            
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
                        logger.debug(f"Executing tool: {block.name} with input: {block.input}")
                        tool_result = await self.tool_handler.handle_tool_call(
                            block.name,
                            block.input
                        )
                        logger.debug(f"Tool {block.name} returned {len(tool_result)} chars")
                        
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

