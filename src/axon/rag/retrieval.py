"""RAG retrieval layer for the brain bank assistant.

This module provides the retrieval-augmented generation pipeline that:
1. Retrieves relevant samples based on user queries
2. Builds context for the LLM
3. Generates responses using Claude
"""

from dataclasses import dataclass, field
from typing import Any

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import Sample, KnowledgeChunk, KnowledgeDocument
from axon.rag.embeddings import EmbeddingService


@dataclass
class RetrievedSample:
    """A retrieved sample with relevance score."""
    
    sample: Sample
    score: float


@dataclass
class RetrievedKnowledge:
    """A retrieved knowledge chunk with relevance score."""
    
    chunk: KnowledgeChunk
    document_title: str | None
    document_url: str
    source_name: str
    score: float


@dataclass
class RAGResponse:
    """Response from the RAG pipeline."""
    
    answer: str
    sources: list[Sample]
    knowledge_sources: list[RetrievedKnowledge] = field(default_factory=list)
    query: str = ""


class ContextBuilder:
    """Builds context for LLM from retrieved samples."""
    
    SYSTEM_PROMPT = """You are Axon, an expert brain bank research assistant. Your role is to help neuroscience researchers find the most suitable brain tissue samples for their research.

You have access to a database of brain tissue samples from multiple brain banks including NIH sites (Miami, Maryland, Pittsburgh, Sepulveda, HBCC, ADRC), Harvard, and Mt. Sinai.

When helping researchers:
1. Be precise and scientific in your language
2. Highlight relevant sample characteristics (diagnosis, brain region, quality metrics like RIN score, PMI)
3. Note any limitations or caveats about the samples
4. Suggest follow-up questions if the researcher's needs aren't fully clear
5. When appropriate, recommend contacting the specific brain bank for availability

Always base your responses on the actual sample data provided to you. If no relevant samples are found, say so clearly and suggest alternative search criteria."""

    def format_sample(self, sample: Sample) -> str:
        """Format a single sample for LLM context."""
        parts = [f"**ID:** {sample.external_id} ({sample.source_bank})"]
        
        if sample.primary_diagnosis:
            parts.append(f"**Diagnosis:** {sample.primary_diagnosis}")
        
        # Neuropathology scores
        if sample.extended_data:
            neuropath = sample.extended_data.get("neuropathology_scores", {})
            if neuropath:
                scores = []
                
                braak_nft = neuropath.get("braak_nft_stage")
                if braak_nft and braak_nft not in ("Not Assessed", "No Results Reported"):
                    scores.append(f"Braak NFT: {braak_nft}")
                
                thal = neuropath.get("thal_phase")
                if thal and thal not in ("Not Assessed", "No Results Reported"):
                    scores.append(f"Thal: {thal}")
                
                cerad = neuropath.get("cerad_score")
                if cerad and cerad not in ("Not Assessed", "No Results Reported"):
                    scores.append(f"CERAD: {cerad}")
                
                adnc = neuropath.get("adnc")
                if adnc and adnc not in ("Not Assessed", "No Results Reported"):
                    scores.append(f"ADNC: {adnc}")
                
                braak_pd = neuropath.get("braak_pd_stage")
                if braak_pd and braak_pd not in ("Not Assessed", "No Results Reported"):
                    scores.append(f"Braak PD: {braak_pd}")
                
                lewy = neuropath.get("lewy_pathology")
                if lewy and lewy not in ("Not Assessed", "No Results Reported"):
                    scores.append(f"Lewy: {lewy}")
                
                if scores:
                    parts.append(f"**Neuropathology:** {'; '.join(scores)}")
            
            neuropath_dx = sample.extended_data.get("neuropathology_diagnosis")
            if neuropath_dx and neuropath_dx not in ("Coding Pending", "Diagnostic pathology not present"):
                parts.append(f"**Neuropath Dx:** {neuropath_dx}")
        
        if sample.brain_region:
            # Truncate very long brain region lists
            regions = sample.brain_region
            if len(regions) > 200:
                region_list = regions.split(", ")
                regions = ", ".join(region_list[:10]) + f" (+{len(region_list)-10} more regions)"
            parts.append(f"**Brain Regions:** {regions}")
        
        demographics = []
        if sample.donor_age:
            demographics.append(f"{sample.donor_age} years old")
        if sample.donor_sex:
            demographics.append(sample.donor_sex)
        if sample.donor_race:
            demographics.append(sample.donor_race)
        if demographics:
            parts.append(f"**Donor:** {', '.join(demographics)}")
        
        quality = []
        if sample.rin_score:
            parts.append(f"**RIN Score:** {sample.rin_score}")
        if sample.postmortem_interval_hours:
            parts.append(f"**PMI:** {sample.postmortem_interval_hours} hours")
        
        if sample.preservation_method:
            parts.append(f"**Preservation:** {sample.preservation_method}")
        
        if sample.hemisphere:
            parts.append(f"**Hemisphere:** {sample.hemisphere}")
        
        return "\n".join(parts)
    
    def format_samples(self, samples: list[Sample], scores: list[float] | None = None) -> str:
        """Format multiple samples for LLM context."""
        if not samples:
            return "No relevant samples found."
        
        formatted = []
        for i, sample in enumerate(samples, 1):
            header = f"### Sample {i}"
            if scores and i <= len(scores):
                header += f" (relevance: {scores[i-1]:.0%})"
            
            formatted.append(header)
            formatted.append(self.format_sample(sample))
            formatted.append("")  # Empty line between samples
        
        return "\n".join(formatted)
    
    def build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return self.SYSTEM_PROMPT
    
    def format_knowledge(self, knowledge: list[RetrievedKnowledge]) -> str:
        """Format knowledge chunks for LLM context."""
        if not knowledge:
            return ""
        
        formatted = []
        for i, k in enumerate(knowledge, 1):
            header = f"### Reference {i}"
            if k.score:
                header += f" (relevance: {k.score:.0%})"
            
            formatted.append(header)
            formatted.append(f"**Source:** {k.source_name}")
            if k.document_title:
                formatted.append(f"**Document:** {k.document_title}")
            if k.chunk.section_title:
                formatted.append(f"**Section:** {k.chunk.section_title}")
            formatted.append("")
            formatted.append(k.chunk.content)
            formatted.append("")
        
        return "\n".join(formatted)
    
    def build_context(
        self,
        query: str,
        samples: list[Sample],
        scores: list[float] | None = None,
        knowledge: list[RetrievedKnowledge] | None = None,
    ) -> str:
        """Build the full context message for the LLM."""
        context_parts = []
        
        # Add knowledge base context first (educational background)
        if knowledge:
            context_parts.extend([
                "## Reference Information",
                "",
                "The following reference information may be relevant to the query:",
                "",
                self.format_knowledge(knowledge),
            ])
        
        # Add sample context
        context_parts.extend([
            "## Available Brain Tissue Samples",
            "",
            f"Based on your query, I found {len(samples)} relevant sample(s):",
            "",
            self.format_samples(samples, scores),
        ])
        
        return "\n".join(context_parts)


class RAGRetriever:
    """Retrieves relevant samples for RAG."""
    
    def __init__(
        self,
        db_session: AsyncSession,
        embedding_api_key: str,
    ):
        """Initialize the retriever.
        
        Args:
            db_session: Database session
            embedding_api_key: OpenAI API key for embeddings
        """
        self.db_session = db_session
        self.embedding_service = EmbeddingService(api_key=embedding_api_key)
    
    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        **filters,
    ) -> list[RetrievedSample]:
        """Retrieve samples relevant to the query.
        
        Args:
            query: Natural language query
            limit: Maximum number of samples to retrieve
            **filters: Additional filters (source_bank, min_rin, etc.)
            
        Returns:
            List of retrieved samples with scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)
        
        # Search for similar samples
        results = await self._search_samples(
            query_embedding=query_embedding,
            limit=limit,
            **filters,
        )
        
        return results
    
    async def _search_samples(
        self,
        query_embedding: list[float],
        limit: int,
        source_bank: str | None = None,
        min_rin: float | None = None,
        max_pmi: float | None = None,
        diagnosis: str | None = None,
        brain_region: str | None = None,
        **kwargs,
    ) -> list[RetrievedSample]:
        """Search for samples using vector similarity."""
        from sqlalchemy import text
        
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Build SQL query
        sql = """
            SELECT 
                id, source_bank, external_id, source_url,
                donor_age, donor_age_range, donor_sex, donor_race, donor_ethnicity,
                primary_diagnosis, primary_diagnosis_code, secondary_diagnoses,
                cause_of_death, manner_of_death,
                brain_region, brain_region_code, tissue_type, hemisphere, preservation_method,
                postmortem_interval_hours, ph_level, rin_score, quality_metrics,
                quantity_available, is_available, raw_data, extended_data,
                1 - (embedding <=> $1::vector) as similarity
            FROM samples
            WHERE embedding IS NOT NULL
        """
        
        params = [embedding_str]
        param_idx = 2
        
        if source_bank:
            sql += f" AND source_bank = ${param_idx}"
            params.append(source_bank)
            param_idx += 1
        
        if diagnosis:
            sql += f" AND primary_diagnosis ILIKE ${param_idx}"
            params.append(f"%{diagnosis}%")
            param_idx += 1
        
        if brain_region:
            sql += f" AND brain_region ILIKE ${param_idx}"
            params.append(f"%{brain_region}%")
            param_idx += 1
        
        if min_rin is not None:
            sql += f" AND rin_score >= ${param_idx}"
            params.append(min_rin)
            param_idx += 1
        
        if max_pmi is not None:
            sql += f" AND postmortem_interval_hours <= ${param_idx}"
            params.append(max_pmi)
            param_idx += 1
        
        sql += f" ORDER BY embedding <=> $1::vector LIMIT ${param_idx}"
        params.append(limit)
        
        # Execute using raw asyncpg connection
        conn = await self.db_session.connection()
        raw_conn = await conn.get_raw_connection()
        asyncpg_conn = raw_conn.driver_connection
        
        rows = await asyncpg_conn.fetch(sql, *params)
        
        # Convert to RetrievedSample objects
        results = []
        for row in rows:
            sample = Sample(
                id=row["id"],
                source_bank=row["source_bank"],
                external_id=row["external_id"],
                source_url=row["source_url"],
                donor_age=row["donor_age"],
                donor_age_range=row["donor_age_range"],
                donor_sex=row["donor_sex"],
                donor_race=row["donor_race"],
                donor_ethnicity=row["donor_ethnicity"],
                primary_diagnosis=row["primary_diagnosis"],
                primary_diagnosis_code=row["primary_diagnosis_code"],
                secondary_diagnoses=row["secondary_diagnoses"],
                cause_of_death=row["cause_of_death"],
                manner_of_death=row["manner_of_death"],
                brain_region=row["brain_region"],
                brain_region_code=row["brain_region_code"],
                tissue_type=row["tissue_type"],
                hemisphere=row["hemisphere"],
                preservation_method=row["preservation_method"],
                postmortem_interval_hours=row["postmortem_interval_hours"],
                ph_level=row["ph_level"],
                rin_score=row["rin_score"],
                quality_metrics=row["quality_metrics"],
                quantity_available=row["quantity_available"],
                is_available=row["is_available"],
                raw_data=row["raw_data"] or {},
                extended_data=row["extended_data"],
            )
            
            score = max(0.0, min(1.0, row["similarity"]))
            results.append(RetrievedSample(sample=sample, score=score))
        
        return results
    
    async def retrieve_knowledge(
        self,
        query: str,
        limit: int = 5,
        source_name: str | None = None,
        content_type: str | None = None,
    ) -> list[RetrievedKnowledge]:
        """Retrieve knowledge chunks relevant to the query.
        
        Args:
            query: Natural language query
            limit: Maximum number of chunks to retrieve
            source_name: Filter by source (e.g., "NIH NeuroBioBank")
            content_type: Filter by content type (e.g., "best_practices")
            
        Returns:
            List of retrieved knowledge chunks with scores
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)
        
        return await self._search_knowledge(
            query_embedding=query_embedding,
            limit=limit,
            source_name=source_name,
            content_type=content_type,
        )
    
    async def _search_knowledge(
        self,
        query_embedding: list[float],
        limit: int,
        source_name: str | None = None,
        content_type: str | None = None,
    ) -> list[RetrievedKnowledge]:
        """Search for knowledge chunks using vector similarity."""
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Build SQL query with JOIN to get document info
        sql = """
            SELECT 
                kc.id, kc.document_id, kc.chunk_index, kc.content,
                kc.section_title, kc.heading_hierarchy, kc.token_count,
                kd.url, kd.title, kd.source_name, kd.content_type,
                1 - (kc.embedding <=> $1::vector) as similarity
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kc.document_id = kd.id
            WHERE kc.embedding IS NOT NULL
        """
        
        params = [embedding_str]
        param_idx = 2
        
        if source_name:
            sql += f" AND kd.source_name = ${param_idx}"
            params.append(source_name)
            param_idx += 1
        
        if content_type:
            sql += f" AND kd.content_type = ${param_idx}"
            params.append(content_type)
            param_idx += 1
        
        sql += f" ORDER BY kc.embedding <=> $1::vector LIMIT ${param_idx}"
        params.append(limit)
        
        # Execute using raw asyncpg connection
        conn = await self.db_session.connection()
        raw_conn = await conn.get_raw_connection()
        asyncpg_conn = raw_conn.driver_connection
        
        try:
            rows = await asyncpg_conn.fetch(sql, *params)
        except Exception:
            # Table might not exist yet
            return []
        
        # Convert to RetrievedKnowledge objects
        results = []
        for row in rows:
            chunk = KnowledgeChunk(
                id=row["id"],
                document_id=row["document_id"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                section_title=row["section_title"],
                heading_hierarchy=row["heading_hierarchy"],
                token_count=row["token_count"],
            )
            
            score = max(0.0, min(1.0, row["similarity"]))
            results.append(RetrievedKnowledge(
                chunk=chunk,
                document_title=row["title"],
                document_url=row["url"],
                source_name=row["source_name"],
                score=score,
            ))
        
        return results


class RAGPipeline:
    """Complete RAG pipeline for the brain bank assistant."""
    
    def __init__(
        self,
        db_session: AsyncSession,
        embedding_api_key: str,
        anthropic_api_key: str,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Initialize the RAG pipeline.
        
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
    
    async def query(
        self,
        query: str,
        limit: int = 10,
        knowledge_limit: int = 3,
        max_tokens: int = 1024,
        include_knowledge: bool = True,
        **filters,
    ) -> RAGResponse:
        """Process a query through the RAG pipeline.
        
        Args:
            query: User's natural language query
            limit: Maximum samples to retrieve
            knowledge_limit: Maximum knowledge chunks to retrieve
            max_tokens: Maximum tokens in response
            include_knowledge: Whether to include knowledge base results
            **filters: Additional filters for retrieval
            
        Returns:
            RAGResponse with answer and sources
        """
        # Retrieve relevant samples
        retrieved = await self.retriever.retrieve(
            query=query,
            limit=limit,
            **filters,
        )
        
        samples = [r.sample for r in retrieved]
        scores = [r.score for r in retrieved]
        
        # Retrieve relevant knowledge chunks
        knowledge = []
        if include_knowledge:
            knowledge = await self.retriever.retrieve_knowledge(
                query=query,
                limit=knowledge_limit,
            )
        
        # Build context
        context = self.context_builder.build_context(
            query=query,
            samples=samples,
            scores=scores,
            knowledge=knowledge,
        )
        
        # Generate response with Claude
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=self.context_builder.build_system_prompt(),
            messages=[
                {
                    "role": "user",
                    "content": f"{context}\n\n---\n\n**User Query:** {query}",
                }
            ],
        )
        
        answer = response.content[0].text
        
        return RAGResponse(
            answer=answer,
            sources=samples,
            knowledge_sources=knowledge,
            query=query,
        )

