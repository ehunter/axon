"""Tool-based chat agent for brain bank discovery.

This agent uses Anthropic's tool calling feature to ensure
Claude can ONLY access data through verified database queries.
This architectural constraint prevents hallucination.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.tools import TOOL_DEFINITIONS, ToolHandler

logger = logging.getLogger(__name__)


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

1. **Controls**: "Do you also need controls?"
2. **Age matching**: "Do your controls need to be age-matched to your [disease] samples?"
3. **Brain region**: "What brain region would you like?"
4. **Tissue use**: "What will you use the tissue for?" (RNA-seq, proteomics, etc.)
5. **Sex balance**: "Do you need an equal number of males and females?"
6. **Co-pathologies**: "Do you care about co-pathologies?" (explain if asked)

## MINIMUM REQUIRED BEFORE SEARCHING

**DO NOT search until you have ALL of these:**
1. ✅ Disease/condition (from initial request)
2. ✅ Number of samples needed
3. ✅ Whether controls are needed (yes/no)
4. ✅ Age requirements (if controls needed)
5. ✅ Brain region
6. ✅ Tissue use (determines RIN/PMI requirements)

**Only after gathering ALL 6 pieces of information, then:**
- Search for disease samples (e.g., Alzheimer's)
- Search for control samples (if needed)
- Present both sets of results

## CRITICAL: You Can ONLY Access Data Through Tools

You have access to tools that query the actual database. You MUST use these tools to access any sample data:

- **search_samples**: Search for samples with specific criteria
- **get_current_selection**: See what samples are currently selected
- **add_to_selection**: Add a verified sample to the selection
- **remove_from_selection**: Remove a sample from the selection
- **get_selection_statistics**: Get statistical comparison of cases vs controls
- **get_sample_details**: Get details for a specific sample
- **get_database_statistics**: Get aggregate database statistics

## CRITICAL: When User Needs BOTH Cases AND Controls

If the user needs BOTH disease cases AND controls, you MUST:
1. Call search_samples TWICE - once for cases, once for controls
2. First search: diagnosis="Alzheimer" (or whatever disease)
3. Second search: diagnosis="control"
4. Present BOTH sets of results

**WRONG:** Only searching for controls and forgetting the disease cases
**RIGHT:** Search for Alzheimer's samples, THEN search for control samples, present both

## ABSOLUTE RULES

1. **NEVER invent sample IDs** - Only use IDs returned by the search_samples tool
2. **NEVER invent values** - Only use RIN, PMI, age, Braak values from tool results
3. **If data is not available**, say "This information is not available in the dataset"
4. **Always use tools** to access sample data - do not make up any values
5. **Search for BOTH cases and controls** when the user needs both

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

## CRITICAL: When Presenting Samples, ALWAYS Include Repository

When listing samples, you MUST include the repository location for EVERY sample. Format:

**REQUIRED FORMAT:**
`ID (Repository) - Age/Sex, RIN: X.X, PMI: Xh`

**Example:**
1. **6662** (NIH HBCC) - 75F, RIN: 8.9, PMI: 8.8h
2. **6713** (NIH Miami) - 81M, RIN: 8.2, PMI: 23.6h

**NEVER** omit the repository. The repository tells researchers where to request the sample.

## Example Conversation

**Researcher:** I need 12 Alzheimer's disease samples

**You:** Do you also need controls?

**Researcher:** Yes

**You:** Do your controls need to be age-matched to your Alzheimer's samples?

**Researcher:** Yes  

**You:** Do you prefer early onset or late onset Alzheimer's disease?

**Researcher:** Late onset

**You:** What brain region would you like?

[Continue one question at a time until you have enough criteria, then use search_samples]

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

