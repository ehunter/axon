"""Tests for the Firecrawl scraper service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from axon.knowledge.scraper import FirecrawlScraper, ScrapedDocument


class TestFirecrawlScraper:
    """Test suite for FirecrawlScraper."""

    def test_scraper_initialization_with_api_key(self):
        """Test scraper initializes with API key."""
        scraper = FirecrawlScraper(api_key="test-api-key")
        assert scraper.api_key == "test-api-key"

    def test_scraper_initialization_without_api_key_raises(self):
        """Test scraper raises error without API key."""
        with pytest.raises(ValueError, match="Firecrawl API key is required"):
            FirecrawlScraper(api_key="")

    @pytest.mark.asyncio
    async def test_scrape_url_returns_scraped_document(self):
        """Test scraping a URL returns a ScrapedDocument."""
        scraper = FirecrawlScraper(api_key="test-api-key")
        
        mock_response = {
            "success": True,
            "data": {
                "markdown": "# Best Practices\n\nThis is content about brain banking.",
                "html": "<h1>Best Practices</h1><p>This is content about brain banking.</p>",
                "metadata": {
                    "title": "Best Practices - NIH NeuroBioBank",
                    "description": "Brain banking best practices guide",
                    "sourceURL": "https://neurobiobank.nih.gov/about-best-practices/",
                    "statusCode": 200
                }
            }
        }
        
        with patch.object(scraper, '_call_firecrawl', return_value=mock_response):
            result = await scraper.scrape_url("https://neurobiobank.nih.gov/about-best-practices/")
        
        assert isinstance(result, ScrapedDocument)
        assert result.url == "https://neurobiobank.nih.gov/about-best-practices/"
        assert result.title == "Best Practices - NIH NeuroBioBank"
        assert "Best Practices" in result.markdown_content
        assert result.success is True

    @pytest.mark.asyncio
    async def test_scrape_url_handles_failure(self):
        """Test scraping handles failures gracefully."""
        scraper = FirecrawlScraper(api_key="test-api-key")
        
        mock_response = {
            "success": False,
            "error": "Page not found"
        }
        
        with patch.object(scraper, '_call_firecrawl', return_value=mock_response):
            result = await scraper.scrape_url("https://example.com/nonexistent")
        
        assert result.success is False
        assert result.error == "Page not found"

    @pytest.mark.asyncio
    async def test_batch_scrape_multiple_urls(self):
        """Test batch scraping multiple URLs."""
        scraper = FirecrawlScraper(api_key="test-api-key")
        
        urls = [
            "https://neurobiobank.nih.gov/about-best-practices/",
            "https://neurobiobank.nih.gov/subjects/"
        ]
        
        mock_responses = [
            ScrapedDocument(
                url=urls[0],
                title="Best Practices",
                markdown_content="# Best Practices",
                html_content="<h1>Best Practices</h1>",
                success=True,
                metadata={}
            ),
            ScrapedDocument(
                url=urls[1],
                title="Subjects",
                markdown_content="# Subjects",
                html_content="<h1>Subjects</h1>",
                success=True,
                metadata={}
            )
        ]
        
        with patch.object(scraper, 'scrape_url', side_effect=mock_responses):
            results = await scraper.batch_scrape(urls)
        
        assert len(results) == 2
        assert all(doc.success for doc in results)

    def test_scraped_document_dataclass(self):
        """Test ScrapedDocument dataclass creation."""
        doc = ScrapedDocument(
            url="https://example.com",
            title="Test Title",
            description="Test description",
            markdown_content="# Test",
            html_content="<h1>Test</h1>",
            success=True,
            scraped_at=datetime.now(),
            metadata={"statusCode": 200}
        )
        
        assert doc.url == "https://example.com"
        assert doc.title == "Test Title"
        assert doc.success is True


class TestScrapedDocumentValidation:
    """Test ScrapedDocument validation and edge cases."""

    def test_empty_content_is_valid(self):
        """Test document with empty content is still valid."""
        doc = ScrapedDocument(
            url="https://example.com",
            title=None,
            markdown_content="",
            html_content="",
            success=True,
            metadata={}
        )
        assert doc.success is True
        assert doc.markdown_content == ""

    def test_long_url_handling(self):
        """Test handling of very long URLs."""
        long_url = "https://example.com/" + "a" * 1900  # Close to 2000 char limit
        doc = ScrapedDocument(
            url=long_url,
            title="Test",
            markdown_content="Content",
            success=True,
            metadata={}
        )
        assert len(doc.url) < 2000

