"""CLI-ONPREM 애플리케이션의 메인 진입점."""

import importlib
import sys
from typing import Any, cast

import typer
from rich.console import Console

# from cli_onprem.commands import docker_tar, fatpack, helm, s3_share

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

console = Console()


def get_command(import_path: str) -> typer.Typer:
    """지정된 경로에서 명령어 모듈을 로드합니다."""
    module_path, attr_name = import_path.split(":")
    module = importlib.import_module(module_path)
    return cast(typer.Typer, getattr(module, attr_name))


app.add_typer(get_command("cli_onprem.commands.docker_tar:app"), name="docker-tar")
app.add_typer(get_command("cli_onprem.commands.fatpack:app"), name="fatpack")
app.add_typer(get_command("cli_onprem.commands.helm_local:app"), name="helm-local")
app.add_typer(get_command("cli_onprem.commands.s3_share:app"), name="s3-share")


@app.callback()
def main(verbose: bool = False) -> None:
    """CLI-ONPREM - 인프라 엔지니어를 위한 CLI 도구."""
    pass


def main_cli() -> Any:
    """Entry point for CLI."""
    return app(sys.argv[1:])


if __name__ == "__main__":
    main_cli()
