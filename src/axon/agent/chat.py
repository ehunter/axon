"""Chat agent for brain bank discovery."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.prompts import SYSTEM_PROMPT, EDUCATIONAL_TOPICS
from axon.agent.database_queries import (
    get_race_breakdown_detailed,
    get_diagnosis_breakdown,
    get_sample_count_by_source,
    get_sample_count_by_sex,
    count_samples_with_filter,
    get_total_sample_count,
    compare_demographics_neuropathology,
    get_complex_stats,
)
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
        self.db_session = db_session
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
        
        # Check if this is an aggregate/statistics question
        stats_context = await self._get_stats_context(message)
        
        # Retrieve relevant samples if needed (and not a stats question)
        retrieved: list[RetrievedSample] = []
        if retrieve_samples and self._should_retrieve(message) and not stats_context:
            retrieved = await self.retriever.retrieve(
                query=message,
                limit=num_samples,
                **filters,
            )
        
        samples = [r.sample for r in retrieved]
        scores = [r.score for r in retrieved]
        
        # Build messages for Claude
        messages = self.conversation.get_history_for_llm()
        
        # Add context about retrieved samples or stats to the last user message
        if stats_context:
            messages[-1]["content"] = f"{stats_context}\n\n---\n\n**User Query:** {message}"
        elif samples:
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
    
    async def _get_stats_context(self, message: str) -> str | None:
        """Check if message is asking for statistics and return context if so."""
        message_lower = message.lower()
        
        # Keywords indicating aggregate/count questions
        count_keywords = [
            "how many", "total number", "count", "breakdown", 
            "statistics", "summary", "available", "do you have",
            "most common", "compare", "vs", "versus", "difference"
        ]
        
        is_stats_question = any(kw in message_lower for kw in count_keywords)
        
        if not is_stats_question:
            return None
        
        context_parts = ["## Database Statistics\n"]
        
        # Check for complex demographic comparison queries
        # e.g., "neuropathology in hispanic women vs men over 65"
        is_comparison = any(kw in message_lower for kw in ["vs", "versus", "compare", "difference"])
        has_demographics = any(kw in message_lower for kw in ["women", "men", "male", "female", "hispanic", "black", "white", "asian"])
        has_neuropathology = any(kw in message_lower for kw in ["neuropathology", "diagnosis", "pathology", "disease"])
        
        # Extract age filter (handle "over 65", "over-65", ">65", "65+", "65 years old", etc.)
        import re
        age_match = re.search(r'(?:over|above|>)[\s-]*(\d+)', message_lower)
        if not age_match:
            age_match = re.search(r'(\d+)\s*(?:\+|years?\s*old|year[\s-]*old)', message_lower)
        min_age = int(age_match.group(1)) if age_match else None
        
        age_match_max = re.search(r'(?:under|below|<)[\s-]*(\d+)', message_lower)
        max_age = int(age_match_max.group(1)) if age_match_max else None
        
        # Extract ethnicity/race
        ethnicity = None
        race = None
        if "hispanic" in message_lower or "latino" in message_lower:
            ethnicity = "Hispanic"
        if "black" in message_lower or "african" in message_lower:
            race = "Black"
        if "white" in message_lower or "caucasian" in message_lower:
            race = "White"
        if "asian" in message_lower:
            race = "Asian"
        
        # Handle comparison queries (e.g., "women vs men")
        if is_comparison and has_demographics and has_neuropathology:
            # Determine what we're comparing
            if ("women" in message_lower or "female" in message_lower) and ("men" in message_lower or "male" in message_lower):
                # Comparing women vs men
                group1_filters = {"sex": "female", "min_age": min_age, "max_age": max_age, "ethnicity": ethnicity, "race": race}
                group2_filters = {"sex": "male", "min_age": min_age, "max_age": max_age, "ethnicity": ethnicity, "race": race}
                
                age_desc = f" over {min_age}" if min_age else ""
                eth_desc = f" {ethnicity}" if ethnicity else ""
                race_desc = f" {race}" if race else ""
                
                comparison = await compare_demographics_neuropathology(
                    self.db_session,
                    group1_filters,
                    group2_filters,
                    group1_label=f"{eth_desc}{race_desc} Women{age_desc}".strip(),
                    group2_label=f"{eth_desc}{race_desc} Men{age_desc}".strip(),
                )
                context_parts.append(comparison)
                return "\n\n".join(context_parts)
        
        # Handle complex single-group queries (e.g., "neuropathology in hispanic women over 65")
        if has_demographics and has_neuropathology:
            sex = None
            if "women" in message_lower or "female" in message_lower:
                sex = "female"
            elif "men" in message_lower or "male" in message_lower:
                sex = "male"
            
            stats = await get_complex_stats(
                self.db_session,
                min_age=min_age,
                max_age=max_age,
                sex=sex,
                race=race,
                ethnicity=ethnicity,
            )
            context_parts.append(stats)
            return "\n\n".join(context_parts)
        
        # Check for race-related questions
        race_keywords = ["race", "african", "black", "white", "asian", "hispanic", "ethnicity"]
        if any(kw in message_lower for kw in race_keywords):
            race_stats = await get_race_breakdown_detailed(self.db_session)
            context_parts.append(race_stats)
        
        # Check for sex-related questions
        elif any(kw in message_lower for kw in ["male", "female", "sex", "gender"]):
            sex_counts = await get_sample_count_by_sex(self.db_session)
            total = sum(sex_counts.values())
            lines = ["**Sample Counts by Sex:**\n"]
            for sex, count in sorted(sex_counts.items(), key=lambda x: -x[1]):
                pct = (count / total) * 100 if total > 0 else 0
                lines.append(f"- {sex}: **{count:,}** ({pct:.1f}%)")
            context_parts.append("\n".join(lines))
        
        # Check for source-related questions
        elif any(kw in message_lower for kw in ["source", "bank", "institution", "nih", "harvard", "sinai"]):
            source_counts = await get_sample_count_by_source(self.db_session)
            total = sum(source_counts.values())
            lines = ["**Sample Counts by Source Bank:**\n"]
            for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
                pct = (count / total) * 100 if total > 0 else 0
                lines.append(f"- {source}: **{count:,}** ({pct:.1f}%)")
            context_parts.append("\n".join(lines))
        
        # Check for diagnosis-related questions
        elif any(kw in message_lower for kw in ["diagnosis", "disease", "alzheimer", "parkinson", "als", "schizophrenia"]):
            # Extract specific diagnosis if mentioned
            diagnosis_terms = {
                "alzheimer": "Alzheimer",
                "parkinson": "Parkinson",
                "als": "ALS",
                "amyotrophic": "ALS",
                "huntington": "Huntington",
                "schizophrenia": "schizophrenia",
                "multiple sclerosis": "Multiple sclerosis",
                "ms ": "Multiple sclerosis",
            }
            search_term = None
            for term, search in diagnosis_terms.items():
                if term in message_lower:
                    search_term = search
                    break
            
            if search_term:
                count = await count_samples_with_filter(self.db_session, diagnosis=search_term)
                context_parts.append(f"**Samples matching '{search_term}':** {count:,}")
            else:
                diag_stats = await get_diagnosis_breakdown(self.db_session)
                context_parts.append(diag_stats)
        
        # General total count
        else:
            total = await get_total_sample_count(self.db_session)
            context_parts.append(f"**Total samples in database:** {total:,}")
        
        return "\n\n".join(context_parts)
    
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

