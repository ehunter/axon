"""Tests for embedding service.

Following TDD: tests written first, then implementation.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from axon.db.models import Sample


class TestEmbeddingService:
    """Tests for the embedding service."""

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI embedding response."""
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1] * 1536  # 1536 dimensions
        
        mock_response = MagicMock()
        mock_response.data = [mock_embedding]
        mock_response.usage.total_tokens = 10
        
        return mock_response

    @pytest.fixture
    def sample_with_data(self):
        """Create a sample with realistic data."""
        return Sample(
            id="test-sample-1",
            source_bank="NIH Miami",
            external_id="NIH1001",
            donor_age=65,
            donor_sex="female",
            donor_race="White",
            primary_diagnosis="Alzheimer's disease",
            primary_diagnosis_code="G30.9",
            brain_region="Hippocampus, Frontal cortex",
            rin_score=Decimal("7.5"),
            postmortem_interval_hours=Decimal("12.0"),
        )

    @pytest.mark.asyncio
    async def test_create_embedding_for_text(self, mock_openai_response):
        """Should create embedding for text using OpenAI."""
        from axon.rag.embeddings import EmbeddingService
        
        with patch("axon.rag.embeddings.AsyncOpenAI") as mock_client:
            mock_client.return_value.embeddings.create = AsyncMock(
                return_value=mock_openai_response
            )
            
            service = EmbeddingService(api_key="test-key")
            embedding = await service.embed_text("Test text for embedding")
            
            assert embedding is not None
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_create_embeddings_batch(self, mock_openai_response):
        """Should create embeddings for multiple texts in batch."""
        from axon.rag.embeddings import EmbeddingService
        
        # Mock for batch response
        mock_embedding_1 = MagicMock()
        mock_embedding_1.embedding = [0.1] * 1536
        mock_embedding_2 = MagicMock()
        mock_embedding_2.embedding = [0.2] * 1536
        
        mock_batch_response = MagicMock()
        mock_batch_response.data = [mock_embedding_1, mock_embedding_2]
        mock_batch_response.usage.total_tokens = 20
        
        with patch("axon.rag.embeddings.AsyncOpenAI") as mock_client:
            mock_client.return_value.embeddings.create = AsyncMock(
                return_value=mock_batch_response
            )
            
            service = EmbeddingService(api_key="test-key")
            embeddings = await service.embed_batch(["Text 1", "Text 2"])
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 1536
            assert len(embeddings[1]) == 1536

    @pytest.mark.asyncio
    async def test_generate_sample_text(self, sample_with_data):
        """Should generate searchable text from sample."""
        from axon.rag.embeddings import EmbeddingService
        
        service = EmbeddingService(api_key="test-key")
        text = service.generate_sample_text(sample_with_data)
        
        # Should include key fields
        assert "Alzheimer's disease" in text
        assert "Hippocampus" in text
        assert "female" in text
        assert "65" in text
        assert "NIH Miami" in text

    @pytest.mark.asyncio
    async def test_embed_sample(self, sample_with_data, mock_openai_response):
        """Should embed a sample and return the vector."""
        from axon.rag.embeddings import EmbeddingService
        
        with patch("axon.rag.embeddings.AsyncOpenAI") as mock_client:
            mock_client.return_value.embeddings.create = AsyncMock(
                return_value=mock_openai_response
            )
            
            service = EmbeddingService(api_key="test-key")
            embedding = await service.embed_sample(sample_with_data)
            
            assert embedding is not None
            assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_embed_samples_batch(self, sample_with_data, mock_openai_response):
        """Should embed multiple samples in batch."""
        from axon.rag.embeddings import EmbeddingService
        
        samples = [sample_with_data, sample_with_data]
        
        # Mock for batch response
        mock_embedding_1 = MagicMock()
        mock_embedding_1.embedding = [0.1] * 1536
        mock_embedding_2 = MagicMock()
        mock_embedding_2.embedding = [0.2] * 1536
        
        mock_batch_response = MagicMock()
        mock_batch_response.data = [mock_embedding_1, mock_embedding_2]
        mock_batch_response.usage.total_tokens = 40
        
        with patch("axon.rag.embeddings.AsyncOpenAI") as mock_client:
            mock_client.return_value.embeddings.create = AsyncMock(
                return_value=mock_batch_response
            )
            
            service = EmbeddingService(api_key="test-key")
            embeddings = await service.embed_samples(samples)
            
            assert len(embeddings) == 2

    @pytest.mark.asyncio
    async def test_handles_empty_text(self):
        """Should handle empty text gracefully."""
        from axon.rag.embeddings import EmbeddingService
        
        service = EmbeddingService(api_key="test-key")
        
        with pytest.raises(ValueError, match="empty"):
            await service.embed_text("")

    @pytest.mark.asyncio
    async def test_respects_rate_limits(self, mock_openai_response):
        """Should batch requests to respect rate limits."""
        from axon.rag.embeddings import EmbeddingService
        
        with patch("axon.rag.embeddings.AsyncOpenAI") as mock_client:
            mock_client.return_value.embeddings.create = AsyncMock(
                return_value=mock_openai_response
            )
            
            service = EmbeddingService(api_key="test-key", batch_size=100)
            
            # Should be configurable
            assert service.batch_size == 100


class TestSampleTextGeneration:
    """Tests for sample text generation for embeddings."""

    @pytest.fixture
    def minimal_sample(self):
        """Sample with minimal data."""
        return Sample(
            id="min-sample",
            source_bank="Test",
            external_id="T001",
        )

    @pytest.fixture
    def full_sample(self):
        """Sample with all fields populated."""
        return Sample(
            id="full-sample",
            source_bank="NIH Miami",
            external_id="NIH2001",
            donor_age=72,
            donor_sex="male",
            donor_race="Asian",
            donor_ethnicity="Not Hispanic",
            primary_diagnosis="Parkinson's disease",
            primary_diagnosis_code="G20",
            secondary_diagnoses=[{"diagnosis": "Dementia", "code": "F03"}],
            brain_region="Substantia nigra, Hippocampus",
            tissue_type="frozen",
            hemisphere="left",
            preservation_method="Flash frozen",
            rin_score=Decimal("8.5"),
            postmortem_interval_hours=Decimal("6.0"),
            cause_of_death="Natural causes",
        )

    def test_generates_text_from_minimal_sample(self, minimal_sample):
        """Should generate text even with minimal data."""
        from axon.rag.embeddings import EmbeddingService
        
        service = EmbeddingService(api_key="test-key")
        text = service.generate_sample_text(minimal_sample)
        
        assert "Test" in text  # source_bank
        assert text.strip()  # Not empty

    def test_generates_comprehensive_text(self, full_sample):
        """Should include all relevant fields in text."""
        from axon.rag.embeddings import EmbeddingService
        
        service = EmbeddingService(api_key="test-key")
        text = service.generate_sample_text(full_sample)
        
        # Check key fields are present
        assert "Parkinson" in text
        assert "Substantia nigra" in text
        assert "72" in text
        assert "male" in text
        assert "NIH Miami" in text
        assert "8.5" in text or "RIN" in text

    def test_handles_none_values(self, minimal_sample):
        """Should handle None values gracefully."""
        from axon.rag.embeddings import EmbeddingService
        
        service = EmbeddingService(api_key="test-key")
        text = service.generate_sample_text(minimal_sample)
        
        # Should not contain "None" as a string
        assert "None" not in text

