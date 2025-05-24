"""Standardized error handling utilities."""

from typing import Optional

import typer
from rich.console import Console


class CLIError:
    """Standardized error handling for CLI operations."""
    
    @staticmethod
    def print_error(
        console: Console,
        message: str,
        exception: Optional[Exception] = None,
        exit_code: int = 1
    ) -> None:
        """Print error message and exit.
        
        Args:
            console: Rich console instance
            message: Error message to display
            exception: Optional exception to chain
            exit_code: Exit code (default: 1)
        """
        console.print(f"[bold red]오류: {message}[/bold red]")
        if exception:
            raise typer.Exit(code=exit_code) from exception
        else:
            raise typer.Exit(code=exit_code)
    
    @staticmethod
    def print_warning(console: Console, message: str) -> None:
        """Print warning message without exiting.
        
        Args:
            console: Rich console instance
            message: Warning message to display
        """
        console.print(f"[bold yellow]경고: {message}[/bold yellow]")
    
    @staticmethod
    def handle_subprocess_error(
        console: Console,
        command: str,
        error: Exception,
        suggestion: Optional[str] = None
    ) -> None:
        """Handle subprocess errors with consistent formatting.
        
        Args:
            console: Rich console instance
            command: Command that failed
            error: Exception that occurred
            suggestion: Optional suggestion for fixing the error
        """
        console.print(f"[bold red]오류: '{command}' 명령 실행 실패[/bold red]")
        console.print(f"[red]세부사항: {error}[/red]")
        if suggestion:
            console.print(f"[yellow]제안: {suggestion}[/yellow]")
        raise typer.Exit(code=1) from error