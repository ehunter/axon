"""CLI commands for data ingestion."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from axon.config import get_settings

app = typer.Typer(help="Import data from brain banks")
console = Console()


async def _run_csv_import(
    filepath: Path,
    source_type: str,
    batch_size: int,
    dry_run: bool,
) -> None:
    """Run the CSV import asynchronously."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from axon.db.models import Base
    from axon.ingest.importer import SampleImporter
    
    # Get adapter based on source type
    if source_type == "nih":
        from axon.ingest.adapters.nih import NIHAdapter
        adapter = NIHAdapter()
    else:
        console.print(f"[red]Unknown source type: {source_type}[/red]")
        raise typer.Exit(1)
    
    # Parse CSV
    console.print(f"[blue]Parsing {filepath.name}...[/blue]")
    samples = list(adapter.process_csv(str(filepath)))
    console.print(f"[green]Found {len(samples)} samples to import[/green]")
    
    if dry_run:
        console.print("[yellow]Dry run - no data will be written[/yellow]")
        
        # Show summary
        from collections import Counter
        sources = Counter(s["source_bank"] for s in samples)
        console.print("\n[bold]Source distribution:[/bold]")
        for source, count in sources.most_common():
            console.print(f"  {source}: {count}")
        
        with_rin = sum(1 for s in samples if s.get("rin_score") is not None)
        console.print(f"\n[bold]Samples with RIN:[/bold] {with_rin}")
        return
    
    # Connect to database
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        importer = SampleImporter(session, auto_create_sources=True)
        
        # Import with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Importing samples...", total=len(samples))
            
            created = 0
            updated = 0
            errors = 0
            
            for i in range(0, len(samples), batch_size):
                batch = samples[i:i + batch_size]
                result = await importer.import_batch(batch)
                
                created += result.created
                updated += result.updated
                errors += result.errors
                
                progress.update(task, advance=len(batch))
            
            await session.commit()
        
        console.print()
        console.print("[bold green]Import complete![/bold green]")
        console.print(f"  Created: {created}")
        console.print(f"  Updated: {updated}")
        console.print(f"  Errors: {errors}")
    
    await engine.dispose()


@app.command("csv")
def import_csv(
    filepath: Path = typer.Argument(
        ...,
        help="Path to CSV file to import",
        exists=True,
        readable=True,
    ),
    source_type: str = typer.Option(
        "nih",
        "--source", "-s",
        help="Source type (nih, harvard, etc.)",
    ),
    batch_size: int = typer.Option(
        100,
        "--batch-size", "-b",
        help="Number of samples per batch",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run", "-n",
        help="Parse CSV but don't write to database",
    ),
):
    """Import brain tissue samples from a CSV file.
    
    Example:
        axon import csv sample_repo_data.csv --source nih
        axon import csv sample_repo_data.csv --dry-run
    """
    console.print(f"[bold]🧠 Axon CSV Import[/bold]")
    console.print(f"File: {filepath}")
    console.print(f"Source: {source_type}")
    console.print()
    
    try:
        asyncio.run(_run_csv_import(filepath, source_type, batch_size, dry_run))
    except KeyboardInterrupt:
        console.print("\n[yellow]Import cancelled[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def import_status():
    """Show import status and database statistics."""
    console.print("[yellow]Not implemented yet[/yellow]")

