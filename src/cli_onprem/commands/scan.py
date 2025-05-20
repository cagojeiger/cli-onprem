"""CLI-ONPREM을 위한 스캔 명령어."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="디렉토리를 스캔하고 보고서 생성")
console = Console()


PATH_ARG = typer.Argument(..., help="스캔할 디렉토리 경로")


@app.command()
def directory(
    path: Path = PATH_ARG,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="상세 출력 활성화"
    ),
) -> None:
    """디렉토리를 스캔하고 내용에 대한 보고서를 생성합니다."""
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
