"""CLI-ONPREM 애플리케이션의 메인 진입점."""

import typer
from rich.console import Console

from cli_onprem.commands import docker_tar, fatpack, helm

import os
import sys

is_test = "pytest" in sys.modules
context_settings = {
    "ignore_unknown_options": is_test,
    "allow_extra_args": is_test,
}

app = typer.Typer(
    name="cli-onprem",
    help="인프라 엔지니어를 위한 CLI 도구",
    add_completion=True,
    context_settings=context_settings,
    no_args_is_help=True,
)

app.add_typer(docker_tar.app, name="docker-tar")
app.add_typer(fatpack.app, name="fatpack")
app.add_typer(helm.app, name="helm")

console = Console()


@app.callback()
def main(verbose: bool = False) -> None:
    """CLI-ONPREM - 인프라 엔지니어를 위한 CLI 도구."""
    pass


if __name__ == "__main__":
    app()
