"""CLI command for interactive chat with Axon."""

import asyncio
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

from axon.config import get_settings

app = typer.Typer(help="Chat with Axon brain bank assistant")
console = Console(theme=Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "info": "dim",
}))


@app.command("start")
def start_chat(
    num_samples: int = typer.Option(10, help="Number of samples to retrieve per query"),
    stream: bool = typer.Option(True, help="Stream responses"),
):
    """Start an interactive chat session with Axon.
    
    Chat with the AI assistant to find brain tissue samples.
    Type 'quit' or 'exit' to end the session.
    Type 'new' to start a fresh conversation.
    Type 'history' to see conversation summary.
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        console.print("[red]Error:[/red] OPENAI_API_KEY not set")
        raise typer.Exit(1)
    
    if not settings.anthropic_api_key:
        console.print("[red]Error:[/red] ANTHROPIC_API_KEY not set")
        raise typer.Exit(1)
    
    asyncio.run(_chat_loop(
        openai_key=settings.openai_api_key,
        anthropic_key=settings.anthropic_api_key,
        num_samples=num_samples,
        stream=stream,
    ))


async def _chat_loop(
    openai_key: str,
    anthropic_key: str,
    num_samples: int,
    stream: bool,
):
    """Main chat loop."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from axon.agent.chat import ChatAgent
    from axon.config import get_settings
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    # Print welcome banner
    console.print()
    console.print(Panel.fit(
        "[bold green]🧠 Axon Brain Bank Assistant[/bold green]\n\n"
        "I can help you find brain tissue samples for your research.\n"
        "Ask me about samples by diagnosis, brain region, or quality metrics.\n\n"
        "[dim]Commands: 'quit' to exit, 'new' for fresh conversation, 'history' for summary[/dim]",
        border_style="green",
    ))
    console.print()
    
    async with session_factory() as session:
        agent = ChatAgent(
            db_session=session,
            embedding_api_key=openai_key,
            anthropic_api_key=anthropic_key,
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
                    agent.new_conversation()
                    console.print("[info]Started new conversation.[/info]\n")
                    continue
                
                if command == "history":
                    console.print(f"[info]{agent.get_conversation_summary()}[/info]\n")
                    continue
                
                if command == "help":
                    _print_help()
                    continue
                
                # Get response from agent
                console.print()
                console.print("[assistant]Axon[/assistant]", end="")
                
                if stream:
                    # Stream the response
                    console.print()
                    response_text = ""
                    async for chunk in await agent.chat(
                        user_input,
                        num_samples=num_samples,
                        stream=True,
                    ):
                        console.print(chunk, end="")
                        response_text += chunk
                    console.print("\n")
                else:
                    # Get complete response
                    response = await agent.chat(
                        user_input,
                        num_samples=num_samples,
                        stream=False,
                    )
                    console.print()
                    console.print(Markdown(response))
                    console.print()
                
            except KeyboardInterrupt:
                console.print("\n\n[info]Interrupted. Type 'quit' to exit.[/info]\n")
            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}\n")
    
    await engine.dispose()


def _print_help():
    """Print help information."""
    console.print(Panel(
        "[bold]Available Commands:[/bold]\n\n"
        "• [cyan]quit[/cyan] / [cyan]exit[/cyan] - End the chat session\n"
        "• [cyan]new[/cyan] - Start a fresh conversation\n"
        "• [cyan]history[/cyan] - Show conversation summary\n"
        "• [cyan]help[/cyan] - Show this help message\n\n"
        "[bold]Example Queries:[/bold]\n\n"
        "• \"Find Alzheimer's samples with RIN > 7\"\n"
        "• \"Show me Parkinson's samples from the substantia nigra\"\n"
        "• \"What ALS samples do you have from Harvard?\"\n"
        "• \"I need schizophrenia samples with low PMI\"",
        title="Help",
        border_style="blue",
    ))
    console.print()


@app.command("query")
def single_query(
    query: str = typer.Argument(..., help="Query to ask Axon"),
    num_samples: int = typer.Option(10, help="Number of samples to retrieve"),
):
    """Ask a single question without starting a chat session."""
    settings = get_settings()
    
    if not settings.openai_api_key:
        console.print("[red]Error:[/red] OPENAI_API_KEY not set")
        raise typer.Exit(1)
    
    if not settings.anthropic_api_key:
        console.print("[red]Error:[/red] ANTHROPIC_API_KEY not set")
        raise typer.Exit(1)
    
    asyncio.run(_single_query(
        query=query,
        openai_key=settings.openai_api_key,
        anthropic_key=settings.anthropic_api_key,
        num_samples=num_samples,
    ))


async def _single_query(
    query: str,
    openai_key: str,
    anthropic_key: str,
    num_samples: int,
):
    """Execute a single query."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    from axon.agent.chat import ChatAgent
    from axon.config import get_settings
    
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        agent = ChatAgent(
            db_session=session,
            embedding_api_key=openai_key,
            anthropic_api_key=anthropic_key,
        )
        
        console.print("\n[assistant]Axon[/assistant]\n")
        
        response = await agent.chat(
            query,
            num_samples=num_samples,
            stream=False,
        )
        
        console.print(Markdown(response))
        console.print()
    
    await engine.dispose()

