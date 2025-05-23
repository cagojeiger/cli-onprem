"""CLI-ONPREM 애플리케이션의 메인 진입점."""

import sys
from typing import Any

import typer
from rich.console import Console

from cli_onprem.commands import docker_tar, fatpack, helm, s3_share

context_settings = {
    "ignore_unknown_options": True,  # Always allow unknown options
    "allow_extra_args": True,  # Always allow extra args
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
app.add_typer(s3_share.app, name="s3-share")

console = Console()


@app.callback()
def main(verbose: bool = False) -> None:
    """CLI-ONPREM - 인프라 엔지니어를 위한 CLI 도구."""
    pass


def main_cli() -> Any:
    """Entry point for CLI."""
    return app(sys.argv[1:])


if __name__ == "__main__":
    main_cli()
