"""CLI entry point for Axon."""

import typer

from axon.cli.commands.ingest import app as ingest_app

app = typer.Typer(
    name="axon",
    help="🧠 Axon - Brain Bank Discovery System",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(ingest_app, name="import", help="Import data from brain banks")


@app.command()
def version():
    """Show version information."""
    from axon import __version__
    typer.echo(f"Axon v{__version__}")


if __name__ == "__main__":
    app()

