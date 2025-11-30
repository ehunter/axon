"""Vector and semantic search services."""

from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import Sample
from axon.rag.embeddings import EmbeddingService


@dataclass
class SearchResult:
    """A search result with sample and similarity score."""
    
    sample: Sample
    score: float  # Similarity score (0-1, higher is more similar)


class VectorSearchService:
    """Service for vector similarity search using pgvector."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the vector search service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def search_similar(
        self,
        query_embedding: list[float],
        limit: int = 10,
        source_bank: str | None = None,
        min_rin: float | None = None,
        max_pmi: float | None = None,
    ) -> list[SearchResult]:
        """Find samples similar to a query embedding.
        
        Uses cosine similarity via pgvector.
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            source_bank: Filter by source bank
            min_rin: Minimum RIN score filter
            max_pmi: Maximum PMI hours filter
            
        Returns:
            List of SearchResult with samples and scores
        """
        # Build the query using pgvector's cosine distance operator
        # 1 - cosine_distance gives us cosine similarity
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Start with base query
        sql = """
            SELECT 
                samples.*,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM samples
            WHERE embedding IS NOT NULL
        """
        
        params = {"embedding": embedding_str}
        
        # Add filters
        if source_bank:
            sql += " AND source_bank = :source_bank"
            params["source_bank"] = source_bank
        
        if min_rin is not None:
            sql += " AND rin_score >= :min_rin"
            params["min_rin"] = min_rin
        
        if max_pmi is not None:
            sql += " AND postmortem_interval_hours <= :max_pmi"
            params["max_pmi"] = max_pmi
        
        # Order by similarity and limit
        sql += " ORDER BY embedding <=> :embedding::vector LIMIT :limit"
        params["limit"] = limit
        
        # Execute query
        result = await self.session.execute(text(sql), params)
        rows = result.fetchall()
        
        # Convert to SearchResult objects
        results = []
        for row in rows:
            # Map row to Sample object
            sample = Sample(
                id=row.id,
                source_bank=row.source_bank,
                external_id=row.external_id,
                source_url=row.source_url,
                donor_age=row.donor_age,
                donor_age_range=row.donor_age_range,
                donor_sex=row.donor_sex,
                donor_race=row.donor_race,
                donor_ethnicity=row.donor_ethnicity,
                primary_diagnosis=row.primary_diagnosis,
                primary_diagnosis_code=row.primary_diagnosis_code,
                secondary_diagnoses=row.secondary_diagnoses,
                cause_of_death=row.cause_of_death,
                manner_of_death=row.manner_of_death,
                brain_region=row.brain_region,
                brain_region_code=row.brain_region_code,
                tissue_type=row.tissue_type,
                hemisphere=row.hemisphere,
                preservation_method=row.preservation_method,
                postmortem_interval_hours=row.postmortem_interval_hours,
                ph_level=row.ph_level,
                rin_score=row.rin_score,
                quality_metrics=row.quality_metrics,
                quantity_available=row.quantity_available,
                is_available=row.is_available,
                raw_data=row.raw_data,
                extended_data=row.extended_data,
            )
            
            # Normalize similarity to 0-1 range
            similarity = max(0.0, min(1.0, row.similarity))
            
            results.append(SearchResult(sample=sample, score=similarity))
        
        return results


class HybridSearchService:
    """Service combining keyword filters with vector similarity search."""
    
    def __init__(self, session: AsyncSession):
        """Initialize the hybrid search service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.vector_search = VectorSearchService(session)
    
    async def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        diagnosis: str | None = None,
        brain_region: str | None = None,
        source_bank: str | None = None,
        sex: str | None = None,
        min_age: int | None = None,
        max_age: int | None = None,
        min_rin: float | None = None,
        max_pmi: float | None = None,
    ) -> list[SearchResult]:
        """Search with combined vector similarity and keyword filters.
        
        Args:
            query_embedding: Query vector for similarity search
            limit: Maximum number of results
            diagnosis: Filter by diagnosis (partial match)
            brain_region: Filter by brain region (partial match)
            source_bank: Filter by source bank
            sex: Filter by donor sex
            min_age: Minimum donor age
            max_age: Maximum donor age
            min_rin: Minimum RIN score
            max_pmi: Maximum PMI hours
            
        Returns:
            List of SearchResult with samples and scores
        """
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        # Build query with filters
        sql = """
            SELECT 
                samples.*,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM samples
            WHERE embedding IS NOT NULL
        """
        
        params = {"embedding": embedding_str}
        
        # Text filters (partial match)
        if diagnosis:
            sql += " AND primary_diagnosis ILIKE :diagnosis"
            params["diagnosis"] = f"%{diagnosis}%"
        
        if brain_region:
            sql += " AND brain_region ILIKE :brain_region"
            params["brain_region"] = f"%{brain_region}%"
        
        # Exact match filters
        if source_bank:
            sql += " AND source_bank = :source_bank"
            params["source_bank"] = source_bank
        
        if sex:
            sql += " AND donor_sex ILIKE :sex"
            params["sex"] = sex
        
        # Range filters
        if min_age is not None:
            sql += " AND donor_age >= :min_age"
            params["min_age"] = min_age
        
        if max_age is not None:
            sql += " AND donor_age <= :max_age"
            params["max_age"] = max_age
        
        if min_rin is not None:
            sql += " AND rin_score >= :min_rin"
            params["min_rin"] = min_rin
        
        if max_pmi is not None:
            sql += " AND postmortem_interval_hours <= :max_pmi"
            params["max_pmi"] = max_pmi
        
        # Order and limit
        sql += " ORDER BY embedding <=> :embedding::vector LIMIT :limit"
        params["limit"] = limit
        
        # Execute
        result = await self.session.execute(text(sql), params)
        rows = result.fetchall()
        
        # Convert to SearchResult objects
        results = []
        for row in rows:
            sample = Sample(
                id=row.id,
                source_bank=row.source_bank,
                external_id=row.external_id,
                donor_age=row.donor_age,
                donor_sex=row.donor_sex,
                donor_race=row.donor_race,
                primary_diagnosis=row.primary_diagnosis,
                brain_region=row.brain_region,
                rin_score=row.rin_score,
                postmortem_interval_hours=row.postmortem_interval_hours,
                hemisphere=row.hemisphere,
                preservation_method=row.preservation_method,
            )
            
            similarity = max(0.0, min(1.0, row.similarity))
            results.append(SearchResult(sample=sample, score=similarity))
        
        return results


class SemanticSearchService:
    """High-level semantic search service with text query support."""
    
    def __init__(
        self,
        session: AsyncSession,
        embedding_api_key: str,
    ):
        """Initialize the semantic search service.
        
        Args:
            session: Database session
            embedding_api_key: OpenAI API key for embeddings
        """
        self.session = session
        self.embedding_service = EmbeddingService(api_key=embedding_api_key)
        self.hybrid_search = HybridSearchService(session)
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        **filters,
    ) -> list[SearchResult]:
        """Search samples using a natural language query.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            **filters: Additional filters (diagnosis, brain_region, etc.)
            
        Returns:
            List of SearchResult sorted by relevance
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)
        
        # Perform hybrid search
        results = await self.hybrid_search.search(
            query_embedding=query_embedding,
            limit=limit,
            **filters,
        )
        
        # Results are already sorted by similarity
        return results

