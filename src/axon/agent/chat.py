"""Chat agent for brain bank discovery."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from axon.agent.prompts import SYSTEM_PROMPT, EDUCATIONAL_TOPICS
from axon.agent.database_queries import (
    get_race_breakdown_detailed,
    get_ethnicity_breakdown,
    get_diagnosis_breakdown,
    get_sample_count_by_source,
    get_sample_count_by_sex,
    count_samples_with_filter,
    count_samples_with_demographics,
    get_total_sample_count,
    compare_demographics_neuropathology,
    get_complex_stats,
)
from axon.db.models import Sample
from axon.rag.retrieval import ContextBuilder, RAGRetriever, RetrievedSample
from axon.matching.service import MatchingService, MatchingCriteria, format_match_result_for_agent


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
        
        # Sample matching
        self.matching_service = MatchingService(db_session)
        self.matching_criteria = MatchingCriteria()
    
    def new_conversation(self) -> None:
        """Start a new conversation."""
        self.conversation = Conversation(
            id=f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        # Reset matching criteria for new conversation
        self.matching_criteria = MatchingCriteria()
    
    async def run_matching(self) -> str:
        """Run the matching algorithm with current criteria.
        
        Returns:
            Formatted result string for display
        """
        if not self.matching_criteria.is_complete_for_matching():
            return "I don't have enough information to find matched samples yet. Let me ask a few more questions."
        
        result = await self.matching_service.find_matched_samples(self.matching_criteria)
        return format_match_result_for_agent(result)
    
    async def get_matching_preview(self) -> str:
        """Get a preview of available samples for current criteria.
        
        Returns:
            Formatted preview string
        """
        return await self.matching_service.get_matching_preview(self.matching_criteria)
    
    def update_matching_criteria(
        self,
        diagnosis: str | None = None,
        n_cases: int | None = None,
        needs_controls: bool | None = None,
        n_controls: int | None = None,
        age_matched: bool | None = None,
        min_age: int | None = None,
        max_age: int | None = None,
        brain_region: str | None = None,
        min_rin: float | None = None,
        max_pmi: float | None = None,
        exclude_co_pathologies: bool | None = None,
    ) -> None:
        """Update matching criteria from conversation.
        
        Args:
            diagnosis: Disease diagnosis for cases
            n_cases: Number of cases needed
            needs_controls: Whether controls are needed
            n_controls: Number of controls needed
            age_matched: Whether controls should be age-matched
            min_age: Minimum donor age
            max_age: Maximum donor age
            brain_region: Required brain region
            min_rin: Minimum RIN score
            max_pmi: Maximum PMI in hours
            exclude_co_pathologies: Whether to exclude co-pathologies
        """
        if diagnosis is not None:
            self.matching_criteria.diagnosis = diagnosis
        if n_cases is not None:
            self.matching_criteria.n_cases = n_cases
        if needs_controls is not None:
            self.matching_criteria.needs_controls = needs_controls
        if n_controls is not None:
            self.matching_criteria.n_controls = n_controls
        if age_matched is not None:
            self.matching_criteria.age_matched = age_matched
        if min_age is not None:
            self.matching_criteria.min_age = min_age
        if max_age is not None:
            self.matching_criteria.max_age = max_age
        if brain_region is not None:
            self.matching_criteria.brain_region = brain_region
        if min_rin is not None:
            self.matching_criteria.min_rin = min_rin
        if max_pmi is not None:
            self.matching_criteria.max_pmi = max_pmi
        if exclude_co_pathologies is not None:
            self.matching_criteria.exclude_co_pathologies = exclude_co_pathologies
    
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
        
        # Check if agent announced a search and user is confirming
        search_context = None
        if self._agent_announced_search() and self._is_confirmation(message):
            # Extract criteria from conversation and do a proper search
            search_context = await self._do_criteria_based_search(num_samples)
        
        # Retrieve relevant samples if needed (and not a stats question or criteria search)
        retrieved: list[RetrievedSample] = []
        if retrieve_samples and self._should_retrieve(message) and not stats_context and not search_context:
            # Build a better query from conversation context, not just the last message
            query = self._build_search_query(message)
            retrieved = await self.retriever.retrieve(
                query=query,
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
        elif search_context:
            messages[-1]["content"] = f"{search_context}\n\n---\n\n**User Query:** {message}"
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
    
    def _agent_announced_search(self) -> bool:
        """Check if the agent's last message announced it would search for samples."""
        for msg in reversed(self.conversation.messages):
            if msg.role == "assistant":
                content = msg.content.lower()
                search_phrases = [
                    "let me search",
                    "let me find",
                    "i'll search",
                    "i will search",
                    "i'll find",
                    "i will find",
                    "searching for",
                    "let me look for",
                    "i'll look for",
                    "let me get",
                    "finding samples",
                    "find samples that match",
                    "search for samples",
                    "present you with",
                    "present the best options",
                ]
                return any(phrase in content for phrase in search_phrases)
        return False
    
    def _is_confirmation(self, message: str) -> bool:
        """Check if message is a simple confirmation."""
        confirmations = {
            "ok", "okay", "k", "sure", "yes", "yeah", "yep", "yup",
            "go ahead", "please", "proceed", "continue", "sounds good",
            "do it", "yes please", "go for it", "alright", "all right",
            "perfect", "great", "good", "fine", "that's fine",
        }
        return message.lower().strip().rstrip('!.,') in confirmations
    
    def _build_search_query(self, message: str) -> str:
        """Build a search query from conversation context.
        
        Instead of searching with just the last message (e.g., "ok"),
        builds a composite query from key criteria mentioned in conversation.
        """
        # If the message itself is substantive, use it
        if len(message) > 20 and not self._is_confirmation(message):
            return message
        
        # Otherwise, extract key terms from recent conversation
        key_terms = []
        
        # Look through recent messages for criteria
        for msg in self.conversation.messages[-10:]:
            content = msg.content.lower()
            
            # Disease terms
            diseases = ["alzheimer", "parkinson", "als", "huntington", "schizophrenia", "dementia"]
            for disease in diseases:
                if disease in content and disease not in key_terms:
                    key_terms.append(disease)
            
            # Brain regions
            regions = ["frontal", "temporal", "hippocampus", "cortex", "cerebellum", "parietal"]
            for region in regions:
                if region in content and region not in key_terms:
                    key_terms.append(region)
            
            # Pathology staging
            if "braak" in content:
                # Try to extract Braak stage
                import re
                braak_match = re.search(r'braak\s*(?:stage)?\s*([iv]+|\d+)', content, re.IGNORECASE)
                if braak_match:
                    key_terms.append(f"Braak {braak_match.group(1)}")
            
            # Quality metrics
            if "rin" in content and "rin" not in key_terms:
                key_terms.append("high RIN")
            
            # Tissue type
            if "frozen" in content:
                key_terms.append("frozen tissue")
            elif "fixed" in content:
                key_terms.append("fixed tissue")
        
        if key_terms:
            return " ".join(key_terms)
        
        # Fallback to original message
        return message
    
    async def _do_criteria_based_search(self, limit: int = 20) -> str:
        """Perform a search based on criteria extracted from conversation.
        
        This is triggered when the agent announced a search and user confirmed.
        Returns formatted context for Claude to present results.
        """
        # Extract criteria from conversation using Claude
        criteria = await self._extract_criteria_from_conversation()
        
        if not criteria:
            # Fallback to keyword-based search
            query = self._build_search_query("")
            retrieved = await self.retriever.retrieve(query=query, limit=limit)
            samples = [r.sample for r in retrieved]
            scores = [r.score for r in retrieved]
            return self.context_builder.build_context(query=query, samples=samples, scores=scores)
        
        # Use the matching service for a proper database query
        from axon.matching.candidates import find_case_candidates, find_control_candidates
        
        context_parts = ["## Search Results Based on Your Criteria\n"]
        context_parts.append(f"**Searching for:** {criteria.get('diagnosis', 'samples')}")
        
        # Find cases
        cases = await find_case_candidates(
            self.db_session,
            diagnosis=criteria.get('diagnosis'),
            min_age=criteria.get('min_age'),
            max_age=criteria.get('max_age'),
            brain_region=criteria.get('brain_region'),
            min_rin=criteria.get('min_rin'),
            max_pmi=criteria.get('max_pmi'),
            limit=limit,
        )
        
        if cases:
            context_parts.append(f"\n**Found {len(cases)} matching case samples:**\n")
            for i, case in enumerate(cases[:10], 1):
                context_parts.append(
                    f"{i}. **{case.external_id}** ({case.source_bank})\n"
                    f"   - Diagnosis: {case.diagnosis}\n"
                    f"   - Age: {case.age}, Sex: {case.sex}\n"
                    f"   - RIN: {case.rin}, PMI: {case.pmi}h\n"
                    f"   - Brain region: {case.brain_region}\n"
                )
            if len(cases) > 10:
                context_parts.append(f"\n... and {len(cases) - 10} more samples available.\n")
        else:
            context_parts.append("\n**No cases found matching all criteria.**\n")
            context_parts.append("Consider relaxing some constraints.\n")
        
        # Find controls if needed
        if criteria.get('needs_controls'):
            controls = await find_control_candidates(
                self.db_session,
                min_age=criteria.get('min_age') if criteria.get('age_matched') else None,
                max_age=criteria.get('max_age') if criteria.get('age_matched') else None,
                brain_region=criteria.get('brain_region'),
                min_rin=criteria.get('min_rin'),
                max_pmi=criteria.get('max_pmi'),
                limit=limit,
            )
            
            if controls:
                context_parts.append(f"\n**Found {len(controls)} matching control samples:**\n")
                for i, ctrl in enumerate(controls[:10], 1):
                    context_parts.append(
                        f"{i}. **{ctrl.external_id}** ({ctrl.source_bank})\n"
                        f"   - Age: {ctrl.age}, Sex: {ctrl.sex}\n"
                        f"   - RIN: {ctrl.rin}, PMI: {ctrl.pmi}h\n"
                    )
                if len(controls) > 10:
                    context_parts.append(f"\n... and {len(controls) - 10} more controls available.\n")
            else:
                context_parts.append("\n**No control samples found matching criteria.**\n")
        
        return "\n".join(context_parts)
    
    async def _extract_criteria_from_conversation(self) -> dict | None:
        """Use Claude to extract search criteria from the conversation."""
        # Build a summary of the conversation for extraction
        conversation_text = "\n".join([
            f"{msg.role.upper()}: {msg.content}"
            for msg in self.conversation.messages[-20:]
        ])
        
        extraction_prompt = f"""Extract the sample search criteria from this conversation.
Return ONLY a JSON object with these fields (use null for unspecified):

{{
    "diagnosis": "disease name or null",
    "needs_controls": true/false,
    "age_matched": true/false,
    "min_age": number or null,
    "max_age": number or null,
    "brain_region": "region name or null",
    "min_rin": number or null,
    "max_pmi": number or null,
    "braak_min": "stage or null",
    "braak_max": "stage or null",
    "tissue_type": "frozen/fixed or null",
    "exclude_co_pathologies": true/false,
    "equal_sex": true/false
}}

Conversation:
{conversation_text}

JSON:"""
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": extraction_prompt}],
            )
            
            import json
            import re
            
            # Extract JSON from response
            text = response.content[0].text
            # Find JSON object in response
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                criteria = json.loads(json_match.group())
                # Filter out null values
                return {k: v for k, v in criteria.items() if v is not None}
        except Exception as e:
            print(f"Error extracting criteria: {e}")
        
        return None
    
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
        
        # Handle demographic count queries (e.g., "how many hispanic women")
        # This is for simple counts without neuropathology
        if has_demographics and (ethnicity or race):
            sex = None
            if "women" in message_lower or "female" in message_lower:
                sex = "female"
            elif "men" in message_lower or "male" in message_lower:
                sex = "male"
            
            # Build count query
            count = await count_samples_with_demographics(
                self.db_session,
                sex=sex,
                race=race,
                ethnicity=ethnicity,
                min_age=min_age,
                max_age=max_age,
            )
            
            # Build description
            desc_parts = []
            if ethnicity:
                desc_parts.append(ethnicity)
            if race:
                desc_parts.append(race)
            if sex:
                desc_parts.append("women" if sex == "female" else "men")
            if min_age:
                desc_parts.append(f"over {min_age}")
            if max_age:
                desc_parts.append(f"under {max_age}")
            
            desc = " ".join(desc_parts) if desc_parts else "samples"
            context_parts.append(f"**{desc.title()} in database:** {count:,}")
            return "\n\n".join(context_parts)
        
        # Check for race-related questions (general breakdown)
        race_keywords = ["race", "african", "black", "white", "asian"]
        if any(kw in message_lower for kw in race_keywords) and not (ethnicity or race):
            race_stats = await get_race_breakdown_detailed(self.db_session)
            context_parts.append(race_stats)
        
        # Check for ethnicity-related questions (general breakdown)
        elif "hispanic" in message_lower or "latino" in message_lower or "ethnicity" in message_lower:
            ethnicity_stats = await get_ethnicity_breakdown(self.db_session)
            context_parts.append(ethnicity_stats)
        
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
        message_lower = message.lower().strip()
        
        # Skip retrieval for simple greetings or meta-questions
        skip_patterns = [
            "hello", "hi", "hey", "thanks", "thank you",
            "bye", "goodbye", "help", "what can you do",
        ]
        
        if message_lower in skip_patterns:
            return False
        
        # Check if this is a short conversational response to the agent's question
        if self._is_conversational_response(message):
            return False
        
        return True
    
    def _is_conversational_response(self, message: str) -> bool:
        """Check if message is a response to the agent's previous question.
        
        This prevents the system from running semantic search on responses like
        "yes", "no", "I would prefer X" when the agent asked a clarifying question.
        
        Uses intent detection to distinguish:
        - Answer patterns: "I would prefer", "I'd like", "yes", "no" → Don't search
        - Request patterns: "I need", "can you find", "search for" → Do search
        """
        message_lower = message.lower().strip()
        
        # If the agent didn't just ask a question, this isn't a conversational response
        if not self._last_assistant_asked_question():
            return False
        
        # Remove trailing punctuation for matching
        message_clean = message_lower.rstrip('?!.,')
        
        # === PATTERNS THAT ASK FOR AGENT'S ADVICE (don't search, use knowledge) ===
        advice_patterns = [
            "what do you recommend", "what would you recommend",
            "what do you suggest", "what would you suggest",
            "what's your recommendation", "what is your recommendation",
            "which do you recommend", "which would you recommend",
            "any suggestions", "any recommendations",
            "what should i", "what would you advise",
            "do you have any suggestions", "do you have any recommendations",
            "what's best", "what is best", "which is best",
            "what's better", "what is better", "which is better",
            "your thoughts", "your opinion", "what do you think",
            "help me choose", "help me decide",
        ]
        
        # If asking for advice, use knowledge base / conversation context, not sample search
        for pattern in advice_patterns:
            if pattern in message_lower:
                return True  # Conversational, should NOT retrieve samples
        
        # === PATTERNS THAT INDICATE A NEW REQUEST (should search) ===
        new_request_patterns = [
            "i need", "i'm looking for", "i am looking for",
            "can you find", "can you search", "can you show",
            "search for", "find me", "show me", "look for",
            "what about", "how about searching",
            "let's search", "let's find", "let's look",
            "give me", "get me",
        ]
        
        # If message starts with a request pattern, it's a new request - DO search
        for pattern in new_request_patterns:
            if message_lower.startswith(pattern):
                return False  # Not conversational, should retrieve
        
        # === PATTERNS THAT INDICATE ANSWERING A QUESTION (don't search) ===
        
        # Short exact responses
        short_responses = {
            # Affirmative
            "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "k",
            "correct", "right", "exactly", "absolutely", "definitely",
            "of course", "certainly", "indeed", "agreed", "affirmative",
            "that's right", "that's correct", "sounds good", "works for me",
            "please", "go ahead", "continue", "proceed",
            "i do", "i would", "i am", "i will", "we do", "we would",
            
            # Negative
            "no", "nope", "nah", "not really", "no thanks", "negative",
            "i don't", "i wouldn't", "i'm not", "we don't",
            "not sure", "i don't know", "unsure", "maybe", "perhaps",
            
            # Clarifications
            "both", "either", "neither", "all of them", "none of them",
            "the first one", "the second one", "the latter", "the former",
        }
        
        # Check for exact short responses
        if message_clean in short_responses or message_lower in short_responses:
            return True
        
        # Check for numeric responses (e.g., "12", "6-8", "100")
        if message_clean.replace("-", "").replace(" ", "").isdigit():
            return True
        
        # === ANSWER PATTERNS (phrases that indicate responding to a question) ===
        answer_patterns = [
            # Preference expressions
            "i would prefer", "i'd prefer", "i prefer",
            "i would like", "i'd like", "i like",
            "i would rather", "i'd rather", "i rather",
            "i would want", "i'd want", "i want",
            "i would choose", "i'd choose", "i choose",
            
            # Opinion/belief expressions
            "i think", "i believe", "i feel",
            "i don't think", "i don't believe", "i don't feel",
            "i'm not sure", "i am not sure",
            
            # Acceptance/rejection
            "that would be", "that's", "that is",
            "yes,", "yes ", "no,", "no ",
            "sure,", "okay,", "ok,",
            
            # Clarifying responses
            "actually", "well,", "hmm,",
            "let me think", "good question",
            
            # Specific to our domain
            "frozen", "fixed", "fresh",  # tissue type responses
            "frontal", "temporal", "hippocampus", "cerebellum",  # brain region responses
            "male", "female", "both sexes",  # sex responses
            "age matched", "age-matched", "not age matched",
            "with co-pathologies", "without co-pathologies",
            "early onset", "late onset", "early-onset", "late-onset",
        ]
        
        # Check if message starts with or contains answer patterns
        for pattern in answer_patterns:
            if message_lower.startswith(pattern):
                return True
        
        # For domain-specific single-word answers (brain regions, tissue types)
        domain_answers = {
            "frozen", "fixed", "fresh", "paraffin",
            "frontal", "temporal", "parietal", "occipital", "hippocampus", 
            "cerebellum", "brainstem", "cortex", "amygdala", "striatum",
            "male", "female", "males", "females",
            "left", "right", "bilateral",
        }
        
        # If it's a short message (under 50 chars) containing domain answers
        if len(message_lower) < 50:
            words = set(message_clean.split())
            if words & domain_answers:  # intersection
                return True
        
        # === FALLBACK: Short messages following questions are likely answers ===
        # If message is reasonably short and agent just asked a question,
        # lean towards treating it as an answer (avoids irrelevant searches)
        if len(message_lower) < 80 and not any(p in message_lower for p in new_request_patterns):
            # Check if it looks like an answer vs. a question or command
            if not message_lower.endswith('?') and not message_lower.startswith(('what', 'where', 'how', 'why', 'when', 'which', 'can you', 'could you')):
                return True
        
        return False
    
    def _last_assistant_asked_question(self) -> bool:
        """Check if the last assistant message ended with a question."""
        # Look for the most recent assistant message
        for msg in reversed(self.conversation.messages):
            if msg.role == "assistant":
                content = msg.content.strip()
                # Check if it ends with a question mark
                # Also handle cases where there might be trailing formatting
                last_sentence = content.split('\n')[-1].strip()
                return '?' in last_sentence[-50:] if len(last_sentence) > 50 else '?' in last_sentence
        return False
    
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

