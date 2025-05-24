"""Console and Typer app utilities."""

from typing import Any, Dict, Optional, Tuple

import typer
from rich.console import Console


class ConsoleManager:
    """Manages console output with consistent styling."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def info(self, message: str) -> None:
        """Print informational message."""
        self.console.print(f"[bold blue]► {message}[/bold blue]")
    
    def success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[bold green]✓ {message}[/bold green]")
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[bold yellow]⚠ {message}[/bold yellow]")
    
    def error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[bold red]✗ {message}[/bold red]")
    
    def print(self, message: str, **kwargs: Any) -> None:
        """Pass-through to console.print."""
        self.console.print(message, **kwargs)


def create_typer_app(
    help_text: str,
    context_settings: Optional[Dict] = None
) -> Tuple[typer.Typer, Console]:
    """Create a standard Typer app with common settings.
    
    Args:
        help_text: Help text for the Typer app
        context_settings: Additional context settings to override defaults
        
    Returns:
        Tuple of (Typer app, Rich console)
    """
    default_context_settings = {
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
    
    if context_settings:
        default_context_settings.update(context_settings)
    
    app = typer.Typer(
        help=help_text,
        context_settings=default_context_settings,
    )
    console = Console()
    
    return app, console