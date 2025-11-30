"""Tests for vector similarity search.

Following TDD: tests written first, then implementation.

NOTE: These tests require PostgreSQL with pgvector extension.
They will be skipped when running with SQLite (default test database).
"""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from axon.db.models import Sample

# These tests require PostgreSQL with pgvector extension.
# They will be skipped in the default test environment (SQLite).
# To run these tests, set DATABASE_URL to a PostgreSQL connection string.
import os

USES_POSTGRES = "postgresql" in os.environ.get("DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not USES_POSTGRES,
    reason="Vector search tests require PostgreSQL with pgvector"
)


@pytest.fixture
def sample_embedding():
    """A sample embedding vector."""
    return [0.1] * 1536


@pytest.fixture
async def samples_with_embeddings(db_session):
    """Create samples with embeddings in the database."""
    # Create samples with different diagnoses
    samples = [
        Sample(
            source_bank="NIH Miami",
            external_id="NIH1001",
            donor_age=65,
            donor_sex="female",
            primary_diagnosis="Alzheimer's disease",
            brain_region="Hippocampus",
            rin_score=Decimal("7.5"),
            embedding=[0.1, 0.2, 0.3] + [0.0] * 1533,  # Similar to Alzheimer's query
        ),
        Sample(
            source_bank="NIH Miami",
            external_id="NIH1002",
            donor_age=70,
            donor_sex="male",
            primary_diagnosis="Parkinson's disease",
            brain_region="Substantia nigra",
            rin_score=Decimal("6.8"),
            embedding=[0.9, 0.8, 0.7] + [0.0] * 1533,  # Different
        ),
        Sample(
            source_bank="Harvard",
            external_id="H2001",
            donor_age=68,
            donor_sex="female",
            primary_diagnosis="Alzheimer's disease with dementia",
            brain_region="Frontal cortex",
            rin_score=Decimal("8.2"),
            embedding=[0.15, 0.25, 0.35] + [0.0] * 1533,  # Similar to Alzheimer's
        ),
    ]
    
    for sample in samples:
        db_session.add(sample)
    await db_session.commit()
    
    for sample in samples:
        await db_session.refresh(sample)
    
    return samples


class TestVectorSearch:
    """Tests for vector similarity search."""

    @pytest.mark.asyncio
    async def test_find_similar_samples(self, db_session, samples_with_embeddings):
        """Should find samples similar to a query embedding."""
        from axon.rag.search import VectorSearchService
        
        # Query embedding similar to Alzheimer's samples
        query_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        service = VectorSearchService(db_session)
        results = await service.search_similar(query_embedding, limit=2)
        
        assert len(results) == 2
        # Should find Alzheimer's samples first (more similar)
        diagnoses = [r.sample.primary_diagnosis for r in results]
        assert any("Alzheimer" in d for d in diagnoses)

    @pytest.mark.asyncio
    async def test_returns_similarity_scores(self, db_session, samples_with_embeddings):
        """Should return similarity scores with results."""
        from axon.rag.search import VectorSearchService
        
        query_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        service = VectorSearchService(db_session)
        results = await service.search_similar(query_embedding, limit=3)
        
        for result in results:
            assert hasattr(result, "score")
            assert 0 <= result.score <= 1  # Normalized similarity

    @pytest.mark.asyncio
    async def test_respects_limit(self, db_session, samples_with_embeddings):
        """Should respect the limit parameter."""
        from axon.rag.search import VectorSearchService
        
        query_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        service = VectorSearchService(db_session)
        results = await service.search_similar(query_embedding, limit=1)
        
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_filter_by_source_bank(self, db_session, samples_with_embeddings):
        """Should filter results by source bank."""
        from axon.rag.search import VectorSearchService
        
        query_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        service = VectorSearchService(db_session)
        results = await service.search_similar(
            query_embedding,
            limit=10,
            source_bank="Harvard"
        )
        
        assert len(results) == 1
        assert results[0].sample.source_bank == "Harvard"

    @pytest.mark.asyncio
    async def test_filter_by_min_rin(self, db_session, samples_with_embeddings):
        """Should filter results by minimum RIN score."""
        from axon.rag.search import VectorSearchService
        
        query_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        service = VectorSearchService(db_session)
        results = await service.search_similar(
            query_embedding,
            limit=10,
            min_rin=7.0
        )
        
        assert len(results) == 2  # Two samples have RIN >= 7.0
        for result in results:
            assert float(result.sample.rin_score) >= 7.0


class TestHybridSearch:
    """Tests for hybrid search combining keyword and vector search."""

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_filters(
        self, db_session, samples_with_embeddings
    ):
        """Should combine keyword filters with vector similarity."""
        from axon.rag.search import HybridSearchService
        
        query_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        service = HybridSearchService(db_session)
        results = await service.search(
            query_embedding=query_embedding,
            diagnosis="Alzheimer",
            limit=10
        )
        
        # Should only return Alzheimer's samples
        for result in results:
            assert "Alzheimer" in result.sample.primary_diagnosis

    @pytest.mark.asyncio
    async def test_hybrid_search_with_brain_region(
        self, db_session, samples_with_embeddings
    ):
        """Should filter by brain region."""
        from axon.rag.search import HybridSearchService
        
        query_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        service = HybridSearchService(db_session)
        results = await service.search(
            query_embedding=query_embedding,
            brain_region="Hippocampus",
            limit=10
        )
        
        assert len(results) == 1
        assert "Hippocampus" in results[0].sample.brain_region


class TestSemanticSearch:
    """Tests for end-to-end semantic search with query embedding."""

    @pytest.mark.asyncio
    async def test_search_by_text_query(self, db_session, samples_with_embeddings):
        """Should search using a text query."""
        from axon.rag.search import SemanticSearchService
        
        # Mock the embedding service
        mock_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        with patch("axon.rag.search.EmbeddingService") as MockEmbedding:
            mock_service = MockEmbedding.return_value
            mock_service.embed_query = AsyncMock(return_value=mock_embedding)
            
            service = SemanticSearchService(
                db_session,
                embedding_api_key="test-key"
            )
            results = await service.search(
                query="Alzheimer's disease in hippocampus",
                limit=2
            )
            
            assert len(results) >= 1
            mock_service.embed_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_returns_ranked_results(
        self, db_session, samples_with_embeddings
    ):
        """Should return results ranked by relevance."""
        from axon.rag.search import SemanticSearchService
        
        mock_embedding = [0.12, 0.22, 0.32] + [0.0] * 1533
        
        with patch("axon.rag.search.EmbeddingService") as MockEmbedding:
            mock_service = MockEmbedding.return_value
            mock_service.embed_query = AsyncMock(return_value=mock_embedding)
            
            service = SemanticSearchService(
                db_session,
                embedding_api_key="test-key"
            )
            results = await service.search(query="brain samples", limit=3)
            
            # Results should be sorted by score (descending)
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)

