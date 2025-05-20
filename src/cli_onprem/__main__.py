"""Main entry point for the CLI-ONPREM application."""

import typer
from rich.console import Console

from cli_onprem.commands import greet, scan

app = typer.Typer(
    name="cli-onprem",
    help="CLI tool for infrastructure engineers",
    add_completion=True,
)

app.add_typer(greet.app, name="greet")
app.add_typer(scan.app, name="scan")

console = Console()


@app.callback()
def main(verbose: bool = False) -> None:
    """CLI-ONPREM - CLI tool for infrastructure engineers."""
    pass


if __name__ == "__main__":
    app()
