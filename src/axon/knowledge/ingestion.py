"""Knowledge ingestion pipeline for storing scraped content."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from axon.db.models import KnowledgeDocument, KnowledgeChunk
from axon.knowledge.scraper import FirecrawlScraper, ScrapedDocument
from axon.knowledge.chunker import TextChunker, Chunk
from axon.rag.embeddings import EmbeddingService


class KnowledgeIngestion:
    """Pipeline for ingesting web content into the knowledge base."""
    
    def __init__(
        self,
        db_session: AsyncSession,
        embedding_service: EmbeddingService | None = None,
        scraper: FirecrawlScraper | None = None,
        chunker: TextChunker | None = None
    ):
        """Initialize the ingestion pipeline.
        
        Args:
            db_session: Database session for storing documents.
            embedding_service: Service for generating embeddings.
            scraper: Optional scraper instance.
            chunker: Optional chunker instance.
        """
        self.db_session = db_session
        self.embedding_service = embedding_service
        self.scraper = scraper
        self.chunker = chunker or TextChunker()
    
    async def ingest_document(
        self,
        document: ScrapedDocument,
        source_name: str,
        content_type: str,
        tags: list[str] | None = None,
        update_existing: bool = True
    ) -> KnowledgeDocument | None:
        """Ingest a scraped document into the knowledge base.
        
        Args:
            document: The scraped document to ingest.
            source_name: Name of the source (e.g., "NIH NeuroBioBank").
            content_type: Type of content (e.g., "best_practices", "definitions").
            tags: Optional tags for categorization.
            update_existing: Whether to update if document already exists.
            
        Returns:
            The created or updated KnowledgeDocument, or None if failed.
        """
        if not document.success:
            return None
        
        # Check for existing document
        existing = await self._find_existing_document(document.url)
        
        if existing and not update_existing:
            return existing
        
        if existing and update_existing:
            # Update existing document
            return await self._update_document(existing, document, source_name, content_type, tags)
        
        # Create new document
        return await self._create_document(document, source_name, content_type, tags)
    
    async def _find_existing_document(self, url: str) -> KnowledgeDocument | None:
        """Find an existing document by URL."""
        result = await self.db_session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.url == url)
        )
        return result.scalar_one_or_none()
    
    async def _create_document(
        self,
        document: ScrapedDocument,
        source_name: str,
        content_type: str,
        tags: list[str] | None
    ) -> KnowledgeDocument:
        """Create a new knowledge document with chunks."""
        # Create document record
        knowledge_doc = KnowledgeDocument(
            id=str(uuid4()),
            url=document.url,
            title=document.title,
            description=document.description,
            markdown_content=document.markdown_content,
            html_content=document.html_content,
            source_name=source_name,
            content_type=content_type,
            tags=tags,
            last_scraped_at=document.scraped_at,
            scrape_status="success",
            processing_status="pending",
            scrape_metadata=document.metadata,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.db_session.add(knowledge_doc)
        await self.db_session.flush()  # Get the ID
        
        # Chunk the content and create embeddings
        if document.markdown_content:
            await self._create_chunks_with_embeddings(knowledge_doc, document.markdown_content)
        
        knowledge_doc.processing_status = "embedded"
        await self.db_session.commit()
        
        # Refresh to load the chunks relationship
        await self.db_session.refresh(knowledge_doc, ["chunks"])
        
        return knowledge_doc
    
    async def _update_document(
        self,
        existing: KnowledgeDocument,
        document: ScrapedDocument,
        source_name: str,
        content_type: str,
        tags: list[str] | None
    ) -> KnowledgeDocument:
        """Update an existing document and regenerate chunks."""
        # Update document fields
        existing.title = document.title
        existing.description = document.description
        existing.markdown_content = document.markdown_content
        existing.html_content = document.html_content
        existing.source_name = source_name
        existing.content_type = content_type
        existing.tags = tags
        existing.last_scraped_at = document.scraped_at
        existing.scrape_status = "success"
        existing.processing_status = "pending"
        existing.scrape_metadata = document.metadata
        existing.updated_at = datetime.now()
        
        # Delete existing chunks
        await self.db_session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.document_id == existing.id)
        )
        
        # Create new chunks with embeddings
        if document.markdown_content:
            await self._create_chunks_with_embeddings(existing, document.markdown_content)
        
        existing.processing_status = "embedded"
        await self.db_session.commit()
        
        # Refresh to load the chunks relationship
        await self.db_session.refresh(existing, ["chunks"])
        
        return existing
    
    async def _create_chunks_with_embeddings(
        self,
        knowledge_doc: KnowledgeDocument,
        content: str
    ) -> list[KnowledgeChunk]:
        """Create chunks with embeddings for a document."""
        # Chunk the content
        chunks = self.chunker.chunk_text(content)
        
        if not chunks:
            return []
        
        # Generate embeddings if service is available
        embeddings = []
        if self.embedding_service:
            texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed_batch(texts)
        
        # Create chunk records
        chunk_records = []
        for i, chunk in enumerate(chunks):
            embedding = embeddings[i] if i < len(embeddings) else None
            
            chunk_record = KnowledgeChunk(
                id=str(uuid4()),
                document_id=knowledge_doc.id,
                chunk_index=chunk.index,
                content=chunk.content,
                section_title=chunk.section_title,
                heading_hierarchy=chunk.heading_hierarchy,
                token_count=chunk.token_count,
                embedding=embedding,
                created_at=datetime.now()
            )
            
            self.db_session.add(chunk_record)
            chunk_records.append(chunk_record)
        
        return chunk_records
    
    async def ingest_from_urls(
        self,
        urls: list[str],
        source_name: str,
        content_type: str,
        tags: list[str] | None = None,
        update_existing: bool = True
    ) -> dict[str, Any]:
        """Scrape and ingest multiple URLs.
        
        Args:
            urls: List of URLs to scrape and ingest.
            source_name: Name of the source.
            content_type: Type of content.
            tags: Optional tags for all documents.
            update_existing: Whether to update existing documents.
            
        Returns:
            Summary dict with successful/failed counts.
        """
        if not self.scraper:
            raise ValueError("Scraper is required for ingest_from_urls")
        
        # Scrape all URLs
        documents = await self.scraper.batch_scrape(urls)
        
        successful = 0
        failed = 0
        results = []
        
        for doc in documents:
            if doc.success:
                result = await self.ingest_document(
                    document=doc,
                    source_name=source_name,
                    content_type=content_type,
                    tags=tags,
                    update_existing=update_existing
                )
                if result:
                    successful += 1
                    results.append({"url": doc.url, "status": "success", "id": result.id})
                else:
                    failed += 1
                    results.append({"url": doc.url, "status": "failed", "error": "Ingestion failed"})
            else:
                failed += 1
                results.append({"url": doc.url, "status": "failed", "error": doc.error})
        
        return {
            "successful": successful,
            "failed": failed,
            "total": len(urls),
            "results": results
        }


# Predefined configurations for NIH NeuroBioBank pages
NIH_NEUROBIOBANK_PAGES = [
    {
        "url": "https://neurobiobank.nih.gov/about-best-practices/",
        "content_type": "best_practices",
        "tags": ["protocols", "brain-banking", "quality-control"]
    },
    {
        "url": "https://neurobiobank.nih.gov/subjects/",
        "content_type": "definitions",
        "tags": ["neuropathology", "metrics", "staging"]
    }
]


async def ingest_nih_neurobiobank(
    db_session: AsyncSession,
    embedding_service: EmbeddingService,
    scraper: FirecrawlScraper
) -> dict[str, Any]:
    """Convenience function to ingest NIH NeuroBioBank pages.
    
    Args:
        db_session: Database session.
        embedding_service: Embedding service for vectors.
        scraper: Firecrawl scraper instance.
        
    Returns:
        Ingestion summary.
    """
    ingestion = KnowledgeIngestion(
        db_session=db_session,
        embedding_service=embedding_service,
        scraper=scraper
    )
    
    results = []
    
    for page_config in NIH_NEUROBIOBANK_PAGES:
        # Scrape single page
        doc = await scraper.scrape_url(page_config["url"])
        
        if doc.success:
            result = await ingestion.ingest_document(
                document=doc,
                source_name="NIH NeuroBioBank",
                content_type=page_config["content_type"],
                tags=page_config["tags"]
            )
            results.append({
                "url": page_config["url"],
                "status": "success" if result else "failed",
                "chunks": len(result.chunks) if result else 0
            })
        else:
            results.append({
                "url": page_config["url"],
                "status": "failed",
                "error": doc.error
            })
    
    return {
        "source": "NIH NeuroBioBank",
        "pages_processed": len(results),
        "results": results
    }

