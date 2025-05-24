"""Progress reporting utilities."""

from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class ProgressReporter:
    """Unified progress reporting for CLI operations."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize progress reporter.
        
        Args:
            console: Rich console instance (creates new one if not provided)
        """
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
    
    def step(self, message: str) -> None:
        """Print step message."""
        self.console.print(f"[cyan]→ {message}[/cyan]")
    
    def create_spinner(self, message: str = "처리 중...") -> Progress:
        """Create a spinner progress indicator.
        
        Args:
            message: Message to display with spinner
            
        Returns:
            Rich Progress instance
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )