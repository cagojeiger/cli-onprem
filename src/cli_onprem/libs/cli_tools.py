"""CLI tool checking utilities."""

import shutil
from typing import Optional

import typer
from rich.console import Console


def check_cli_tool(
    tool_name: str,
    error_message: str,
    install_url: str,
    console: Optional[Console] = None,
) -> None:
    """Check if a CLI tool is installed.
    
    Args:
        tool_name: Name of the CLI tool to check
        error_message: Error message to display if tool is not found
        install_url: URL for installation instructions
        console: Rich console instance (creates new one if not provided)
    
    Raises:
        typer.Exit: If the tool is not installed
    """
    if console is None:
        console = Console()
        
    if shutil.which(tool_name) is None:
        console.print(f"[bold red]오류: {error_message}[/bold red]")
        console.print(f"[yellow]{tool_name} 설치 방법: {install_url}[/yellow]")
        raise typer.Exit(code=1)