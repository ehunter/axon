"""CLI commands for generating embeddings."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from axon.config import get_settings

app = typer.Typer(help="Embedding generation commands")
console = Console()


@app.command("generate")
def generate_embeddings(
    batch_size: int = typer.Option(50, help="Number of samples per batch"),
    limit: Optional[int] = typer.Option(None, help="Maximum samples to process"),
    force: bool = typer.Option(False, help="Regenerate embeddings for all samples"),
    delay: float = typer.Option(1.0, help="Delay between batches (seconds) for rate limiting"),
):
    """Generate embeddings for samples in the database.
    
    Uses OpenAI's text-embedding-3-small model (1536 dimensions).
    Requires OPENAI_API_KEY environment variable.
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        console.print("[red]Error:[/red] OPENAI_API_KEY not set in environment")
        raise typer.Exit(1)
    
    console.print("🧠 [bold]Axon Embedding Generator[/bold]")
    console.print(f"   Batch size: {batch_size}")
    console.print(f"   Delay: {delay}s between batches")
    if limit:
        console.print(f"   Limit: {limit}")
    console.print()
    
    asyncio.run(_generate_embeddings(
        api_key=settings.openai_api_key,
        batch_size=batch_size,
        limit=limit,
        force=force,
        delay=delay,
    ))


async def _generate_embeddings(
    api_key: str,
    batch_size: int,
    limit: Optional[int],
    force: bool,
    delay: float,
):
    """Generate embeddings asynchronously."""
    import asyncio as aio
    from sqlalchemy import select, func, text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from axon.config import get_settings
    from axon.db.models import Sample
    from axon.rag.embeddings import EmbeddingService
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    embedding_service = EmbeddingService(api_key=api_key, batch_size=batch_size)
    
    async with session_factory() as session:
        # Count samples needing embeddings
        if force:
            count_query = select(func.count(Sample.id))
        else:
            count_query = select(func.count(Sample.id)).where(
                text("embedding IS NULL")
            )
        
        result = await session.execute(count_query)
        total_count = result.scalar() or 0
        
        if limit:
            total_count = min(total_count, limit)
        
        if total_count == 0:
            console.print("[green]✓[/green] All samples already have embeddings!")
            return
        
        console.print(f"Found {total_count} samples needing embeddings\n")
        
        processed = 0
        errors = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Generating embeddings...", total=total_count)
            
            offset = 0
            while processed < total_count:
                # Fetch batch of samples
                if force:
                    query = select(Sample).offset(offset).limit(batch_size)
                else:
                    query = select(Sample).where(
                        text("embedding IS NULL")
                    ).limit(batch_size)
                
                result = await session.execute(query)
                samples = result.scalars().all()
                
                if not samples:
                    break
                
                try:
                    # Generate embeddings
                    embeddings = await embedding_service.embed_samples(samples)
                    
                    # Update samples with embeddings
                    conn = await session.connection()
                    raw_conn = await conn.get_raw_connection()
                    asyncpg_conn = raw_conn.driver_connection
                    
                    for sample, embedding in zip(samples, embeddings):
                        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                        await asyncpg_conn.execute(
                            "UPDATE samples SET embedding = $1::vector WHERE id = $2",
                            embedding_str,
                            sample.id
                        )
                    
                    await session.commit()
                    processed += len(samples)
                    
                except Exception as e:
                    console.print(f"\n[red]Error processing batch:[/red] {e}")
                    errors += 1
                    await session.rollback()
                
                progress.update(task, completed=processed)
                
                if force:
                    offset += batch_size
                
                # Rate limiting delay
                if delay > 0 and processed < total_count:
                    await aio.sleep(delay)
        
        console.print()
        console.print(f"[green]✓[/green] Generated embeddings for {processed} samples")
        if errors:
            console.print(f"[yellow]![/yellow] {errors} batches had errors")
    
    await engine.dispose()


@app.command("stats")
def embedding_stats():
    """Show embedding statistics."""
    asyncio.run(_show_stats())


async def _show_stats():
    """Show embedding statistics."""
    from sqlalchemy import select, func, text
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from axon.config import get_settings
    from axon.db.models import Sample
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        # Total samples
        total_result = await session.execute(select(func.count(Sample.id)))
        total = total_result.scalar() or 0
        
        # Samples with embeddings
        with_embedding_result = await session.execute(
            select(func.count(Sample.id)).where(text("embedding IS NOT NULL"))
        )
        with_embedding = with_embedding_result.scalar() or 0
        
        # Samples without embeddings
        without_embedding = total - with_embedding
        
        console.print("\n[bold]Embedding Statistics[/bold]\n")
        console.print(f"  Total samples:     {total:,}")
        console.print(f"  With embeddings:   {with_embedding:,} ({100*with_embedding/total:.1f}%)" if total else "  With embeddings:   0")
        console.print(f"  Without embeddings:{without_embedding:,}" if total else "  Without embeddings: 0")
        console.print()
    
    await engine.dispose()

