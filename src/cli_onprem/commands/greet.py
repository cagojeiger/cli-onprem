"""CLI-ONPREM을 위한 인사 명령어."""

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="사용자에게 인사")
console = Console()


@app.command()
def hello(
    name: Optional[str] = typer.Argument(None, help="인사할 사람의 이름"),
) -> None:
    """친근한 메시지로 사용자에게 인사합니다."""
    if name:
        console.print(f"[bold green]Hello, {name}![/bold green]")
    else:
        console.print("[bold green]Hello, world![/bold green]")
