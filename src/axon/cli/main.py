"""CLI entry point for Axon."""

import typer

from axon.cli.commands.ingest import app as ingest_app
from axon.cli.commands.embeddings import app as embeddings_app
from axon.cli.commands.chat import app as chat_app
from axon.cli.commands.knowledge import app as knowledge_app
from axon.cli.commands.export import app as export_app

app = typer.Typer(
    name="axon",
    help="🧠 Axon - Brain Bank Discovery System",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(ingest_app, name="import", help="Import data from brain banks")
app.add_typer(embeddings_app, name="embeddings", help="Generate and manage embeddings")
app.add_typer(chat_app, name="chat", help="Chat with Axon assistant")
app.add_typer(knowledge_app, name="knowledge", help="Manage knowledge base (web content)")
app.add_typer(export_app, name="export", help="Export sample selections")


@app.command()
def version():
    """Show version information."""
    from axon import __version__
    typer.echo(f"Axon v{__version__}")


if __name__ == "__main__":
    app()

