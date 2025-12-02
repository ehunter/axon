"""CLI command for interactive chat with Axon."""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme
from rich.status import Status
from rich.table import Table

from axon.config import get_settings

app = typer.Typer(help="Chat with Axon brain bank assistant")
console = Console(theme=Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "info": "dim",
    "tool": "bold yellow",
}))


@app.command("start")
def start_chat(
    use_tools: bool = typer.Option(True, help="Use tool-based agent (prevents hallucination)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logging"),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream responses in real-time"),
):
    """Start an interactive chat session with Axon.
    
    Chat with the AI assistant to find brain tissue samples.
    
    Commands:
        quit/exit - End the session
        new - Start a fresh conversation
        selection - See current sample selection
        export [format] - Export selection (csv, xlsx, json, txt)
        email - Preview admin email summary
        help - Show all commands
    """
    import logging
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("axon").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce HTTP noise
    
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        console.print("[red]Error:[/red] ANTHROPIC_API_KEY not set")
        raise typer.Exit(1)
    
    asyncio.run(_chat_loop(
        anthropic_key=settings.anthropic_api_key,
        use_tools=use_tools,
        stream=stream,
    ))


async def _chat_loop(
    anthropic_key: str,
    use_tools: bool = True,
    stream: bool = True,
):
    """Main chat loop."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from axon.agent.chat_with_tools import ToolBasedChatAgent, StreamEventType
    from axon.agent.persistence import ConversationService
    from axon.config import get_settings
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    # Print welcome banner
    console.print()
    console.print(Panel.fit(
        "[bold green]🧠 Axon Brain Bank Assistant[/bold green]\n\n"
        "I can help you find brain tissue samples for your research.\n"
        "All sample data comes directly from the database - no fabrication.\n\n"
        "[dim]Commands: 'quit' to exit, 'new' for fresh conversation,\n"
        "'history' for past sessions, 'resume <id>' to continue a session[/dim]",
        border_style="green",
    ))
    console.print()
    
    async with session_factory() as session:
        # Create persistence service for saving conversations
        persistence_service = ConversationService(session)
        
        # Get embedding API key for knowledge search (optional)
        embedding_api_key = settings.openai_api_key or None
        
        agent = ToolBasedChatAgent(
            db_session=session,
            anthropic_api_key=anthropic_key,
            persistence_service=persistence_service,
            embedding_api_key=embedding_api_key,
        )
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[user]You[/user]")
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                command = user_input.strip().lower()
                
                if command in ("quit", "exit", "q"):
                    console.print("\n[info]Goodbye! Happy researching! 🔬[/info]\n")
                    break
                
                if command == "new":
                    await agent.new_conversation()
                    console.print("[info]Started new conversation. Selection cleared.[/info]\n")
                    continue
                
                if command == "selection":
                    selection = agent.get_current_selection()
                    console.print()
                    console.print(Markdown(selection))
                    console.print()
                    continue
                
                if command == "help":
                    _print_help()
                    continue
                
                if command == "history":
                    await _handle_history(persistence_service)
                    continue
                
                if command.startswith("resume"):
                    await _handle_resume(agent, persistence_service, command)
                    continue
                
                if command.startswith("export"):
                    await _handle_export(agent, command)
                    continue
                
                if command == "email":
                    await _handle_email_preview(agent)
                    continue
                
                # Get response from agent
                console.print()
                console.print("[assistant]Axon[/assistant]\n")
                
                if stream:
                    # Streaming mode
                    await _stream_response(agent, user_input)
                else:
                    # Non-streaming mode (original behavior)
                    with Status("[dim]Thinking...[/dim]", spinner="dots", console=console) as status:
                        try:
                            response = await agent.chat(user_input)
                        except Exception as e:
                            console.print(f"[red]Error getting response: {e}[/red]\n")
                            continue
                    
                    console.print(Markdown(response))
                
                console.print()
                
            except KeyboardInterrupt:
                console.print("\n\n[info]Interrupted. Type 'quit' to exit.[/info]\n")
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}\n")
                import traceback
                traceback.print_exc()
    
    await engine.dispose()


async def _stream_response(agent, user_input: str):
    """Stream a response from the agent with live updates.
    
    Shows a 'Thinking...' spinner until text starts streaming,
    then displays the response as it arrives.
    """
    from axon.agent.chat_with_tools import StreamEventType
    
    response_text = ""
    thinking_shown = False
    status = None
    
    try:
        # Start with "Thinking..." indicator
        status = Status("[dim]Thinking...[/dim]", spinner="dots", console=console)
        status.start()
        thinking_shown = True
        
        async for event in agent.chat_stream(user_input):
            if event.type == StreamEventType.TOOL_START:
                # Tool executing - keep showing "Thinking..."
                pass
            
            elif event.type == StreamEventType.TOOL_END:
                # Tool finished - keep showing "Thinking..."
                pass
            
            elif event.type == StreamEventType.TEXT:
                # First text arrives - stop the spinner
                if thinking_shown and status:
                    status.stop()
                    thinking_shown = False
                
                # Stream text
                console.print(event.content, end="")
                response_text += event.content
            
            elif event.type == StreamEventType.DONE:
                # Stop spinner if still running (e.g., empty response)
                if thinking_shown and status:
                    status.stop()
                    thinking_shown = False
                
                # Ensure we end with a newline
                if response_text and not response_text.endswith("\n"):
                    console.print()
    
    except Exception as e:
        # Make sure spinner stops on error
        if thinking_shown and status:
            status.stop()
        console.print(f"\n[red]Error during streaming: {e}[/red]")
        import traceback
        traceback.print_exc()


async def _handle_history(persistence_service):
    """Handle the history command - show recent conversations."""
    conversations = await persistence_service.list_conversations(limit=10)
    
    if not conversations:
        console.print("[info]No previous conversations found.[/info]\n")
        return
    
    console.print()
    console.print("[bold]Recent Conversations:[/bold]\n")
    
    for conv in conversations:
        title = conv.title or "Untitled"
        date_str = conv.updated_at.strftime("%Y-%m-%d %H:%M")
        msg_count = conv.message_count
        
        # Truncate title if too long
        if len(title) > 50:
            title = title[:47] + "..."
        
        console.print(
            f"  [cyan]{conv.id[:8]}[/cyan]  {title}  "
            f"[dim]({msg_count} messages, {date_str})[/dim]"
        )
    
    console.print()
    console.print("[dim]Use 'resume <id>' to continue a conversation[/dim]\n")


async def _handle_resume(agent, persistence_service, command: str):
    """Handle the resume command - load a previous conversation."""
    parts = command.split()
    
    if len(parts) < 2:
        console.print("[yellow]Usage: resume <conversation_id>[/yellow]\n")
        console.print("[dim]Use 'history' to see available conversations[/dim]\n")
        return
    
    conv_id_prefix = parts[1]
    
    # Find conversation matching the prefix
    conversations = await persistence_service.list_conversations(limit=50)
    matches = [c for c in conversations if c.id.startswith(conv_id_prefix)]
    
    if not matches:
        console.print(f"[red]No conversation found matching '{conv_id_prefix}'[/red]\n")
        return
    
    if len(matches) > 1:
        console.print(f"[yellow]Multiple conversations match '{conv_id_prefix}':[/yellow]")
        for conv in matches[:5]:
            console.print(f"  [cyan]{conv.id[:8]}[/cyan]  {conv.title or 'Untitled'}")
        console.print("[dim]Please provide a more specific ID[/dim]\n")
        return
    
    # Load the conversation
    conv = matches[0]
    success = await agent.load_conversation(conv.id)
    
    if success:
        title = conv.title or "Untitled"
        console.print(f"[green]✓[/green] Resumed: [bold]{title}[/bold]\n")
        
        # Show restored selection summary
        selection = agent.tool_handler.selection
        if selection.cases or selection.controls:
            case_count = len(selection.cases)
            control_count = len(selection.controls)
            console.print(f"[dim]Restored selection: {case_count} case(s), {control_count} control(s)[/dim]")
        
        # Show last few messages for context
        data = await persistence_service.load_conversation(conv.id)
        if data and data.messages:
            console.print("[dim]Recent messages:[/dim]")
            for msg in data.messages[-4:]:  # Last 4 messages
                role_color = "cyan" if msg.role == "user" else "green"
                role_label = "You" if msg.role == "user" else "Axon"
                content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                console.print(f"  [{role_color}]{role_label}[/{role_color}]: {content_preview}")
            console.print()
    else:
        console.print(f"[red]Failed to load conversation '{conv_id_prefix}'[/red]\n")


def _print_help():
    """Print help information."""
    console.print(Panel(
        "[bold]Available Commands:[/bold]\n\n"
        "• [cyan]quit[/cyan] / [cyan]exit[/cyan] - End the chat session\n"
        "• [cyan]new[/cyan] - Start a fresh conversation\n"
        "• [cyan]history[/cyan] - Show recent conversations\n"
        "• [cyan]resume[/cyan] <id> - Continue a previous conversation\n"
        "• [cyan]selection[/cyan] - Show current sample selection\n"
        "• [cyan]export[/cyan] [format] - Export selection (csv, xlsx, json, txt)\n"
        "• [cyan]email[/cyan] - Preview admin email summary\n"
        "• [cyan]help[/cyan] - Show this help message\n\n"
        "[bold]Export Formats:[/bold]\n\n"
        "• [cyan]export csv[/cyan] - Comma-separated values\n"
        "• [cyan]export xlsx[/cyan] - Excel spreadsheet with formatting\n"
        "• [cyan]export json[/cyan] - JSON format\n"
        "• [cyan]export txt[/cyan] - Human-readable text report\n\n"
        "[bold]Example Queries:[/bold]\n\n"
        "• \"Find Alzheimer's samples with RIN > 7\"\n"
        "• \"Show me Parkinson's samples from the substantia nigra\"\n"
        "• \"What ALS samples do you have from Harvard?\"\n"
        "• \"I need schizophrenia samples with low PMI\"",
        title="Help",
        border_style="blue",
    ))
    console.print()


async def _handle_export(agent, command: str):
    """Handle export command."""
    from axon.export import ExportService, ExportFormat
    from axon.export.service import ExportMetadata
    
    # Parse format from command
    parts = command.split()
    format_str = parts[1] if len(parts) > 1 else "csv"
    
    format_map = {
        "csv": ExportFormat.CSV,
        "xlsx": ExportFormat.EXCEL,
        "excel": ExportFormat.EXCEL,
        "json": ExportFormat.JSON,
        "txt": ExportFormat.TEXT,
        "text": ExportFormat.TEXT,
    }
    
    export_format = format_map.get(format_str.lower(), ExportFormat.CSV)
    
    # Get selection from agent
    selection = agent.tool_handler.selection
    
    if not selection.cases and not selection.controls:
        console.print("[yellow]No samples selected yet.[/yellow] Use the chat to find and select samples first.\n")
        return
    
    # Gather metadata interactively
    console.print("\n[bold]Export Options[/bold] (press Enter to skip)\n")
    
    researcher = Prompt.ask("  Researcher name", default="")
    purpose = Prompt.ask("  Research purpose", default="")
    tissue_use = Prompt.ask("  Tissue use (e.g., RNA-seq, Histology)", default="")
    notes = Prompt.ask("  Additional notes", default="")
    
    # Extract criteria from conversation (simplified)
    criteria = {}
    if selection.cases:
        # Get common characteristics from cases
        ages = [s.age for s in selection.cases if s.age]
        if ages:
            criteria["age_range"] = f"{min(ages)}-{max(ages)}"
        
        diagnoses = set(s.diagnosis for s in selection.cases if s.diagnosis)
        if diagnoses:
            criteria["diagnosis"] = ", ".join(diagnoses)
        
        regions = set(s.brain_region for s in selection.cases if s.brain_region)
        if regions and len(regions) == 1:
            criteria["brain_region"] = list(regions)[0]
    
    metadata = ExportMetadata(
        researcher_name=researcher or None,
        research_purpose=purpose or None,
        tissue_use=tissue_use or None,
        selection_criteria=criteria,
        notes=notes or None,
    )
    
    # Create export
    service = ExportService(selection, metadata)
    result = service.export(export_format)
    
    # Determine output path
    output_path = Path(result.filename)
    
    if isinstance(result.content, bytes):
        output_path.write_bytes(result.content)
    else:
        output_path.write_text(result.content)
    
    console.print(f"\n[green]✓[/green] Exported {result.sample_count} samples to [bold]{output_path}[/bold]")
    
    # Show summary table
    table = Table(title="Export Summary")
    table.add_column("Property", style="cyan")
    table.add_column("Value")
    table.add_row("Format", result.format.value)
    table.add_row("File", str(output_path))
    table.add_row("Cases", str(len(selection.cases)))
    table.add_row("Controls", str(len(selection.controls)))
    table.add_row("Total", str(result.sample_count))
    console.print(table)
    console.print()


async def _handle_email_preview(agent):
    """Handle email preview command."""
    from axon.export import ExportService
    from axon.export.service import ExportMetadata
    
    # Get selection from agent
    selection = agent.tool_handler.selection
    
    if not selection.cases and not selection.controls:
        console.print("[yellow]No samples selected yet.[/yellow] Use the chat to find and select samples first.\n")
        return
    
    # Gather basic metadata
    console.print("\n[bold]Email Details[/bold] (press Enter to skip)\n")
    
    researcher = Prompt.ask("  Researcher name", default="")
    purpose = Prompt.ask("  Research purpose", default="")
    tissue_use = Prompt.ask("  Tissue use", default="")
    
    metadata = ExportMetadata(
        researcher_name=researcher or "Not specified",
        research_purpose=purpose or "Not specified",
        tissue_use=tissue_use or "Not specified",
    )
    
    service = ExportService(selection, metadata)
    email_text = service.generate_admin_email()
    
    console.print()
    console.print(Panel(email_text, title="Admin Email Preview", border_style="blue"))
    console.print()
    
    # Offer to save
    save = Prompt.ask("Save to file?", choices=["y", "n"], default="n")
    if save.lower() == "y":
        filename = f"brain_bank_request_{selection.cases[0].external_id if selection.cases else 'samples'}.txt"
        Path(filename).write_text(email_text)
        console.print(f"[green]✓[/green] Saved to {filename}\n")


@app.command("query")
def single_query(
    query: str = typer.Argument(..., help="Query to ask Axon"),
):
    """Ask a single question without starting a chat session."""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        console.print("[red]Error:[/red] ANTHROPIC_API_KEY not set")
        raise typer.Exit(1)
    
    asyncio.run(_single_query(
        query=query,
        anthropic_key=settings.anthropic_api_key,
    ))


async def _single_query(
    query: str,
    anthropic_key: str,
):
    """Execute a single query."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from axon.agent.chat_with_tools import ToolBasedChatAgent
    from axon.config import get_settings
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        agent = ToolBasedChatAgent(
            db_session=session,
            anthropic_api_key=anthropic_key,
        )
        
        console.print("\n[assistant]Axon[/assistant]\n")
        
        response = await agent.chat(query)
        
        console.print(Markdown(response))
        console.print()
    
    await engine.dispose()

