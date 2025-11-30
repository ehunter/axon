"""CLI commands for knowledge base management."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from axon.config import get_settings
from axon.db.connection import get_session_factory
from axon.knowledge.scraper import FirecrawlScraper
from axon.knowledge.ingestion import KnowledgeIngestion, NIH_NEUROBIOBANK_PAGES
from axon.rag.embeddings import EmbeddingService

app = typer.Typer(help="Knowledge base management commands")
console = Console()


@app.command("scrape")
def scrape_url(
    url: str = typer.Argument(..., help="URL to scrape"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for markdown"),
):
    """Scrape a single URL and display/save the content."""
    settings = get_settings()
    
    if not settings.firecrawl_api_key:
        console.print("[red]Error: FIRECRAWL_API_KEY not set[/red]")
        raise typer.Exit(1)
    
    async def _scrape():
        scraper = FirecrawlScraper(api_key=settings.firecrawl_api_key)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Scraping {url}...", total=None)
            doc = await scraper.scrape_url(url)
            progress.remove_task(task)
        
        if not doc.success:
            console.print(f"[red]Error: {doc.error}[/red]")
            raise typer.Exit(1)
        
        console.print(f"\n[green]✓ Successfully scraped:[/green] {doc.title or url}")
        console.print(f"[dim]Description: {doc.description or 'N/A'}[/dim]")
        console.print(f"[dim]Content length: {len(doc.markdown_content or '')} characters[/dim]")
        
        if output:
            with open(output, "w") as f:
                f.write(f"# {doc.title or 'Scraped Content'}\n\n")
                f.write(f"Source: {url}\n\n")
                f.write("---\n\n")
                f.write(doc.markdown_content or "")
            console.print(f"[green]Saved to {output}[/green]")
        else:
            console.print("\n[bold]Content Preview:[/bold]")
            preview = (doc.markdown_content or "")[:1000]
            if len(doc.markdown_content or "") > 1000:
                preview += "\n\n... [truncated]"
            console.print(preview)
    
    asyncio.run(_scrape())


@app.command("ingest")
def ingest_url(
    url: str = typer.Argument(..., help="URL to scrape and ingest"),
    source_name: str = typer.Option("Custom", "--source", "-s", help="Source name"),
    content_type: str = typer.Option("general", "--type", "-t", help="Content type"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
):
    """Scrape a URL and ingest it into the knowledge base."""
    settings = get_settings()
    
    if not settings.firecrawl_api_key:
        console.print("[red]Error: FIRECRAWL_API_KEY not set[/red]")
        raise typer.Exit(1)
    
    if not settings.openai_api_key:
        console.print("[red]Error: OPENAI_API_KEY not set for embeddings[/red]")
        raise typer.Exit(1)
    
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    async def _ingest():
        session_factory = get_session_factory()
        scraper = FirecrawlScraper(api_key=settings.firecrawl_api_key)
        embedding_service = EmbeddingService(api_key=settings.openai_api_key)
        
        async with session_factory() as session:
            ingestion = KnowledgeIngestion(
                db_session=session,
                embedding_service=embedding_service,
                scraper=scraper
            )
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                # Scrape
                task = progress.add_task("Scraping URL...", total=None)
                doc = await scraper.scrape_url(url)
                progress.update(task, description="Processing content...")
                
                if not doc.success:
                    progress.remove_task(task)
                    console.print(f"[red]Scrape failed: {doc.error}[/red]")
                    raise typer.Exit(1)
                
                # Ingest
                progress.update(task, description="Creating embeddings...")
                result = await ingestion.ingest_document(
                    document=doc,
                    source_name=source_name,
                    content_type=content_type,
                    tags=tag_list
                )
                progress.remove_task(task)
            
            if result:
                console.print(f"\n[green]✓ Successfully ingested:[/green] {doc.title or url}")
                console.print(f"[dim]Document ID: {result.id}[/dim]")
                console.print(f"[dim]Chunks created: {len(result.chunks)}[/dim]")
            else:
                console.print("[red]Ingestion failed[/red]")
    
    asyncio.run(_ingest())


@app.command("ingest-nih")
def ingest_nih_neurobiobank():
    """Scrape and ingest NIH NeuroBioBank pages."""
    settings = get_settings()
    
    if not settings.firecrawl_api_key:
        console.print("[red]Error: FIRECRAWL_API_KEY not set[/red]")
        raise typer.Exit(1)
    
    if not settings.openai_api_key:
        console.print("[red]Error: OPENAI_API_KEY not set for embeddings[/red]")
        raise typer.Exit(1)
    
    console.print("[bold]Ingesting NIH NeuroBioBank pages...[/bold]\n")
    
    # Show pages to be scraped
    table = Table(title="Pages to Scrape")
    table.add_column("URL")
    table.add_column("Type")
    table.add_column("Tags")
    
    for page in NIH_NEUROBIOBANK_PAGES:
        table.add_row(
            page["url"],
            page["content_type"],
            ", ".join(page["tags"])
        )
    
    console.print(table)
    console.print()
    
    async def _ingest():
        session_factory = get_session_factory()
        scraper = FirecrawlScraper(api_key=settings.firecrawl_api_key)
        embedding_service = EmbeddingService(api_key=settings.openai_api_key)
        
        async with session_factory() as session:
            ingestion = KnowledgeIngestion(
                db_session=session,
                embedding_service=embedding_service,
                scraper=scraper
            )
            
            results = []
            
            for page in NIH_NEUROBIOBANK_PAGES:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Scraping {page['url']}...", total=None)
                    
                    doc = await scraper.scrape_url(page["url"])
                    
                    if doc.success:
                        progress.update(task, description="Creating embeddings...")
                        result = await ingestion.ingest_document(
                            document=doc,
                            source_name="NIH NeuroBioBank",
                            content_type=page["content_type"],
                            tags=page["tags"]
                        )
                        progress.remove_task(task)
                        
                        if result:
                            console.print(f"[green]✓[/green] {page['url']}")
                            console.print(f"  [dim]Chunks: {len(result.chunks)}[/dim]")
                            results.append({"url": page["url"], "status": "success", "chunks": len(result.chunks)})
                        else:
                            console.print(f"[yellow]⚠[/yellow] {page['url']} - Ingestion failed")
                            results.append({"url": page["url"], "status": "failed"})
                    else:
                        progress.remove_task(task)
                        console.print(f"[red]✗[/red] {page['url']} - {doc.error}")
                        results.append({"url": page["url"], "status": "failed", "error": doc.error})
            
            # Summary
            console.print()
            successful = sum(1 for r in results if r["status"] == "success")
            console.print(f"[bold]Summary:[/bold] {successful}/{len(results)} pages ingested successfully")
    
    asyncio.run(_ingest())


@app.command("list")
def list_documents(
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Filter by source name"),
    content_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by content type"),
):
    """List all documents in the knowledge base."""
    from sqlalchemy import select
    from axon.db.models import KnowledgeDocument
    
    async def _list():
        session_factory = get_session_factory()
        
        async with session_factory() as session:
            query = select(KnowledgeDocument)
            
            if source:
                query = query.where(KnowledgeDocument.source_name == source)
            if content_type:
                query = query.where(KnowledgeDocument.content_type == content_type)
            
            result = await session.execute(query)
            documents = result.scalars().all()
            
            if not documents:
                console.print("[dim]No documents found[/dim]")
                return
            
            table = Table(title="Knowledge Base Documents")
            table.add_column("ID", style="dim")
            table.add_column("Title")
            table.add_column("Source")
            table.add_column("Type")
            table.add_column("Status")
            table.add_column("Scraped")
            
            for doc in documents:
                table.add_row(
                    doc.id[:8] + "...",
                    (doc.title or "Untitled")[:40],
                    doc.source_name,
                    doc.content_type,
                    doc.processing_status,
                    doc.last_scraped_at.strftime("%Y-%m-%d %H:%M") if doc.last_scraped_at else "N/A"
                )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(documents)} documents[/dim]")
    
    asyncio.run(_list())


@app.command("stats")
def show_stats():
    """Show knowledge base statistics."""
    from sqlalchemy import select, func
    from axon.db.models import KnowledgeDocument, KnowledgeChunk
    
    async def _stats():
        session_factory = get_session_factory()
        
        async with session_factory() as session:
            # Count documents
            doc_count = await session.execute(
                select(func.count(KnowledgeDocument.id))
            )
            total_docs = doc_count.scalar()
            
            # Count chunks
            chunk_count = await session.execute(
                select(func.count(KnowledgeChunk.id))
            )
            total_chunks = chunk_count.scalar()
            
            # Count embedded chunks
            embedded_count = await session.execute(
                select(func.count(KnowledgeChunk.id)).where(
                    KnowledgeChunk.embedding.isnot(None)
                )
            )
            total_embedded = embedded_count.scalar()
            
            # Count by source
            sources = await session.execute(
                select(
                    KnowledgeDocument.source_name,
                    func.count(KnowledgeDocument.id)
                ).group_by(KnowledgeDocument.source_name)
            )
            source_counts = sources.all()
            
            # Display
            console.print("\n[bold]Knowledge Base Statistics[/bold]\n")
            
            table = Table()
            table.add_column("Metric")
            table.add_column("Value", justify="right")
            
            table.add_row("Total Documents", str(total_docs))
            table.add_row("Total Chunks", str(total_chunks))
            table.add_row("Embedded Chunks", str(total_embedded))
            table.add_row("Embedding Coverage", f"{(total_embedded/total_chunks*100):.1f}%" if total_chunks else "N/A")
            
            console.print(table)
            
            if source_counts:
                console.print("\n[bold]Documents by Source[/bold]\n")
                source_table = Table()
                source_table.add_column("Source")
                source_table.add_column("Count", justify="right")
                
                for source_name, count in source_counts:
                    source_table.add_row(source_name, str(count))
                
                console.print(source_table)
    
    asyncio.run(_stats())


@app.command("delete")
def delete_document(
    document_id: str = typer.Argument(..., help="Document ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a document from the knowledge base."""
    from sqlalchemy import delete as sql_delete, select
    from axon.db.models import KnowledgeDocument
    
    async def _delete():
        session_factory = get_session_factory()
        
        async with session_factory() as session:
            # Find document
            result = await session.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id.like(f"{document_id}%")
                )
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                console.print(f"[red]Document not found: {document_id}[/red]")
                raise typer.Exit(1)
            
            if not force:
                console.print(f"[yellow]About to delete:[/yellow] {doc.title or doc.url}")
                confirm = typer.confirm("Are you sure?")
                if not confirm:
                    console.print("[dim]Cancelled[/dim]")
                    return
            
            await session.execute(
                sql_delete(KnowledgeDocument).where(KnowledgeDocument.id == doc.id)
            )
            await session.commit()
            
            console.print(f"[green]✓ Deleted document: {doc.title or doc.url}[/green]")
    
    asyncio.run(_delete())

