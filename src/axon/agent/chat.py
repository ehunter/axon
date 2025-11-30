"""Chat agent for brain bank discovery."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.prompts import SYSTEM_PROMPT, EDUCATIONAL_TOPICS
from axon.db.models import Sample
from axon.rag.retrieval import ContextBuilder, RAGRetriever, RetrievedSample


@dataclass
class Message:
    """A message in the conversation."""
    
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    retrieved_samples: list[Sample] = field(default_factory=list)


@dataclass
class Conversation:
    """A conversation with message history."""
    
    id: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, samples: list[Sample] | None = None):
        """Add a message to the conversation."""
        self.messages.append(Message(
            role=role,
            content=content,
            retrieved_samples=samples or [],
        ))
    
    def get_history_for_llm(self, max_messages: int = 20) -> list[dict]:
        """Get conversation history formatted for Claude API."""
        # Get recent messages, excluding system messages
        recent = self.messages[-max_messages:]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
        ]


class ChatAgent:
    """Interactive chat agent for brain bank discovery.
    
    Maintains conversation history and uses RAG to provide
    informed responses about brain tissue samples.
    
    The agent follows a guided workflow to help researchers find
    optimal samples, asking clarifying questions about:
    - Disease criteria and subtypes
    - Pathology requirements (Braak, Thal, etc.)
    - Technical requirements (RIN, PMI, brain region)
    - Matching criteria for controls
    - Exclusion criteria
    """

    def __init__(
        self,
        db_session: AsyncSession,
        embedding_api_key: str,
        anthropic_api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the chat agent.
        
        Args:
            db_session: Database session
            embedding_api_key: OpenAI API key for embeddings
            anthropic_api_key: Anthropic API key for Claude
            model: Claude model to use
        """
        self.retriever = RAGRetriever(db_session, embedding_api_key)
        self.context_builder = ContextBuilder()
        self.client = AsyncAnthropic(api_key=anthropic_api_key)
        self.model = model
        self.conversation = Conversation(id="default")
    
    def new_conversation(self) -> None:
        """Start a new conversation."""
        self.conversation = Conversation(
            id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
    
    async def chat(
        self,
        message: str,
        retrieve_samples: bool = True,
        num_samples: int = 10,
        stream: bool = False,
        **filters,
    ) -> str | AsyncGenerator[str, None]:
        """Send a message and get a response.
        
        Args:
            message: User's message
            retrieve_samples: Whether to retrieve relevant samples
            num_samples: Number of samples to retrieve
            stream: Whether to stream the response
            **filters: Additional filters for sample retrieval
            
        Returns:
            Assistant's response (or async generator if streaming)
        """
        # Add user message to history
        self.conversation.add_message("user", message)
        
        # Retrieve relevant samples if needed
        retrieved: list[RetrievedSample] = []
        if retrieve_samples and self._should_retrieve(message):
            retrieved = await self.retriever.retrieve(
                query=message,
                limit=num_samples,
                **filters,
            )
        
        samples = [r.sample for r in retrieved]
        scores = [r.score for r in retrieved]
        
        # Build messages for Claude
        messages = self.conversation.get_history_for_llm()
        
        # Add context about retrieved samples to the last user message
        if samples:
            context = self.context_builder.build_context(
                query=message,
                samples=samples,
                scores=scores,
            )
            messages[-1]["content"] = f"{context}\n\n---\n\n**User Query:** {message}"
        
        if stream:
            return self._stream_response(messages, samples)
        else:
            return await self._get_response(messages, samples)
    
    def _should_retrieve(self, message: str) -> bool:
        """Determine if we should retrieve samples for this message."""
        # Skip retrieval for simple greetings or meta-questions
        skip_patterns = [
            "hello", "hi", "hey", "thanks", "thank you",
            "bye", "goodbye", "help", "what can you do",
        ]
        message_lower = message.lower().strip()
        
        if len(message_lower) < 10:
            return message_lower not in skip_patterns
        
        return True
    
    async def _get_response(
        self,
        messages: list[dict],
        samples: list[Sample],
    ) -> str:
        """Get a complete response from Claude."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        
        answer = response.content[0].text
        
        # Add assistant response to history
        self.conversation.add_message("assistant", answer, samples)
        
        return answer
    
    async def _stream_response(
        self,
        messages: list[dict],
        samples: list[Sample],
    ) -> AsyncGenerator[str, None]:
        """Stream a response from Claude."""
        full_response = ""
        
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                full_response += text
                yield text
        
        # Add complete response to history
        self.conversation.add_message("assistant", full_response, samples)
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation."""
        num_messages = len(self.conversation.messages)
        num_user = sum(1 for m in self.conversation.messages if m.role == "user")
        num_assistant = sum(1 for m in self.conversation.messages if m.role == "assistant")
        
        return (
            f"Conversation: {self.conversation.id}\n"
            f"Messages: {num_messages} ({num_user} user, {num_assistant} assistant)\n"
            f"Started: {self.conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

