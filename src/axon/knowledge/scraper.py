"""Firecrawl scraper service for web content extraction."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from firecrawl import FirecrawlApp

from axon.config import get_settings


@dataclass
class ScrapedDocument:
    """Represents a scraped document from a URL."""
    
    url: str
    title: str | None = None
    description: str | None = None
    markdown_content: str | None = None
    html_content: str | None = None
    success: bool = False
    error: str | None = None
    scraped_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class FirecrawlScraper:
    """Service for scraping web pages using Firecrawl API."""
    
    def __init__(self, api_key: str | None = None):
        """Initialize the scraper with Firecrawl API key.
        
        Args:
            api_key: Firecrawl API key. If not provided, uses settings.
        """
        self.api_key = api_key or get_settings().firecrawl_api_key
        
        if not self.api_key:
            raise ValueError("Firecrawl API key is required. Set FIRECRAWL_API_KEY environment variable.")
        
        self.client = FirecrawlApp(api_key=self.api_key)
    
    def _call_firecrawl(self, url: str, formats: list[str] | None = None) -> dict[str, Any]:
        """Make a synchronous call to Firecrawl API.
        
        Args:
            url: URL to scrape.
            formats: Output formats (default: ["markdown", "html"]).
            
        Returns:
            Dictionary with success status and document data.
        """
        if formats is None:
            formats = ["markdown", "html"]
        
        try:
            result = self.client.scrape(url, formats=formats)
            
            # Firecrawl v4 returns a Document object - extract fields
            metadata = {}
            if result.metadata:
                metadata = {
                    "title": result.metadata.title,
                    "description": result.metadata.description,
                    "url": result.metadata.url,
                    "language": result.metadata.language,
                    "source_url": result.metadata.source_url,
                    "status_code": result.metadata.status_code,
                }
            
            return {
                "success": True,
                "markdown": result.markdown or "",
                "html": result.html,
                "metadata": metadata,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def scrape_url(
        self,
        url: str,
        formats: list[str] | None = None
    ) -> ScrapedDocument:
        """Scrape a single URL and return structured content.
        
        Args:
            url: URL to scrape.
            formats: Output formats (default: ["markdown", "html"]).
            
        Returns:
            ScrapedDocument with content and metadata.
        """
        # Run synchronous Firecrawl call in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._call_firecrawl(url, formats)
        )
        
        if not response.get("success"):
            return ScrapedDocument(
                url=url,
                success=False,
                error=response.get("error", "Unknown error"),
                scraped_at=datetime.now()
            )
        
        metadata = response.get("metadata", {})
        
        return ScrapedDocument(
            url=url,
            title=metadata.get("title"),
            description=metadata.get("description"),
            markdown_content=response.get("markdown", ""),
            html_content=response.get("html"),
            success=True,
            scraped_at=datetime.now(),
            metadata=metadata
        )
    
    async def batch_scrape(
        self,
        urls: list[str],
        formats: list[str] | None = None,
        delay_between: float = 1.0
    ) -> list[ScrapedDocument]:
        """Scrape multiple URLs with rate limiting.
        
        Args:
            urls: List of URLs to scrape.
            formats: Output formats for each page.
            delay_between: Delay in seconds between requests.
            
        Returns:
            List of ScrapedDocument objects.
        """
        results = []
        
        for i, url in enumerate(urls):
            doc = await self.scrape_url(url, formats)
            results.append(doc)
            
            # Rate limiting - wait between requests (except for last one)
            if i < len(urls) - 1 and delay_between > 0:
                await asyncio.sleep(delay_between)
        
        return results
    
    async def scrape_with_retry(
        self,
        url: str,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        formats: list[str] | None = None
    ) -> ScrapedDocument:
        """Scrape a URL with retry logic for transient failures.
        
        Args:
            url: URL to scrape.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
            formats: Output formats.
            
        Returns:
            ScrapedDocument with content or error.
        """
        last_error = None
        
        for attempt in range(max_retries):
            doc = await self.scrape_url(url, formats)
            
            if doc.success:
                return doc
            
            last_error = doc.error
            
            # Don't retry on 404s or similar permanent errors
            if "not found" in (last_error or "").lower():
                break
            
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
        
        return ScrapedDocument(
            url=url,
            success=False,
            error=f"Failed after {max_retries} attempts: {last_error}",
            scraped_at=datetime.now()
        )

