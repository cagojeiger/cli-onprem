"""CLI-ONPREM 애플리케이션의 메인 진입점."""

import typer
from rich.console import Console

from cli_onprem.commands import docker_tar, greet, scan

app = typer.Typer(
    name="cli-onprem",
    help="인프라 엔지니어를 위한 CLI 도구",
    add_completion=True,
)

app.add_typer(greet.app, name="greet")
app.add_typer(scan.app, name="scan")
app.add_typer(docker_tar.app, name="docker-tar")

console = Console()


@app.callback()
def main(verbose: bool = False) -> None:
    """CLI-ONPREM - 인프라 엔지니어를 위한 CLI 도구."""
    pass


if __name__ == "__main__":
    app()
