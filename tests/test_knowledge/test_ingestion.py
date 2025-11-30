"""Tests for the knowledge ingestion pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from axon.knowledge.scraper import ScrapedDocument
from axon.knowledge.chunker import Chunk
from axon.knowledge.ingestion import KnowledgeIngestion


class TestKnowledgeIngestion:
    """Test suite for KnowledgeIngestion."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service."""
        service = MagicMock()
        service.embed_batch = AsyncMock(return_value=[
            [0.1] * 1536,
            [0.2] * 1536
        ])
        return service

    @pytest.fixture
    def sample_scraped_document(self):
        """Create a sample scraped document."""
        return ScrapedDocument(
            url="https://neurobiobank.nih.gov/about-best-practices/",
            title="Best Practices - NIH NeuroBioBank",
            description="Brain banking best practices",
            markdown_content="""# Best Practices

## Brain Collection

This section describes brain collection protocols.""",
            html_content="<h1>Best Practices</h1>",
            success=True,
            scraped_at=datetime.now(),
            metadata={"statusCode": 200}
        )

    @pytest.fixture
    def sample_chunks(self):
        """Create sample chunks."""
        return [
            Chunk(
                index=0,
                content="# Best Practices\n\nIntroduction to best practices.",
                section_title="Best Practices",
                heading_hierarchy=["Best Practices"],
                token_count=50
            ),
            Chunk(
                index=1,
                content="## Brain Collection\n\nBrain collection protocols.",
                section_title="Brain Collection",
                heading_hierarchy=["Best Practices", "Brain Collection"],
                token_count=45
            )
        ]

    @pytest.mark.asyncio
    async def test_ingest_document_creates_knowledge_document(
        self, mock_db_session, mock_embedding_service, sample_scraped_document, sample_chunks
    ):
        """Test ingesting a document creates a KnowledgeDocument record."""
        ingestion = KnowledgeIngestion(
            db_session=mock_db_session,
            embedding_service=mock_embedding_service
        )
        
        with patch.object(ingestion.chunker, 'chunk_text', return_value=sample_chunks):
            result = await ingestion.ingest_document(
                document=sample_scraped_document,
                source_name="NIH NeuroBioBank",
                content_type="best_practices"
            )
        
        # Should have called session.add for document
        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_ingest_document_creates_chunks_with_embeddings(
        self, mock_db_session, mock_embedding_service, sample_scraped_document, sample_chunks
    ):
        """Test ingesting a document creates chunks with embeddings."""
        ingestion = KnowledgeIngestion(
            db_session=mock_db_session,
            embedding_service=mock_embedding_service
        )
        
        with patch.object(ingestion.chunker, 'chunk_text', return_value=sample_chunks):
            result = await ingestion.ingest_document(
                document=sample_scraped_document,
                source_name="NIH NeuroBioBank",
                content_type="best_practices"
            )
        
        # Should have called embedding service for chunks
        mock_embedding_service.embed_batch.assert_called()

    @pytest.mark.asyncio
    async def test_ingest_document_with_tags(
        self, mock_db_session, mock_embedding_service, sample_scraped_document, sample_chunks
    ):
        """Test ingesting a document with custom tags."""
        ingestion = KnowledgeIngestion(
            db_session=mock_db_session,
            embedding_service=mock_embedding_service
        )
        
        with patch.object(ingestion.chunker, 'chunk_text', return_value=sample_chunks):
            result = await ingestion.ingest_document(
                document=sample_scraped_document,
                source_name="NIH NeuroBioBank",
                content_type="best_practices",
                tags=["brain-banking", "protocols", "quality-control"]
            )
        
        # Document should be created with tags
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_ingest_document_handles_empty_content(
        self, mock_db_session, mock_embedding_service
    ):
        """Test ingesting a document with empty content."""
        empty_doc = ScrapedDocument(
            url="https://example.com/empty",
            title="Empty Page",
            markdown_content="",
            success=True,
            metadata={}
        )
        
        ingestion = KnowledgeIngestion(
            db_session=mock_db_session,
            embedding_service=mock_embedding_service
        )
        
        with patch.object(ingestion.chunker, 'chunk_text', return_value=[]):
            result = await ingestion.ingest_document(
                document=empty_doc,
                source_name="Test",
                content_type="test"
            )
        
        # Should handle gracefully without creating chunks
        assert result is not None

    @pytest.mark.asyncio
    async def test_ingest_updates_existing_document(
        self, mock_db_session, mock_embedding_service, sample_scraped_document, sample_chunks
    ):
        """Test ingesting a URL that already exists updates it."""
        # Mock finding existing document
        existing_doc = MagicMock()
        existing_doc.id = "existing-id"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_doc
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        
        ingestion = KnowledgeIngestion(
            db_session=mock_db_session,
            embedding_service=mock_embedding_service
        )
        
        with patch.object(ingestion.chunker, 'chunk_text', return_value=sample_chunks):
            result = await ingestion.ingest_document(
                document=sample_scraped_document,
                source_name="NIH NeuroBioBank",
                content_type="best_practices",
                update_existing=True
            )
        
        # Should update existing document
        assert mock_db_session.commit.called


class TestKnowledgeIngestionPipeline:
    """Test the full ingestion pipeline."""

    @pytest.fixture
    def mock_scraper(self):
        """Create a mock scraper."""
        scraper = MagicMock()
        scraper.batch_scrape = AsyncMock(return_value=[
            ScrapedDocument(
                url="https://test.com/page1",
                title="Page 1",
                markdown_content="# Page 1 Content",
                success=True,
                metadata={}
            ),
            ScrapedDocument(
                url="https://test.com/page2",
                title="Page 2",
                markdown_content="# Page 2 Content",
                success=True,
                metadata={}
            )
        ])
        return scraper

    @pytest.mark.asyncio
    async def test_ingest_from_urls(self, mock_scraper):
        """Test ingesting from a list of URLs."""
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        
        mock_embedding = MagicMock()
        mock_embedding.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
        
        ingestion = KnowledgeIngestion(
            db_session=mock_session,
            embedding_service=mock_embedding,
            scraper=mock_scraper
        )
        
        urls = [
            "https://test.com/page1",
            "https://test.com/page2"
        ]
        
        results = await ingestion.ingest_from_urls(
            urls=urls,
            source_name="Test Source",
            content_type="test"
        )
        
        # Should scrape all URLs
        mock_scraper.batch_scrape.assert_called_once_with(urls)

    @pytest.mark.asyncio
    async def test_ingest_skips_failed_scrapes(self, mock_scraper):
        """Test that failed scrapes are skipped during ingestion."""
        mock_scraper.batch_scrape = AsyncMock(return_value=[
            ScrapedDocument(
                url="https://test.com/good",
                title="Good Page",
                markdown_content="# Content",
                success=True,
                metadata={}
            ),
            ScrapedDocument(
                url="https://test.com/bad",
                title=None,
                markdown_content=None,
                success=False,
                error="404 Not Found",
                metadata={}
            )
        ])
        
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        
        mock_embedding = MagicMock()
        mock_embedding.embed_batch = AsyncMock(return_value=[[0.1] * 1536])
        
        ingestion = KnowledgeIngestion(
            db_session=mock_session,
            embedding_service=mock_embedding,
            scraper=mock_scraper
        )
        
        results = await ingestion.ingest_from_urls(
            urls=["https://test.com/good", "https://test.com/bad"],
            source_name="Test",
            content_type="test"
        )
        
        # Only successful scrapes should be processed
        assert results["successful"] == 1
        assert results["failed"] == 1

