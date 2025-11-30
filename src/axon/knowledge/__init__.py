"""Knowledge base module for web-scraped content."""

from axon.knowledge.scraper import FirecrawlScraper
from axon.knowledge.chunker import TextChunker
from axon.knowledge.ingestion import KnowledgeIngestion

__all__ = ["FirecrawlScraper", "TextChunker", "KnowledgeIngestion"]

