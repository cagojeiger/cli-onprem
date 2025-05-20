"""Greeting command for CLI-ONPREM."""

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="Greet a user")
console = Console()


@app.command()
def hello(
    name: Optional[str] = typer.Argument(None, help="Name of the person to greet"),
) -> None:
    """Greet a user with a friendly message."""
    if name:
        console.print(f"[bold green]Hello, {name}![/bold green]")
    else:
        console.print("[bold green]Hello, world![/bold green]")
