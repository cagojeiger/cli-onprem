"""Scan command for CLI-ONPREM."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Scan a directory and generate a report")
console = Console()


PATH_ARG = typer.Argument(..., help="Directory path to scan")


@app.command()
def directory(
    path: Path = PATH_ARG,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Scan a directory and generate a report of its contents."""
    if not path.exists():
        console.print(f"[bold red]Error: Path {path} does not exist[/bold red]")
        raise typer.Exit(code=1)

    if not path.is_dir():
        console.print(f"[bold red]Error: {path} is not a directory[/bold red]")
        raise typer.Exit(code=1)

    if verbose:
        console.print(f"[bold blue]Scanning directory: {path}[/bold blue]")

    files = list(path.glob("**/*"))
    file_count = sum(1 for f in files if f.is_file())
    dir_count = sum(1 for f in files if f.is_dir())

    table = Table(title=f"Scan Report for {path}")
    table.add_column("Item", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Files", str(file_count))
    table.add_row("Directories", str(dir_count))
    table.add_row("Total Items", str(file_count + dir_count))

    console.print(table)

    if verbose:
        console.print("[bold green]Scan completed successfully![/bold green]")
