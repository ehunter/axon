"""CLI commands for exporting sample selections."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from axon.export import ExportService, ExportFormat
from axon.export.service import ExportMetadata

console = Console()
app = typer.Typer(help="Export sample selections")


def get_format_from_string(format_str: str) -> ExportFormat:
    """Convert string to ExportFormat enum."""
    format_map = {
        "csv": ExportFormat.CSV,
        "xlsx": ExportFormat.EXCEL,
        "excel": ExportFormat.EXCEL,
        "json": ExportFormat.JSON,
        "txt": ExportFormat.TEXT,
        "text": ExportFormat.TEXT,
    }
    return format_map.get(format_str.lower(), ExportFormat.CSV)


@app.command("selection")
def export_selection(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path. If not specified, prints to stdout (for text/csv) or uses default filename.",
    ),
    format: str = typer.Option(
        "csv", "--format", "-f",
        help="Export format: csv, xlsx/excel, json, txt/text",
    ),
    researcher: Optional[str] = typer.Option(
        None, "--researcher", "-r",
        help="Researcher name for the report",
    ),
    purpose: Optional[str] = typer.Option(
        None, "--purpose", "-p",
        help="Research purpose description",
    ),
    tissue_use: Optional[str] = typer.Option(
        None, "--tissue-use", "-t",
        help="Intended tissue use (e.g., RNA-seq, Histology)",
    ),
    notes: Optional[str] = typer.Option(
        None, "--notes", "-n",
        help="Additional notes for the export",
    ),
):
    """Export the current sample selection to a file.
    
    This command requires an active chat session with selected samples.
    Use 'axon chat' first to select samples, then use this command.
    
    Example:
        axon export selection -f xlsx -o my_samples.xlsx
        axon export selection -f csv --researcher "Dr. Smith" --purpose "AD study"
    """
    # Note: This is a standalone command. For integrated export,
    # use /export within the chat session.
    console.print(
        Panel(
            "[yellow]Note:[/yellow] This command exports from the [bold]current chat session[/bold].\n"
            "Use [cyan]/export[/cyan] within an active chat session to export your selection.\n\n"
            "Or use [cyan]axon chat[/cyan] to start a session and select samples first.",
            title="Export Info",
        )
    )


@app.command("demo")
def export_demo(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path",
    ),
    format: str = typer.Option(
        "txt", "--format", "-f",
        help="Export format: csv, xlsx, json, txt",
    ),
):
    """Generate a demo export to test the export functionality."""
    from axon.agent.tools import SampleSelection, SelectedSample
    
    # Create demo selection
    selection = SampleSelection()
    
    # Add demo cases
    selection.add_case(SelectedSample(
        id="demo-1",
        external_id="6662",
        diagnosis="Alzheimer's disease",
        age=75,
        sex="female",
        rin=8.9,
        pmi=8.8,
        brain_region="Frontal cortex",
        source_bank="NIH Sepulveda",
        braak_stage="NFT Stage V",
        copathologies="None recorded",
    ))
    selection.add_case(SelectedSample(
        id="demo-2",
        external_id="6713",
        diagnosis="Alzheimer's disease",
        age=81,
        sex="male",
        rin=8.2,
        pmi=23.6,
        brain_region="Frontal cortex",
        source_bank="NIH Miami",
        braak_stage="NFT Stage VI",
        copathologies="CAA noted",
    ))
    
    # Add demo controls
    selection.add_control(SelectedSample(
        id="demo-3",
        external_id="6922",
        diagnosis="Control",
        age=73,
        sex="female",
        rin=9.1,
        pmi=25.9,
        brain_region="Frontal cortex",
        source_bank="NIH Pittsburgh",
        braak_stage=None,
        copathologies="None recorded",
    ))
    selection.add_control(SelectedSample(
        id="demo-4",
        external_id="6820",
        diagnosis="Control",
        age=65,
        sex="male",
        rin=8.7,
        pmi=18.3,
        brain_region="Frontal cortex",
        source_bank="NIH Maryland",
        braak_stage=None,
        copathologies="None recorded",
    ))
    
    # Create metadata
    metadata = ExportMetadata(
        researcher_name="Demo Researcher",
        research_purpose="Testing Axon export functionality",
        tissue_use="RNA-seq",
        selection_criteria={
            "diagnosis": "Alzheimer's disease",
            "age_range": "65+",
            "brain_region": "Frontal cortex",
            "RIN_minimum": 6.5,
            "controls": "Age-matched",
        },
        notes="This is a demo export to test the system.",
    )
    
    # Export
    export_format = get_format_from_string(format)
    service = ExportService(selection, metadata)
    result = service.export(export_format)
    
    if output:
        if isinstance(result.content, bytes):
            output.write_bytes(result.content)
        else:
            output.write_text(result.content)
        console.print(f"[green]✓[/green] Exported {result.sample_count} samples to {output}")
    else:
        if isinstance(result.content, str):
            console.print(result.content)
        else:
            # For binary formats, must specify output
            default_path = Path(result.filename)
            default_path.write_bytes(result.content)
            console.print(f"[green]✓[/green] Exported {result.sample_count} samples to {default_path}")
    
    # Show summary
    console.print()
    table = Table(title="Export Summary")
    table.add_column("Property", style="cyan")
    table.add_column("Value")
    table.add_row("Format", result.format.value)
    table.add_row("Filename", result.filename)
    table.add_row("Samples", str(result.sample_count))
    console.print(table)


@app.command("admin-email")
def export_admin_email(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path for the email text",
    ),
):
    """Generate a demo admin email for brain bank administrators."""
    from axon.agent.tools import SampleSelection, SelectedSample
    
    # Create demo selection (same as above)
    selection = SampleSelection()
    
    selection.add_case(SelectedSample(
        id="demo-1",
        external_id="6662",
        diagnosis="Alzheimer's disease",
        age=75,
        sex="female",
        rin=8.9,
        pmi=8.8,
        brain_region="Frontal cortex",
        source_bank="NIH Sepulveda",
        braak_stage="NFT Stage V",
        copathologies="None recorded",
    ))
    selection.add_case(SelectedSample(
        id="demo-2",
        external_id="6713",
        diagnosis="Alzheimer's disease",
        age=81,
        sex="male",
        rin=8.2,
        pmi=23.6,
        brain_region="Frontal cortex",
        source_bank="NIH Miami",
        braak_stage="NFT Stage VI",
        copathologies="CAA noted",
    ))
    
    selection.add_control(SelectedSample(
        id="demo-3",
        external_id="6922",
        diagnosis="Control",
        age=73,
        sex="female",
        rin=9.1,
        pmi=25.9,
        brain_region="Frontal cortex",
        source_bank="NIH Pittsburgh",
        braak_stage=None,
        copathologies="None recorded",
    ))
    
    metadata = ExportMetadata(
        researcher_name="Dr. Jane Smith",
        research_purpose="Investigating tau pathology in late-onset Alzheimer's disease",
        tissue_use="RNA-seq",
        selection_criteria={
            "diagnosis": "Alzheimer's disease",
            "age_range": "65+",
            "brain_region": "Frontal cortex",
            "Braak_stage": "V-VI",
            "RIN_minimum": 6.5,
        },
    )
    
    service = ExportService(selection, metadata)
    email_text = service.generate_admin_email()
    
    if output:
        output.write_text(email_text)
        console.print(f"[green]✓[/green] Admin email saved to {output}")
    else:
        console.print(Panel(email_text, title="Admin Email Preview"))

