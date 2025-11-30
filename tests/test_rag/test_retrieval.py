"""Tests for RAG retrieval layer.

Following TDD: tests written first, then implementation.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from axon.db.models import Sample


@pytest.fixture
def mock_samples():
    """Create mock samples for testing."""
    return [
        Sample(
            id="sample-1",
            source_bank="NIH Miami",
            external_id="NIH1001",
            donor_age=65,
            donor_sex="female",
            primary_diagnosis="Alzheimer's disease",
            brain_region="Hippocampus, Frontal cortex",
            rin_score=Decimal("7.5"),
            postmortem_interval_hours=Decimal("12.0"),
        ),
        Sample(
            id="sample-2",
            source_bank="Harvard",
            external_id="H2001",
            donor_age=72,
            donor_sex="male",
            primary_diagnosis="Alzheimer's disease with dementia",
            brain_region="Hippocampus",
            rin_score=Decimal("8.2"),
            postmortem_interval_hours=Decimal("6.0"),
        ),
    ]


class TestContextBuilder:
    """Tests for building LLM context from retrieved samples."""

    def test_format_sample_for_context(self, mock_samples):
        """Should format a single sample for LLM context."""
        from axon.rag.retrieval import ContextBuilder
        
        builder = ContextBuilder()
        context = builder.format_sample(mock_samples[0])
        
        # Should include key information
        assert "Alzheimer's disease" in context
        assert "Hippocampus" in context
        assert "65" in context
        assert "female" in context
        assert "NIH Miami" in context

    def test_format_multiple_samples(self, mock_samples):
        """Should format multiple samples with numbering."""
        from axon.rag.retrieval import ContextBuilder
        
        builder = ContextBuilder()
        context = builder.format_samples(mock_samples)
        
        # Should have numbered samples
        assert "Sample 1" in context or "[1]" in context
        assert "Sample 2" in context or "[2]" in context
        assert "NIH Miami" in context
        assert "Harvard" in context

    def test_build_system_prompt(self):
        """Should build appropriate system prompt for brain bank assistant."""
        from axon.rag.retrieval import ContextBuilder
        
        builder = ContextBuilder()
        prompt = builder.build_system_prompt()
        
        # Should describe the assistant's role
        assert "brain" in prompt.lower()
        assert "sample" in prompt.lower() or "tissue" in prompt.lower()

    def test_build_context_with_query(self, mock_samples):
        """Should build full context with query and samples."""
        from axon.rag.retrieval import ContextBuilder
        
        builder = ContextBuilder()
        context = builder.build_context(
            query="Find Alzheimer's samples with good RNA quality",
            samples=mock_samples,
        )
        
        assert "Alzheimer" in context
        assert len(context) > 100  # Should be substantial


class TestRAGRetriever:
    """Tests for the RAG retrieval service."""

    @pytest.mark.asyncio
    async def test_retrieve_relevant_samples(self):
        """Should retrieve samples relevant to query."""
        from axon.rag.retrieval import RAGRetriever
        
        # Mock the semantic search
        mock_results = [
            MagicMock(sample=MagicMock(
                id="s1",
                primary_diagnosis="Alzheimer's",
                brain_region="Hippocampus",
            ), score=0.9),
            MagicMock(sample=MagicMock(
                id="s2", 
                primary_diagnosis="Alzheimer's with dementia",
                brain_region="Frontal cortex",
            ), score=0.85),
        ]
        
        with patch("axon.rag.retrieval.EmbeddingService") as MockEmbed:
            mock_embed = MockEmbed.return_value
            mock_embed.embed_query = AsyncMock(return_value=[0.1] * 1536)
            
            retriever = RAGRetriever(
                db_session=MagicMock(),
                embedding_api_key="test-key",
            )
            retriever._search_samples = AsyncMock(return_value=mock_results)
            
            results = await retriever.retrieve(
                query="Alzheimer's samples from hippocampus",
                limit=5,
            )
            
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_with_filters(self):
        """Should pass filters to search."""
        from axon.rag.retrieval import RAGRetriever
        
        with patch("axon.rag.retrieval.EmbeddingService") as MockEmbed:
            mock_embed = MockEmbed.return_value
            mock_embed.embed_query = AsyncMock(return_value=[0.1] * 1536)
            
            retriever = RAGRetriever(
                db_session=MagicMock(),
                embedding_api_key="test-key",
            )
            retriever._search_samples = AsyncMock(return_value=[])
            
            await retriever.retrieve(
                query="Parkinson's samples",
                limit=10,
                min_rin=7.0,
                source_bank="NIH Miami",
            )
            
            # Verify filters were passed
            call_kwargs = retriever._search_samples.call_args[1]
            assert call_kwargs.get("min_rin") == 7.0
            assert call_kwargs.get("source_bank") == "NIH Miami"


class TestRAGPipeline:
    """Tests for the complete RAG pipeline."""

    @pytest.mark.asyncio
    async def test_generate_response(self):
        """Should generate response using retrieved context."""
        from axon.rag.retrieval import RAGPipeline
        
        mock_sample = Sample(
            id="s1",
            source_bank="NIH Miami",
            external_id="NIH1001",
            primary_diagnosis="Alzheimer's disease",
            brain_region="Hippocampus",
            donor_age=65,
            donor_sex="female",
            rin_score=Decimal("7.5"),
            raw_data={},
        )
        
        from axon.rag.retrieval import RetrievedSample
        mock_results = [RetrievedSample(sample=mock_sample, score=0.9)]
        
        with patch("axon.rag.retrieval.RAGRetriever") as MockRetriever:
            mock_retriever = MockRetriever.return_value
            mock_retriever.retrieve = AsyncMock(return_value=mock_results)
            
            with patch("axon.rag.retrieval.AsyncAnthropic") as MockAnthropic:
                mock_client = MockAnthropic.return_value
                mock_response = MagicMock()
                mock_response.content = [MagicMock(text="Based on the available samples...")]
                mock_client.messages.create = AsyncMock(return_value=mock_response)
                
                pipeline = RAGPipeline(
                    db_session=MagicMock(),
                    embedding_api_key="test-embed-key",
                    anthropic_api_key="test-anthropic-key",
                )
                pipeline.retriever = mock_retriever
                
                response = await pipeline.query(
                    "What Alzheimer's samples do you have?"
                )
                
                assert response.answer is not None
                assert len(response.sources) > 0

    @pytest.mark.asyncio
    async def test_includes_source_references(self):
        """Should include source sample references in response."""
        from axon.rag.retrieval import RAGPipeline
        
        mock_sample = Sample(
            id="sample-123",
            source_bank="NIH Miami",
            external_id="NIH1001",
            primary_diagnosis="Alzheimer's",
            raw_data={},
        )
        
        from axon.rag.retrieval import RetrievedSample
        mock_results = [RetrievedSample(sample=mock_sample, score=0.9)]
        
        with patch("axon.rag.retrieval.RAGRetriever") as MockRetriever:
            mock_retriever = MockRetriever.return_value
            mock_retriever.retrieve = AsyncMock(return_value=mock_results)
            
            with patch("axon.rag.retrieval.AsyncAnthropic") as MockAnthropic:
                mock_client = MockAnthropic.return_value
                mock_response = MagicMock()
                mock_response.content = [MagicMock(text="Here are the samples...")]
                mock_client.messages.create = AsyncMock(return_value=mock_response)
                
                pipeline = RAGPipeline(
                    db_session=MagicMock(),
                    embedding_api_key="test-embed-key",
                    anthropic_api_key="test-anthropic-key",
                )
                pipeline.retriever = mock_retriever
                
                response = await pipeline.query("Find samples")
                
                # Should include sample IDs in sources
                assert "sample-123" in [s.id for s in response.sources]

